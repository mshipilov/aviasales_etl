import os
import re
import json
import asyncio
import logging
from datetime import date
from typing import Union
import time
import random

from celery import Celery
from celery.schedules import crontab
from celery.result import AsyncResult
from sqlalchemy import select
from playwright.async_api import async_playwright
import redis

from dotenv import load_dotenv
load_dotenv() 

from .database import AsyncSessionLocal
from .models import Route
from .crud import create_route_history, create_route
from .scraper import AsyncScraper
from .schemas import ScrapeInput, ScrapeContext, ScrapeSuccess, ScrapeFailure, ScrapeResult
from .service import scrape_route, get_active_routes

logger = logging.getLogger(__name__)

inside_docker = os.path.exists('/.dockerenv')
REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL") if inside_docker else os.getenv('REDIS_BROKER_URL_LOCAL')

# 1. Initialize Background Task Infrastructure
celery_app = Celery("tasks", broker=REDIS_BROKER_URL, backend=REDIS_BROKER_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

redis_client = redis.Redis.from_url(REDIS_BROKER_URL, decode_responses=True)

# 2. Automated Trigger
celery_app.conf.beat_schedule = {
    "bulk-scraping-routine": {
        "task": "src.tasks.scrape_all_active_routes_task",
        "schedule": crontab(hour=5, minute=0),
    },
}


@celery_app.task(name="src.tasks.scrape_batch_routes_task")
def scrape_batch_routes_task(scrape_inputs_list: list[dict]) -> list[dict]:
    results = asyncio.run(batch_scrape_and_cache(scrape_inputs_list))
    return [result.model_dump() for result in results]

@celery_app.task(name="src.tasks.scrape_all_active_routes_task")
def scrape_all_active_routes_task() -> None:
    asyncio.run(scrape_all_active_routes())


async def worker_scrape_and_cache(scrape_input_dict: dict, context) -> ScrapeResult:
    """Scrapes a single page within the shared browser context."""
    scrape_input = ScrapeInput(**scrape_input_dict)

    async with AsyncSessionLocal() as db:
    
        page = await context.new_page()
        try:
            scrape_result = await scrape_route(scrape_input=scrape_input, db=db, page=page)
            scrape_result_dict = scrape_result.model_dump()
            # Explicitly commit database because we don't have fastAPI db dependency injection here
            await db.commit()
            
            cache_key = f"cache:route:{scrape_result.origin}:{scrape_result.destination}"
            redis_client.set(
                name=cache_key,
                ex=86400,  # 24 hours
                value=json.dumps(scrape_result_dict, default=str)
            )
            return ScrapeSuccess.model_validate(scrape_result_dict)
            
        except Exception as e:
            await db.rollback()
            msg = f"Failed scraping {scrape_input.origin} -> {scrape_input.destination}: {str(e)}"
            logger.error(msg)
            return ScrapeFailure.model_validate({"error": msg})
        finally:
            await page.close()


async def batch_scrape_and_cache(scrape_inputs_list: list[dict]) -> list[ScrapeResult]:
    """Scrapes few routes with single browser"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--headless=new",       # Forces Chromium's standard headless architecture
                "--no-sandbox",          # Essential for root permissions inside Linux Docker containers
                "--disable-gpu",         # Bypasses hardware rendering calls inside a Docker engine
                "--disable-dev-shm-usage" # Prevents browser memory crashes inside restricted containers
            ])
        context = await browser.new_context()
        
        try:
            tasks = [
                worker_scrape_and_cache(scrape_input_dict, context)
                for scrape_input_dict in scrape_inputs_list
            ]
            results = await asyncio.gather(*tasks)
            
            
            return results
            
        except Exception as e:
            logger.error(f"Batch pipeline transaction failure: {str(e)}")
            raise e
        finally:
            await context.close()
            await browser.close()

async def get_task_result(task_id: str) -> ScrapeResult:
    task_result = AsyncResult(task_id, app=celery_app)
    print('task_result')
    print(task_result.result)
    
    if task_result.status == "SUCCESS":
        return ScrapeSuccess.model_validate(task_result.result[0])
    else: 
        return ScrapeFailure.model_validate(task_result.result)


async def scrape_all_active_routes():
    async with AsyncSessionLocal() as db:
        active_routes = await get_active_routes(db=db)

    # convert RouteResult to ScrapeInput
    scrape_inputs = [{'origin': active_route.origin, 'destination': active_route.destination} for active_route in active_routes]
    # split to batches with 3 elements (for concurrent scraping)
    scrape_inputs_list_of_batches = [scrape_inputs[i:i + 3] for i in range(0, len(scrape_inputs), 3)]
    
    for batch in scrape_inputs_list_of_batches:
        task = scrape_batch_routes_task.delay(batch)


if __name__ == '__main__':
    asyncio.run(scrape_all_active_routes())
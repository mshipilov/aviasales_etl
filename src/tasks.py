import os
import re
import json
import asyncio
import logging
from datetime import date
from typing import Union

from celery import Celery
from celery.schedules import crontab
from celery.result import AsyncResult
from sqlalchemy import select
from playwright.async_api import async_playwright
import redis

from .database import AsyncSessionLocal
from .models import Route
from .crud import create_route_history, create_route
from .scraper import AsyncScraper
from .schemas import ScrapeInput, ScrapeContext, ScrapeSuccess, ScrapeFailure, ScrapeResult
from .service import scrape_route

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 1. Initialize Background Task Infrastructure
celery_app = Celery("scraper_tasks", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# 2. Automated Trigger
celery_app.conf.beat_schedule = {
    "nightly-bulk-scraping-routine": {
        "task": "tasks.scrape_all_active_routes_task",
        "schedule": crontab(hour=5, minute=0),
    },
}

def run_async(coro):
    """Helper framework wrapper to drive modern async loops inside synchronous threads."""
    return asyncio.run(coro)


@celery_app.task(name="tasks.scrape_batch_routes_task")
def scrape_batch_routes_task(scrape_inputs_list: list[dict]) -> list[ScrapeResult]:
    """Async wrapper for scraping task"""
    return run_async(batch_scrape_and_cache(scrape_inputs_list))


async def worker_scrape_and_cache(scrape_input_dict: dict, context, db) -> ScrapeResult:
    """Scrapes a single page within the shared browser context."""
    scrape_input = ScrapeInput(**scrape_input_dict)
    
    page = await context.new_page()
    try:
        scrape_result = await scrape_route(scrape_input=scrape_input, db=db, page=page)
        scrape_result_dict = scrape_result.model_dump()
        
        cache_key = f"cache:route:{scrape_result.origin}:{scrape_result.destination}"
        redis_client.set(
            name=cache_key,
            ex=86400,
            value=json.dumps(scrape_result_dict, default=str)
        )
        return ScrapeSuccess.model_validate(**scrape_result_dict)
        
    except Exception as e:
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
        
        async with AsyncSessionLocal() as db:
            try:
                tasks = [
                    worker_scrape_and_cache(scrape_input_dict, context, db)
                    for scrape_input_dict in scrape_inputs_list
                ]
                
                results = await asyncio.gather(*tasks)
                
                # Explicitly commit database because we don't have fastAPI db dependency injection here
                await db.commit()
                
                return results
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Batch pipeline transaction failure: {str(e)}")
                raise e
            finally:
                await context.close()
                await browser.close()

async def get_task_result(task_id: str) -> ScrapeResult:
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    }
    
    if task_result.status == "SUCCESS":
        return ScrapeSuccess.model_validate(**response)
    else:
        return ScrapeFailure.model_validate(**response)
        
    
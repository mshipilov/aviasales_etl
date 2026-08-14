import logging
from contextlib import asynccontextmanager
from typing import Annotated, Union
import json
import os

import redis
from fastapi import FastAPI, Response, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from dotenv import load_dotenv

load_dotenv() 

from .crud import add_route, deactivate_route, get_route_history, extract_data
from .service import get_active_routes, get_bulk_route_history
from .schemas import ScrapeInput, ScrapeResult, ScrapeSuccess, RouteResult, RouteHistoryResult, RouteHistoryInput, ScrapePreResult
from .database import SessionDep, create_db_tables
from . import log_config
from .tasks import scrape_batch_routes_task, get_task_result

 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create db tables if not exist
    await create_db_tables()
    yield
    # create browser
    """
    async with async_playwright() as p:
        # Launch browser once
        browser = await p.chromium.launch(headless=True)
        # Create a single context shared by workers (avoids opening multiple browser windows)
        context = await browser.new_context()
        app.state.browser = browser
        app.state.context = context

        yield # API is running

        await context.close()
        await browser.close()
    """

app = FastAPI(lifespan=lifespan)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

"""async def get_request_page() -> Page:
    context = app.state.context
    page = await context.new_page()
    try:
        yield page
    finally:
        await page.close()

PageDep = Annotated[Page, Depends(get_request_page)]
"""


@app.post('/routes/scrape/')
async def scrape_route(
    scrape_input: ScrapeInput,
    ) -> Union[ScrapePreResult, ScrapeSuccess]:
    """scrape one route with cache"""
    # cache path format
    cache_key = f"cache:route:{scrape_input.origin}:{scrape_input.destination}"
    
    # 1. check redis cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        scrape_success = json.loads(cached_data)
        scrape_success["status"] = "success"
        return ScrapeSuccess.model_validate(scrape_success)
    # 2. scrape website   
    task_input = scrape_input.model_dump()
    task = scrape_batch_routes_task.delay([task_input])
    return ScrapePreResult.model_validate({
            "status": "pending",
            "task_id": task.id
            })
        

@app.post('/routes/batch_scrape/')
async def scrape_routes(
    scrape_inputs: list[ScrapePreResult]
    ) -> ScrapePreResult:
    """scrape few routes, no cache"""
        
    task_inputs = [scrape_input.model_dump() for scrape_input in scrape_inputs]
    task = scrape_batch_routes_task.delay(task_inputs)
    return ScrapePreResult.model_validate({
                "status": "pending",
                "task_id": task.id
                })

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> ScrapeResult:
    response = await get_task_result(task_id=task_id)
        
    return response

@app.get('/routes/')
async def get_routes(
    db: SessionDep,
    route_number: int = Query(default=8),
    ) -> list[RouteResult]:
    """get list of all active routes"""
    active_routes = await get_active_routes(route_number=route_number, db=db)
    if not active_routes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No active routes found. Please add one."
        )
    return active_routes

@app.post('/routes/history/')
async def get_route_histories(
    db: SessionDep,
    route_history_input: RouteHistoryInput
    ) -> dict[int, list[RouteHistoryResult]]:
    route_histories = await get_bulk_route_history(db=db, route_ids=route_history_input.route_ids)

    return route_histories


@app.patch('/routes/deactivate/')
async def deactivate(abbr: str):
    deactivate_route(abbr)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get('/routes/{abbr}/history')
async def get_route_history(abbr: str):
    history = get_route_history(abbr)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No history found for this route"
        )
    return history


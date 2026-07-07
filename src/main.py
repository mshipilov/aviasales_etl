import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Response, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from dotenv import load_dotenv

from .crud import get_active_routes, add_route, deactivate_route, get_route_history, extract_data
from .service import scrape_route
from .schemas import ScrapeInput, ScrapeResult
from .database import SessionDep, create_db_tables

load_dotenv()  

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create db tables if not exist
    await create_db_tables()
    # create browser
    async with async_playwright() as p:
        # Launch browser once
        browser = await p.chromium.launch(headless=False)
        # Create a single context shared by workers (avoids opening multiple browser windows)
        context = await browser.new_context()
        app.state.browser = browser
        app.state.context = context

        yield # API is running

        await context.close()
        await browser.close()

app = FastAPI(lifespan=lifespan)

async def get_request_page() -> Page:
    context = app.state.context
    page = await context.new_page()
    try:
        yield page
    finally:
        await page.close()

# 2. Create a reusable Type Alias (keeps your endpoints clean)
PageDep = Annotated[Page, Depends(get_request_page)]


@app.post('/routes/scrape_one/')
async def scrape_one_route(
    scrape_input: ScrapeInput, 
    db: SessionDep, 
    page: PageDep) -> ScrapeResult:
    scrape_result = await scrape_route(scrape_input=scrape_input, db=db, page=page)
    return scrape_result

@app.get('/routes/')
def get_routes():
    active_routes = get_active_routes()
    if not active_routes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No active routes found. Please add one."
        )
    return active_routes

@app.patch('/routes/deactivate/')
def deactivate(abbr: str):
    deactivate_route(abbr)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get('/routes/{abbr}/history')
def get_route_history(abbr: str):
    history = get_route_history(abbr)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No history found for this route"
        )
    return history

@app.post('/scrape/')
def scrape():
    extract_data()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


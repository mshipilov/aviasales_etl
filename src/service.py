import logging
from collections import defaultdict


from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import Page

from .schemas import ScrapeInput, ScrapeContext, ScrapeResult, ScrapeSuccess, RouteResult, ScrapeFailure, RouteHistoryResult
from .crud import read_route_by_origin_destination, create_route, create_route_history, read_active_routes, read_bulk_route_history
from .scraper import AsyncScraper


logger = logging.getLogger(__name__)

async def scrape_route(scrape_input: ScrapeInput, db: AsyncSession, page: Page) -> ScrapeSuccess:
    scraper = AsyncScraper(page=page)
    route = await read_route_by_origin_destination(scrape_input=scrape_input, db=db)
    
    # scrape abbr if route present in db
    if route:
        logger.debug(f'already exists: {route}')
        scrape_context = ScrapeContext(origin=route.origin, destination=route.destination, abbr=route.abbr)
        scrape_result = await scraper.scrape_by_context(scrape_context=scrape_context)

    # get and scrape abbr if route not in db
    else:
        logger.debug(f'scraping new route')
        scrape_result = await scraper.scrape_by_input(scrape_input=scrape_input)
        route = await create_route(scrape_result=scrape_result, db=db)

    # save history to db
    await create_route_history(scrape_result=scrape_result, db=db, route_id=route.id)

    # return data
    return scrape_result

async def get_active_routes(db: AsyncSession, route_number: int = 0) -> list[RouteResult]:
    routes = await read_active_routes(route_number=route_number, db=db)
    route_results = [RouteResult.model_validate(route) for route in routes]
    return route_results

async def get_bulk_route_history(
    db: AsyncSession, 
    route_ids: list[int]
    ) -> dict[int, list[RouteHistoryResult]]:
    """
    Fetches route history for multiple route IDs in a single query 
    and groups the records by route_id.
    """
    # 1. Fetch all matching records in one query
    route_histories = await read_bulk_route_history(db=db, route_ids=route_ids)

    # 2. Group records by route_id for easy frontend consumption
    grouped_history = defaultdict(list)
    for record in route_histories:
        grouped_history[record.route_id].append(record)
        
    return grouped_history
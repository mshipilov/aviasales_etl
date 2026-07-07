from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import Page

from .schemas import ScrapeInput, ScrapeContext, ScrapeResult
#from .models import Route
from .crud import read_route_by_origin_destination, create_route, create_route_history
from .scraper import AsyncScraper

async def scrape_route(scrape_input: ScrapeInput, db: AsyncSession, page: Page) -> ScrapeResult:
    scraper = AsyncScraper(page=page)
    route = await read_route_by_origin_destination(scrape_input=scrape_input, db=db)
    
    # scrape abbr if route present in db
    if route:
        scrape_context = ScrapeContext(origin=route.origin, destination=route.destination, abbr=route.abbr)
        scrape_result = await scraper.scrape_by_context(scrape_context=scrape_context)

    # get and scrape abbr if route not in db
    else:
        scrape_result = await scraper.scrpape_by_input(scrape_input=scrape_input)
        await create_route(scrape_result=scrape_result, db=db)

    # save history to db
    await create_route_history(scrape_result=scrape_result, db=db)

    # return data
    return scrape_result

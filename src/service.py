from sqlalchemy.orm import Session

from .schemas import ScrapeInput, ScrapeResult

async def scrape_and_save_route(db: Session, payload: ScrapeInput) -> ScrapeResult:
    # get abbr if origin and destination not in db
    
    # get data for this abbr

    # save data to db

    # return data
    return

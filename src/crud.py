import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.exc import IntegrityError

from .models import Base, Route, RouteHistory
from .schemas import ScrapeInput, ScrapeSuccess

logger = logging.getLogger(__name__)

async def read_route_by_origin_destination(db: AsyncSession, scrape_input: ScrapeInput) -> Route | None:
    logger.info(f"Checking DB for route: {scrape_input.origin} -> {scrape_input.destination}")
    
    stmt = select(Route).where(
        Route.origin == scrape_input.origin,
        Route.destination == scrape_input.destination
    )
    
    result = await db.execute(stmt)

    return result.scalar_one_or_none()

async def create_route(scrape_result: ScrapeSuccess, db: AsyncSession) -> Route:
    logger.info(f"Saving new route in DB: {scrape_result.origin} -> {scrape_result.destination} ({scrape_result.abbr})")
    route = Route(origin=scrape_result.origin,
        destination=scrape_result.destination,
        abbr=scrape_result.abbr
    )
    try:
        db.add(route)
        await db.flush()
        await db.refresh(route)
    except IntegrityError:
        logger.warning(f"Route already exists for {ScrapeSuccess}")

    return route
    
async def create_route_history(scrape_result: ScrapeSuccess, db: AsyncSession, route_id: int) -> RouteHistory:
    logger.info(f"Saving new route history in DB: {scrape_result.origin} -> {scrape_result.destination}, price = {scrape_result.price}")
    db_columns = RouteHistory.__table__.columns.keys()
    filtered_data = {k: v for k, v in scrape_result.model_dump().items() if k in db_columns}
    route_history = RouteHistory(**filtered_data, route_id=route_id)
    db.add(route_history)
    return route_history

async def read_active_routes(route_number: int, db: AsyncSession) -> Sequence[Route]:
    logger.info(f"Fetching newest {route_number} active routes")
    stmt = select(Route).where(Route.is_active == True).order_by(desc(Route.created_at)).limit(route_number)
    result = await db.execute(stmt)
    active_routes = result.scalars().all()
    return active_routes

async def read_bulk_route_history(db: AsyncSession, route_ids: list[int]) -> Sequence[RouteHistory]:
    stmt = (
        select(RouteHistory)
        .where(RouteHistory.route_id.in_(route_ids))
    )
    result = await db.execute(stmt)
    route_histories = result.scalars().all()

    return route_histories


def add_route(origin: str, destination: str, abbr: str):
    logger.info(f"Adding new route: {origin} -> {destination} ({abbr})")
    stmt = select(Route).where(Route.abbr == abbr)
    route = session.execute(stmt)
    # if abbr exists in DB - activate it
    if route.scalars().first():
        print('added route exists in DB')
        route.is_active = True
    # if abbr does not exist in DB - create it
    else:
        print('added route does not exist in DB')
        session.add(Route(origin=origin, destination=destination, abbr=abbr))

    session.commit()


def deactivate_route(abbr):
    logger.info(f"Deactivating route with abbr: {abbr}")
    session.execute(update(Route).where(Route.abbr==abbr).values(is_active=False))

    session.commit()
    

def get_route_history(abbr):
    logger.info(f"Fetching history for route: {abbr}")
    stmt = session.execute(select(Route.abbr).join(RouteHistory).where(Route.id==RouteHistory.route_id).where(Route.abbr==abbr))
    route_history = session.execute(stmt).scalars().all()
    return route_history





def extract_data():
    scraper = Scraper()
    for route in session.execute(select(Route).where(Route.is_active==True)).scalars().all():
        logger.info(f"Processing route: {route.abbr}")
        data = scraper.scrape_abbr(route.abbr)
        if data is None:
            logger.warning(f"Data not found for route with abbr: {route.abbr}")
            continue
        price, departure_date = data['price'], data['departure_date']
        route_history = RouteHistory(
            route_id=route.id,
            price=price,
            departure_date=departure_date
        )
        session.add(route_history)
    session.commit()




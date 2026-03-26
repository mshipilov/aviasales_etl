import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from .models import Base, Route, RouteHistory
from .scraper import Scraper

load_dotenv()
DB_USER=os.getenv('DB_USER')
DB_PASS=os.getenv('DB_PASS')
DB_HOST=os.getenv('DB_HOST')
DB_PORT=os.getenv('DB_PORT')
DB_NAME=os.getenv('DB_NAME')

database_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(database_url, echo=True)
session = Session(engine)

# create tables if not exist
Base.metadata.create_all(engine)


def get_active_routes():
    stmt = select(Route).where(Route.is_active == True)
    active_routes = session.execute(stmt).scalars().all()
    return active_routes


def add_route(origin: str, destination: str, abbr: str):
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
    session.execute(update(Route).where(Route.abbr==abbr).values(is_active=False))

    session.commit()
    

def extract_data():
    scraper = Scraper()
    for route in session.execute(select(Route).where(Route.is_active==True)).first():
        print(route)
        data = scraper.scrape(route.abbr)
        price, departure_date = data['price'], data['departure_date']
        route_history = RouteHistory(
            route_id=route.id,
            price=price,
            departure_date=departure_date
        )
        session.add(route_history)
    session.commit()




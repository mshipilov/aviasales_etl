# aviasales_etl
Avia tickets prices dashboard

Development plan:

Step 1 - core logic (Done - 5 hours)
1. Get price from aviasales.com (selenium)

Step 2 - DB and ORM
1. SQLAlchemy for ORM?
2. Postgres DB

Step 3 - API & parallelism
1. Endpoints: start monitoring, add route, delete route. FastAPI?
2. Async scraping 

Step 4 - scheduler and data visualization
TBD

## How to run project:
cd /app

docker-compose up

docker build . -t scraper:test

docker run --rm scraper:test


### Run script without Docker:
`pip install uv`
`uv run main.py`
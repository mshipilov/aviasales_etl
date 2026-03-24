# aviasales_etl
air ticket price monitoring

Development plan:

Step 1 - core logic (Done - 5 hours)
1. Get price from aviasales.com (selenium)

Step 2 - DB and ORM (Done - 20 hours)
1. SQLAlchemy for ORM
2. Postgres DB
3. Docker

Step 3 - API (Done - 4 hours)
1. Endpoints (FastAPI): get active routes,  add route, delete route, start scraping


Step 4 - scheduler, data visualization, async scraping 
TBD

## How to run project:
cd /app

docker-compose up

docker build . -t scraper:orm

`docker run -it -p 8080:8000 --network app_default --name scraper --entrypoint /bin/bash --rm  scraper:orm` # for testing
`docker run -p 8080:8000 --network app_default --name scraper scraper:orm --host 0.0.0.0 --port 8000` # main version



### Run script without Docker:
`pip install uv`
`uv run uvicorn app.api:app`
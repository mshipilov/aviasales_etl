# aviasales_etl
air ticket price monitoring

## Architecture
Aviasales API -> Scraper -> Transformation -> Database -> FastAPI

## Quick Start
cd /app

docker-compose up

docker build . -t scraper:orm

`docker run -it -p 8080:8000 --network app_default --name scraper --entrypoint /bin/bash --rm  scraper:orm` # for testing
`docker run -p 8080:8000 --network app_default --name scraper scraper:orm --host 0.0.0.0 --port 8000` # main version



### Run script without Docker:
`pip install requirements.txt`
`uvicorn src.main:app`


from fastapi import FastAPI, HTTPException, status
from .crud import get_active_routes, add_route, deactivate_route, extract_data

app = FastAPI()


@app.get('/routes/')
def get_routes():
    active_routes = get_active_routes()
    return active_routes

@app.post('/routes/add/')
def create_route(origin: str, destination: str, abbr: str):
    add_route(
        origin=origin,
        destination = destination,
        abbr=abbr
        ) 

@app.patch('/routes/deactivate/')
def deactivate(abbr: str):
    deactivate_route(abbr)


@app.post('/scrape/')
def scrape():
    extract_data()


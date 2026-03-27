from fastapi import FastAPI,Response, HTTPException, status
from .crud import get_active_routes, add_route, deactivate_route, get_route_history, extract_data

app = FastAPI()


@app.get('/routes/')
def get_routes():
    active_routes = get_active_routes()
    if not active_routes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No active routes found. You need to add one."
        )
    return active_routes

@app.post('/routes/add/')
def create_route(origin: str, destination: str, abbr: str):
    route = add_route(
        origin=origin,
        destination = destination,
        abbr=abbr
        ) 
    return True

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


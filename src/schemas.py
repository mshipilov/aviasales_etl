from typing import List
from datetime import date

from pydantic import BaseModel, Field


class ScrapeInput(BaseModel):
    origin: str = Field(description="city or country in Russian language (start point)")
    destination: str = Field(description="city or country in Russian language (finish point)")

class ScrapeResult(ScrapeInput):
    abbr: str = Field(description="the abbreviation of route as it used in url For example https://www.aviasales.ru/?params=OVBUIO1 abbr is OVBUIO1")
    price: int 
    departure_date: date


'''
class ScrapeRequest(BaseModel):
    # Ensures the list has at least 1 item and at most 3 items
    abbrs: List[str] = Field(
        min_length=1, 
        max_length=3, 
        description="A list containing between 1 and 3 route abbreviations to scrape."
    )
'''
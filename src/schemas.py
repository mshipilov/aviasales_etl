from typing import List
from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict


class CustomBaseModel(BaseModel):    
    def __repr__(self) -> str:
        # Create a clean, readable representation: ClassName(field1=val1, field2=val2)
        fields = ", ".join(f"{k}={v!r}" for k, v in self.model_dump().items())
        return f"{self.__class__.__name__}({fields})"


class ScrapeInput(CustomBaseModel):
    """here user input"""
    origin: str = Field(description="city or country in Russian language (start point)")
    destination: str = Field(description="city or country in Russian language (finish point)")

class ScrapeContext(ScrapeInput):
    """here user's typos in origin and destination are fixed by scraper"""
    abbr: str = Field(description="the abbreviation of route as it used in url For example https://www.aviasales.ru/?params=OVBUIO1 abbr is OVBUIO1")


class ScrapeResult(ScrapeContext):
    price: int 
    departure_date: date

class RouteResult(CustomBaseModel):
    id: int
    origin: str
    destination: str
    abbr: str

    model_config = ConfigDict(from_attributes=True)

class RouteHistoryInput(CustomBaseModel):
    route_ids: list[int]     

class RouteHistoryResult(CustomBaseModel):
    id: int
    extracted_at: datetime
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
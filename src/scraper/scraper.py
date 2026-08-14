import asyncio
import re

from playwright.async_api import async_playwright

from .utils import parse_russian_date
from ..schemas import ScrapeInput, ScrapeContext, ScrapeSuccess

# this is my worker
class AsyncScraper:
    def __init__(self, page):
        self.page = page
    
    async def add_headers(self):
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        })

    async def get_route_abbr(self, scrape_input: ScrapeInput) -> ScrapeContext:
            
        await self.page.goto('https://aviasales.ru', wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        arrival_input = self.page.locator('//*[@id="avia_form_origin-input"]')
        await arrival_input.fill(scrape_input.origin)
        await asyncio.sleep(2)
        
        destination_input = self.page.locator('//*[@id="avia_form_destination-input"]')
        await destination_input.fill(scrape_input.destination)
        await asyncio.sleep(2)
        
        await self.page.keyboard.press("Tab")
        await asyncio.sleep(2)
        
        url = self.page.url
        abbr = url.split('params=')[1] if 'params=' in url else ""
        
        # re-write origin and destination if they were corrected by website
        origin = await arrival_input.input_value()
        destination = await destination_input.input_value()

        scrape_context = ScrapeContext(origin=origin, destination=destination, abbr=abbr)

        return scrape_context

    async def scrape_abbr(self, scrape_context: ScrapeContext) -> ScrapeSuccess:
        url = f'https://www.aviasales.ru/?params={scrape_context.abbr}'
        print(url)

        # open url only if not open yet
        if self.page.url != url:
            await self.page.goto(url, wait_until="domcontentloaded")
        
        # Using async wait_for_selector
        price_element = await self.page.wait_for_selector('//*[@data-test-id="price"]', timeout=15000)
        price_text = await price_element.inner_text()
        price_str = ''.join(re.findall(r'\d+', price_text))
        price = int(price_str)
        
        date_element = self.page.locator('//*[@class="s__SWoCP6V89bMo15td s__uRnfhGiRypgq1l27 s__NwaJc47i36olMXsl"]').first
        date_text = await date_element.inner_text()
        departure_date = parse_russian_date(date_text)

        scrape_result = ScrapeSuccess(price=price, departure_date=departure_date, **scrape_context.model_dump())
        
        return scrape_result
    
    async def scrape_by_input(self, scrape_input: ScrapeInput) -> ScrapeSuccess:
        await self.add_headers()
        scrape_context = await self.get_route_abbr(scrape_input)
        scrape_result = await self.scrape_abbr(scrape_context)

        return scrape_result
        
    async def scrape_by_context(self, scrape_context: ScrapeContext) -> ScrapeSuccess:
        await self.add_headers()
        scrape_result = await self.scrape_abbr(scrape_context)

        return scrape_result

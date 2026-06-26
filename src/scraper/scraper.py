import asyncio
import re

from playwright.async_api import async_playwright

from .utils import parse_russian_date
from ..schemas import ScrapeInput

# this is my worker
class AsyncScraper:
    def __init__(self, browser_context):
        # Pass the context directly to the worker instance
        self.context = browser_context
        self.page = None

    async def init_page(self):
        """Initializes a new page with a custom user agent."""
        self.page = await self.context.new_page()
        # Set extra HTTP headers to match the user agent
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        })

    async def get_route_abbr(self, scrape_input: ScrapeInput) -> dict:
        """Scrapes route abbreviation

        Args:
            ScrapeInput.origin (str) - city or country in Russian language (start point)
            destination (str) - city or country in Russian language (finish point)

        Returns:
            abbr: the abbreviation of route

        """
        if not self.page:
            await self.init_page()
            
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
        scrape_input.origin = await arrival_input.input_value()
        scrape_input.destination = await destination_input.input_value()

        return {'scrape_input': scrape_input, 'abbr': abbr}

    async def scrape_abbr(self, abbr: str) -> dict:
        """Scrapes data for route abbreviation

        Args:
            abbr (str): the abbreviation of route as it used in url For example https://www.aviasales.ru/?params=OVBUIO1 abbr is OVBUIO1.
            open_url (bool): set it to False if page is already opened

        Returns:
            dict: route data

        """
        if not self.page:
            await self.init_page()

        url = f'https://aviasales.ru/?params={abbr}'

        try:
            # open url only if not open yet
            if self.page.url != url:
                await self.page.goto(url, wait_until="domcontentloaded")
            
            # Using async wait_for_selector
            price_element = await self.page.wait_for_selector('//*[@data-test-id="price"]', timeout=15000)
            price_text = await price_element.inner_text()
            price_str = ''.join(re.findall(r'\d+', price_text))
            price = int(price_str) if price_str else None
            
            date_element = self.page.locator('//*[@class="s__SWoCP6V89bMo15td s__uRnfhGiRypgq1l27 s__NwaJc47i36olMXsl"]').first
            date_text = await date_element.inner_text()
            departure_date = parse_russian_date(date_text)
            
            return {
                "abbr": abbr,
                "price": price,
                "departure_date": departure_date
            }
        except ModuleNotFoundError as e:
            return {"abbr": abbr, "error": str(e)}
        finally:
            if self.page:
                await self.page.close()

async def scrape_worker(context, abbr: str) -> dict:
    """Worker function to handle a single abbreviation scrape job."""
    scraper = AsyncScraper(context)
    return await scraper.scrape_abbr(abbr)

async def scrape_worker2(context) -> str:
    """Worker function to handle a single abbreviation scrape job."""
    scraper = AsyncScraper(context)
    return await scraper.get_route_abbr(ScrapeInput(origin='Н', destination='Моква'))

async def main():
    # Sample batch of abbreviations to scrape concurrently
    abbr_batch = ["OVBSHA1", "OVBBJS1", "OVBCAN1"]
    #abbr_batch = ["OVBSHA1"]
    
    async with async_playwright() as p:
        # Launch browser once
        browser = await p.chromium.launch(headless=False)
        # Create a single context shared by workers (avoids opening multiple browser windows)
        context = await browser.new_context()
        
        # Create concurrent tasks for the entire batch
        #tasks = [scrape_worker(context, abbr) for abbr in abbr_batch]
        tasks = [scrape_worker2(context)]
        
        # await until all tasks completed
        results = await asyncio.gather(*tasks)
        
        # Process results
        for result in results:
            print(result)
            
        await browser.close()

# Run the async loop
if __name__ == "__main__":
    asyncio.run(main())

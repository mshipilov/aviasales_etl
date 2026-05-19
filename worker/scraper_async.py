import asyncio
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright  # type: ignore


def parse_russian_date(date_str):
    # Map Russian month names to month numbers
    russian_months = {
        "янв": "1", "фев": "2", "мар": "3", "апр": "4",
        "мая": "5", "май": "5", "июн": "6", "июл": "7", "авг": "8",
        "сен": "9", "окт": "10", "ноя": "11", "дек": "12"
    }
    
    # Split the input string
    parts = date_str.split()
    day = parts[0]
    month_name = parts[1].lower().replace(',', '')
    month_name = month_name[:3]  # take only first 3 letters to hand changes on frontend
    
    # Get the month number from our dictionary
    month_num = russian_months.get(month_name)
    if not month_num:
        raise ValueError(f"Unknown month: {month_name}")
    
    # Use the current year as a default
    current_year = datetime.now().year
    result_date = datetime(current_year, int(month_num), int(day))

    # if result date < now, use next year
    if result_date < datetime.now():
        result_date = result_date + timedelta(days=365)  # ignore 366 days in year for simplicity
    
    return result_date

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

    async def get_route_abbr(self, origin: str, destination: str) -> str:
        """Scrapes route abbreviation

        Args:
            origin (str) - city or country in Russian language (start point)
            destination (str) - city or country in Russian language (finish point)

        Returns:
            abbr: the abbreviation of route

        """
        if not self.page:
            await self.init_page()
            
        await self.page.goto('https://aviasales.ru', wait_until="domcontentloaded")
        await asyncio.sleep(5)  # Replaced page.wait_for_timeout with asyncio.sleep
        
        arrival_input = self.page.locator('//*[@id="avia_form_origin-input"]')
        await arrival_input.fill(origin)
        await asyncio.sleep(2)
        
        destination_input = self.page.locator('//*[@id="avia_form_destination-input"]')
        await destination_input.fill(destination)
        await asyncio.sleep(2)
        
        await self.page.keyboard.press("tab")
        await asyncio.sleep(2)
        
        url = self.page.url
        abbr = url.split('params=')[1] if 'params=' in url else ""
        return abbr

    async def scrape_abbr(self, abbr: str, open_url: bool = True) -> dict:
        """Scrapes data for route abbreviation

        Args:
            abbr (str): the abbreviation of route as it used in url For example https://www.aviasales.ru/?params=OVBUIO1 abbr is OVBUIO1.
            open_url (bool): set it to False if page is already opened

        Returns:
            dict: route data

        """
        if not self.page:
            await self.init_page()
            
        try:
            if open_url:
                url = f'https://aviasales.ru/?params={abbr}'
                await self.page.goto(url, wait_until="domcontentloaded")
            
            # Using async wait_for_selector
            price_element = await self.page.wait_for_selector('//*[@data-test-id="price"]', timeout=15000)
            price_text = await price_element.inner_text()
            price_str = ''.join(re.findall(r'\d+', price_text))
            
            date_element = self.page.locator('//*[@class="s__SWoCP6V89bMo15td s__uRnfhGiRypgq1l27 s__NwaJc47i36olMXsl"]').first
            date_text = await date_element.inner_text()
            departure_date = parse_russian_date(date_text)
            
            return {
                "abbr": abbr,
                "price": int(price_str) if price_str else None,
                "departure_date": departure_date
            }
        except Exception as e:
            return {"abbr": abbr, "error": str(e)}
        finally:
            if self.page:
                await self.page.close()

async def scrape_worker(context, abbr: str) -> dict:
    """Worker function to handle a single abbreviation scrape job."""
    scraper = AsyncScraper(context)
    return await scraper.scrape_abbr(abbr)

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
        tasks = [scrape_worker(context, abbr) for abbr in abbr_batch]
        
        # Run all scraping tasks in parallel
        results = await asyncio.gather(*tasks)
        
        # Process results
        for result in results:
            print(result)
            
        await browser.close()

# Run the async loop
if __name__ == "__main__":
    asyncio.run(main())

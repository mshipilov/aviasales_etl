import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

class Scraper:
    def __init__(self, p):
        # Using launch_persistent_context mimics a real browser profile to bypass detection
        self.browser = p.chromium.launch(headless=False)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()

    def get_route_abbr(self, origin: str, destination: str) -> str:
        self.page.goto('https://aviasales.ru', wait_until="domcontentloaded")

        self.page.wait_for_timeout(5000)

        arrival_input = self.page.locator('//*[@id="avia_form_origin-input"]')
        arrival_input.fill(origin)

        self.page.wait_for_timeout(2000)

        destination_input = self.page.locator('//*[@id="avia_form_destination-input"]')
        destination_input.fill(destination)

        self.page.wait_for_timeout(2000)

        # press tab to save input
        self.page.keyboard.press("Tab")

        self.page.wait_for_timeout(2000)
        
        abbr = self.page.url.split('params=')[1]
        return abbr

    def scrape_abbr(self, abbr: str, open_url: bool = True) -> dict:
        try:
            if open_url:
                url = f'https://aviasales.ru/?params={abbr}'
                self.page.goto(url, wait_until="domcontentloaded")
            
            # Use Playwright's wait_for_selector instead of manual sleep
            price_element = self.page.wait_for_selector('//*[@data-test-id="price"]')
            price_str = ''.join(re.findall(r'\d+', price_element.inner_text()))
            
            date_element = self.page.locator('//*[@class="s__SWoCP6V89bMo15td s__uRnfhGiRypgq1l27 s__NwaJc47i36olMXsl"]').first
            departure_date = parse_russian_date(date_element.inner_text())
            
            return {'price': int(price_str), 'departure_date': departure_date}
        except Exception as e:
            print(f"Error: {e}")
            return {'price': None, 'departure_date': None}


def parse_russian_date(date_str):
    # Map Russian month names to month numbers
    russian_months = {
        "января": "1", "февраля": "2", "марта": "3", "апреля": "4",
        "мая": "5", "июня": "6", "июля": "7", "августа": "8",
        "сентября": "9", "октября": "10", "ноября": "11", "декабря": "12"
    }
    
    # Split the input string
    parts = date_str.split()
    day = parts[0]
    month_name = parts[1].lower().replace(',', '')
    
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



if __name__ == '__main__':
    with sync_playwright() as p:
        scraper = Scraper(p)
        abbr = scraper.get_route_abbr('Новосибирск', 'Москва')
        print(f"Abbreviation: {abbr}")
        data = scraper.scrape_abbr(abbr, open_url=False)
        print(f"Data: {data}")
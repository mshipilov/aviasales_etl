import re
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


class Scraper:
    
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    def __init__(self):
        self.driver = uc.Chrome(options=self.options, version_main=146)
        #driver_executable_path='/usr/bin/chromedriver')

    def scrape(self, route: str) -> int:
        try:
            print(f'start scraping {route} ...')
            self.driver.get(f'https://www.aviasales.ru/?params={route}')
            
            price_element = self.driver.find_element(By.XPATH, '//*[@data-test-id="price"]')
            price_str = ''.join(re.findall(r'\d+', price_element.text))
            price = int(price_str)

            departure_date_element = self.driver.find_element(By.XPATH, '//*[@class="s__SWoCP6V89bMo15td s__uRnfhGiRypgq1l27 s__NwaJc47i36olMXsl"]')
            departure_date_str = departure_date_element.text
            departure_date = parse_russian_date(departure_date_str)
            return {'price': price, 'departure_date': departure_date}
        except Exception as e:
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Text: {str(e)}")
            return None
            
    def scrape_list(self, route_list: list) -> list:
        price_list = []
        for route in route_list:
            price = self.scrape(route)
            price_list.append(price)
        print('scrape_list finished')
            
        if self.driver:
            self.driver.quit()
            
        return price_list


def parse_russian_date(date_str):
    # Map Russian month names (genitive case) to month numbers
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
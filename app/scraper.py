import re
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from webdriver_manager.core.os_manager import OperationSystemManager, ChromeType

# detect installed Chrome version
browser_version = OperationSystemManager().get_browser_version_from_os(ChromeType.GOOGLE)
major_version = int(browser_version.split('.')[0])

class Scraper:
    
    options = uc.ChromeOptions()
    #options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    def __init__(self):
        self.driver = uc.Chrome(options=self.options, version_main=146)
        #driver_executable_path='/usr/bin/chromedriver')

    def get_route_abbr(self, arrival: str, destination: str) -> str:
        """Scrapes route abbreviation

        Args:
            arrival (str) - название города или страны на русском языке (место отправления)
            destination (str) - название города или страны на русском языке (место прибытия)

        Returns:
            abbr: the abbreviation of route

        """
        self.driver.get(f'https://www.aviasales.ru')
        print('inserting arrival...')
        arrival_input = self.driver.find_element(By.XPATH, '//*[@id="avia_form_origin-input"]')
        arrival_input.clear()
        arrival_input.send_keys(arrival)
        print('inserting destination...')
        destination_input = self.driver.find_element(By.XPATH, '//*[@id="avia_form_destination-input"]')
        destination_input.send_keys(destination)
        print(scraper.driver.current_url)
        abbr = scraper.driver.current_url.split('params=')[1]

        return abbr

    def scrape_abbr(self, abbr: str, open_url: bool = True) -> dict:
        """Scrapes data for route abbreviation

        Args:
            abbr (str): the abbreviation of route as it used in url For example https://www.aviasales.ru/?params=OVBUIO1 abbr is OVBUIO1.
            open_url (bool): set it to False if page is already opened

        Returns:
            dict: route data

        Raises:


        """
        try:
            print(f'start scraping {abbr} ...')
            if open_url:
                self.driver.get(f'https://www.aviasales.ru/?params={abbr}')
            
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
            return {'price': None, 'departure_date': None}
            
    def scrape_list(self, route_list: list) -> list:
        price_list = []
        for route in route_list:
            price = self.scrape_abbr(route)
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


if __name__ == '__main__':
    scraper = Scraper()
    abbr = scraper.get_route_abbr('Новосибирск', 'Москва')
    
    print(abbr)
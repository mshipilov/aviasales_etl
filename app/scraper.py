import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


#os.makedirs('/tmp/chromedriver', exist_ok=True)

#uc.Patcher.data_path = "/tmp/undetected_chromedriver"


class Scraper:
    
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    def __init__(self):
        self.driver = uc.Chrome(options=self.options)
        #driver_executable_path='/usr/bin/chromedriver')

    def scrape(self, route: str) -> int:
        try:
            print(f'start scraping {route} ...')
            self.driver.get(f'https://www.aviasales.ru/?params={route}')
            price_element = self.driver.find_element(By.XPATH, '//*[@data-test-id="price"]')
            price_str = ''.join(re.findall(r'\d+', price_element.text))
            price = int(price_str)
            print(price)
            return price
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
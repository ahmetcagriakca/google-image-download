import hashlib
import io
import os
import sys
import time

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver


class GoogleImageDownloader:
    def __init__(self, query: str, max_links_to_fetch: int, driver_path='chromedriver.exe', base_folder='./images',
                 sleep_between_interactions=0.5):
        self.sleep_between_interactions = sleep_between_interactions
        self.base_folder = base_folder
        self.max_links_to_fetch = max_links_to_fetch
        self.query = query
        self.image_folder = os.path.join(self.base_folder, '_'.join(self.query.lower().split(' ')))
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        if driver_path is None or driver_path == '':
            raise Exception(f'Driver path required')

        if not os.path.exists(driver_path):
            raise Exception(f'driver not found on path:{driver_path}')
        self.driver_path = driver_path
        self.driver: WebDriver = webdriver.Chrome(executable_path=self.driver_path)

    def __del__(self):
        self.driver.close()

    def persist_image(self, url: str):
        try:
            image_content = requests.get(url).content
        except Exception as e:
            print(f"ERROR - Could not download {url} - {e}")
            return

        try:
            image_file = io.BytesIO(image_content)
            image = Image.open(image_file).convert('RGB')
            file_path = os.path.join(self.image_folder, hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
            with open(file_path, 'wb') as f:
                image.save(f, "JPEG", quality=85)
            print(f"SUCCESS - saved {url} - as {file_path}")
        except Exception as e:
            print(f"ERROR - Could not save {url} - {e}")

    def scroll_to_end(self):
        '''
        required for all detail loading
        :return:
        '''
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(self.sleep_between_interactions)

    def fetch_image_urls(self):
        search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"
        # load the page
        self.driver.get(search_url.format(q=self.query))

        image_urls = set()
        image_count = 0
        results_start = 0
        while image_count < self.max_links_to_fetch:
            self.scroll_to_end()

            # get all image thumbnail results
            thumbnail_results = self.driver.find_elements_by_css_selector("img.Q4LuWd")
            number_results = len(thumbnail_results)

            print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

            for img in thumbnail_results[results_start:number_results]:
                # try to click every thumbnail such that we can get the real image behind it
                try:
                    img.click()
                    time.sleep(self.sleep_between_interactions)
                except Exception:
                    continue

                # extract image urls
                actual_images = self.driver.find_elements_by_css_selector('img.n3VNCb')
                for actual_image in actual_images:
                    if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                        image_urls.add(actual_image.get_attribute('src'))

                image_count = len(image_urls)

                if len(image_urls) >= self.max_links_to_fetch:
                    print(f"Found: {len(image_urls)} image links, done!")
                    break
            else:
                print("Found:", len(image_urls), "image links, looking for more ...")
                time.sleep(30)
                return
                load_more_button = self.driver.find_element_by_css_selector(".mye4qd")
                if load_more_button:
                    self.driver.execute_script("document.querySelector('.mye4qd').click();")

            # move the result startpoint further down
            results_start = len(thumbnail_results)

        return image_urls

    def start(self):
        urls = self.fetch_image_urls()
        if urls is not None and len(urls )> 0:
            for url in urls:
                self.persist_image(url)


if len(sys.argv) < 2:
    search_term = input("Search term:")
    if search_term is None or search_term == '':
        print('Search term required')
        exit
else:
    search_term = sys.argv[1]

if len(sys.argv) < 3:
    count = input("Count:")
    image_count = int(count)
else:
    image_count = int(sys.argv[2])

print(f'Search term:{search_term} Count:{image_count}')
GoogleImageDownloader(query=search_term, max_links_to_fetch=image_count).start()

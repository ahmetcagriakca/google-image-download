import io
import os
import sys
import time

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from urllib.parse import urlparse


class ImageDownloader:
    def __init__(self, search_url: str, target_folder: str, driver_path='chromedriver.exe', base_folder='./images',
                 sleep_between_interactions=0.5):
        self.sleep_between_interactions = sleep_between_interactions
        self.base_folder = base_folder
        self.target_folder = target_folder
        self.search_url = search_url
        if target_folder is not None and target_folder != '':
            self.image_folder = os.path.join(self.base_folder, '_'.join(self.target_folder.lower().split(' ')))
        else:
            self.image_folder = self.base_folder
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        if driver_path is None or driver_path == '':
            raise Exception(f'Driver path required')

        if not os.path.exists(driver_path):
            raise Exception(f'driver not found on path:{driver_path}')
        self.driver_path = driver_path
        self.driver: WebDriver = webdriver.Chrome(executable_path=self.driver_path)

    def __del__(self):
        if hasattr(self, 'driver') and self.driver is not None:
            self.driver.close()

    def persist_image(self, url: str):
        try:
            image_content = requests.get(url).content
        except Exception as e:
            print(f"ERROR - Could not download {url} - {e}")

        try:
            image_file = io.BytesIO(image_content)
            image = Image.open(image_file).convert('RGB')
            file_path = os.path.join(self.image_folder, urlparse(url).path[1:].replace('/', '_') + '.jpg')
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

    def find_images(self):
        image_elements = self.driver.find_elements_by_xpath("//label[starts-with(@id,'label_images_')]/img")
        image_urls = []
        for image_order in range(1, len(image_elements)):
            if image_order == len(image_elements):
                image_xpath = f"//label[starts-with(@id,'label_images_{image_order}')]/img"
            else:
                image_xpath = f"//label[starts-with(@id,'label_images_0')]/img"
            try:
                element = self.driver.find_element_by_xpath(image_xpath)
            except:
                print(f'image {image_order} not found')
                break
            image_urls.append(element.get_attribute('src'))
            click_element = self.driver.find_element_by_class_name(f"classifiedDetailMainPhoto")
            click_element.click()
            time.sleep(self.sleep_between_interactions)
        return image_urls

    def open_detail(self, order: int):
        try:
            find_list = WebDriverWait(self.driver, 10).until(
                lambda driver: driver.find_elements_by_css_selector(
                    f"#searchResultsTable tr:nth-child({order})"))
            if len(find_list) == 1:
                row = find_list[0]
            elif len(find_list) == 2:
                row = find_list[1]
            else:
                return False
            if 'nativeAd' in row.get_attribute('class'):
                return False
            row.click()
        except Exception as ex:
            print(ex)
            return False
        return True

    def find_rows(self):
        rows = WebDriverWait(self.driver, 10).until(
            lambda driver: driver.find_elements_by_css_selector("#searchResultsTable tr"))
        return rows

    def start(self):
        self.driver.get(self.search_url)
        self.driver.refresh()
        time.sleep(self.sleep_between_interactions)
        rows = self.find_rows()
        start = 1
        for order in range(len(rows)):
            if order < start:
                continue
            self.scroll_to_end()
            result = self.open_detail(order=order)
            if not result:
                print(f'row {order} not found')
                continue
            time.sleep(self.sleep_between_interactions)

            image_urls = self.find_images()

            for elem in image_urls:
                self.persist_image(elem)

            self.driver.back()
            time.sleep(1)


if len(sys.argv) < 2:
    search_url = input("Search url:")
    if search_url is None or search_url == '':
        print('Search Url required')
        exit
else:
    search_url = sys.argv[1]

if len(sys.argv) < 3:
    folder = input("Target folder:")
else:
    folder = sys.argv[2]

print(f'Search url:{search_url} Target folder:{folder}')
ImageDownloader(search_url=search_url, target_folder=folder).start()

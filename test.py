from selenium import webdriver
# This is the path I use
# DRIVER_PATH = '.../Desktop/Scraping/chromedriver 2'
# Put the path for your ChromeDriver here
DRIVER_PATH = 'chromedriver.exe'
wd = webdriver.Chrome(executable_path=DRIVER_PATH)
# wd.get('https://www.sahibinden.com/volkswagen-golf')
wd.get('https://google.com')
search_box = wd.find_element_by_css_selector('input.gLFyf')
search_box.send_keys('Dogs')
# wd.quit()
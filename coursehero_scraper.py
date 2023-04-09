from selenium import webdriver
import seleniumwire.undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
import pandas as pd
import numpy as np
import time
import os
import random
from pathlib import Path
import shutil
import time
import sys

def scrape_coursehero(keywords, proxies):

    start_time = time.time()
    # configuring the path for the optional csv output file
    path = os.getcwd()
    if '//' in path:
        path += '//scraped_data.csv'
    else:
        path += '\scraped_data.csv'

    scraped = []
    # check if there is a previous output to resume it
    if os.path.isfile(path):
        df = pd.read_csv(path)
        scraped = df.keyword.values
    else:
        # initialize the output dataframe
        df = pd.DataFrame()
    nwords = len(keywords)
    print('Initializing the web bot ...')
    print('-'*75)
    driver = initialize_bot(proxies)
    print('Searching the keywords ...')
    print('-'*75)
    for i, keyword in enumerate(keywords):
        data = []
        # skip keywords already scraped
        if keyword in scraped:
            continue
        try:
            # iterating the user agent for the bot
            # agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(random.randint(90, 140))
            # driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": agent})                
            driver.get('https://www.coursehero.com')
            search = wait(driver, 30).until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='search']")))[0]
            search.click()
            time.sleep(1)
            search.send_keys(keyword)
            time.sleep(1)
            search.send_keys(Keys.ENTER)
            time.sleep(3)
            try:
                nres = wait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.query-subtitle"))).text.split(' ')[0].replace(',', '')
            except:
                # No search results
                nres = np.nan
             
            data.append({'keyword':keyword, "#Results":nres, 'Link':driver.current_url})
            df = df.append(data)
            print(f'Keyword {i+1}/{nwords} is scraped')
            # output scraped data to csv each 100 keywords
            if np.mod(i+1, 50) == 0:
                print('Outputting scraped data to csv file ...')
                df.to_csv(path, encoding='UTF-8', index=False)

        except Exception as err:
            # handling errors
            print('-'*75)
            print('The below error occurred, exiting:')
            print(str(err))   
            df.to_csv(path, encoding='UTF-8', index=False)
            driver.quit()
            sys.exit()


    driver.quit()
    # output the dataframe to a csv 
    df.to_csv(path, encoding='UTF-8', index=False)
    mins = round((time.time() - start_time)/60, 2)
    hrs = round(mins / 60, 2)
    print(f'process completed successfully! Elsapsed time {hrs} hours ({mins} mins)')

    return df

def initialize_bot(proxies):

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument("--start-maximized")
    chrome_options.page_load_strategy = 'eager'
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(60)

    return driver

def get_keywords():

    # assuming the input csv file to be the same directory of the script
    path = os.getcwd()
    if '//' in path:
        path += '//data_to_scrape.csv'
    else:
        path += '\data_to_scrape.csv'

    df = pd.read_csv(path)
    df[['Title', 'Author']] =  df[['Title', 'Author']].astype(str)
    df['Title'] =  df['Title'].apply(lambda x: x.replace('"', ''))
    df['Author'] =  df['Author'].apply(lambda x: x.replace('"', ''))
    df[['Title', 'Author']] =  df[['Title', 'Author']].apply(lambda x: '"' + x + '"')
    df['keywords'] = df['Title'] + ' ' + df['Author']

    return df['keywords'].values.tolist()

if __name__ == "__main__":

    # reading the keywords from a given csv file if applicable
    keywords = get_keywords()
    # empty proxies df means no proxies to be used 
    proxies = pd.read_csv('proxies.csv') 
    # scraping the keywords results
    results = scrape_coursehero(keywords, proxies)

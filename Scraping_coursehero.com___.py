from selenium import webdriver
import seleniumwire.undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
#import undetected_chromedriver.v2 as uc
import pandas as pd
import numpy as np
import time
import os
import random
from pathlib import Path
import shutil
import time

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
        # iterate 5 times over each keyword till scraped successfully
        for _ in range(5):
            try:
                # iterating the user agent for the bot
                agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(random.randint(90, 140))
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": agent})
                try:
                    driver.command_executor.set_timeout(10)
                    driver.get('https://www.coursehero.com/')
                except:
                    # handling page loading issues 
                    driver.refresh()
                    time.sleep(3)
                    continue

                wait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//input[@type='search' and @aria-label='Find study guides, class notes and more.']"))).click()
                time.sleep(1)
                wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@type='search' and @aria-label='Find study guides, class notes and more.']"))).send_keys(keyword)
                time.sleep(1)
                wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@type='search' and @aria-label='Find study guides, class notes and more.']"))).send_keys(Keys.ENTER)
                time.sleep(4)
                try:
                    nres = wait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.query-subtitle"))).text.split(' ')[0].replace(',', '')
                except:
                    # No search results
                    nres = np.nan
                 
                data.append({'keyword':keyword, "#Results":nres, 'Link':driver.current_url})
                df = df.append(data)
                print(f'Keyword {i+1}/{nwords} is scraped')
                # output scraped data to csv each 100 keywords
                if np.mod(i+1, 100) == 0:
                    print('Outputting scraped data to csv file ...')
                    df.to_csv(path, encoding='UTF-8', index=False)
                break
            except Exception as err:
                # handling errors
                print('-'*75)
                print('The below error occurred, restarting :')
                print(str(err))   
                print('-'*75)
                print('Restarting the session ....')
                print('-'*75)
                df.to_csv(path, encoding='UTF-8', index=False)
                driver.quit()
                time.sleep(5)
                driver = initialize_bot(proxies)
                continue

    driver.quit()
    # output the dataframe to a csv 
    df.to_csv(path, encoding='UTF-8', index=False)
    mins = round((time.time() - start_time)/60, 2)
    hrs = round(mins / 60, 2)
    print(f'process completed successfully! Elsapsed time {hrs} hours ({mins} mins)')

    return df

def initialize_bot(proxies):

    class Spoofer(object):

        def __init__(self, proxies=proxies):
            self.proxies = proxies
            if self.proxies.shape[0] > 0:
                self.userAgent, self.ip, self.port, self.username, self.password = self.get()

        def get(self):
            ua = ('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(random.randint(90, 140)))
            nprox = len(self.proxies)
            rand_ind = random.randint(0, nprox-1)
            ip = self.proxies.loc[rand_ind, 'ip']
            port = self.proxies.loc[rand_ind, 'port_http']
            username = self.proxies.loc[rand_ind, 'login']
            password = self.proxies.loc[rand_ind, 'password']
            return ua, ip, port, username, password

    class DriverOptions(object):

        def __init__(self):

            self.options = uc.ChromeOptions()
            self.options.add_argument('--log-level=3')
            self.options.add_argument('--start-maximized')
            self.options.add_argument('--disable-dev-shm-usage')
            self.options.add_argument("--incognito")
            self.helperSpoofer = Spoofer()
            if self.helperSpoofer.proxies.shape[0] > 0:
                self.seleniumwire_options = {'proxy':{'https': f'http://{str(self.helperSpoofer.username)}:{str(self.helperSpoofer.password)}@{str(self.helperSpoofer.ip)}:{str(self.helperSpoofer.port)}', 'http':f'http://{str(self.helperSpoofer.username)}:{str(self.helperSpoofer.password)}@{str(self.helperSpoofer.ip)}:{str(self.helperSpoofer.port)}', 'no_proxy':'localhost, 127.0.0.1'}}
            else:
                self.seleniumwire_options = {}
           

            # random user agent
            self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(random.randint(90, 140)))
            self.options.page_load_strategy = 'eager'
           
            # Create empty profile for non Windows OS
            if os.name != 'nt':
                if os.path.isdir('./chrome_profile'):
                    shutil.rmtree('./chrome_profile')
                os.mkdir('./chrome_profile')
                Path('./chrome_profile/First Run').touch()
                self.options.add_argument('--user-data-dir=./chrome_profile/')
   
            # using proxies without credentials
            #if proxies:
            #   self.options.add_argument('--proxy-server=%s' % self.helperSpoofer.ip)


    class WebDriver(DriverOptions):

        def __init__(self):
            DriverOptions.__init__(self)
            self.driver_instance = self.get_driver()

        def get_driver(self):
            try:     
                PROXY = str(self.helperSpoofer.ip) + ':' + str(self.helperSpoofer.port)
                webdriver.DesiredCapabilities.CHROME['proxy'] = {
                    "httpProxy":PROXY,
                    "ftpProxy":PROXY,
                    "sslProxy":PROXY,
                    "noProxy":None,
                    "proxyType":"MANUAL",
                    "autodetect":False}
            except:
                pass

            webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
      
            # uc Chrome driver
            driver = uc.Chrome(options=self.options, seleniumwire_options=self.seleniumwire_options)
            driver.set_page_load_timeout(20)
            # configuring the driver for less detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source":
                    "const newProto = navigator.__proto__;"
                    "delete newProto.webdriver;"
                    "navigator.__proto__ = newProto;"})

            return driver

    driver= WebDriver()
    driverinstance = driver.driver_instance
    return driverinstance

def get_keywords():

    # assuming the input csv file to be the same directory of the script
    path = os.getcwd()
    if '//' in path:
        path += '//data_to_scrape.csv'
    else:
        path += '\data_to_scrape.csv'

    df = pd.read_csv(path)
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

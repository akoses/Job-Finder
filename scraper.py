from timeit import repeat
from typing import Any, List
from urllib.parse import urlencode
import bs4
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from tqdm import tqdm
import re
import time

from bs4 import BeautifulSoup
import requests


def build_url(url, params):
    return url + "?" + urlencode(params)


class Scraper:
    """
    Scraper base class.
    Each scraper must implement the scrape method.
    """

    def __init__(self, query, **kwargs):
        self.query = query
        self.kwargs = kwargs
        # List for all our scraped data

        # List for all our scraped sentences/list elements
        self.jobs: List[dict] = []

        # Set up the webdriver add headless mode
        

    def __str__(self):
        return f"Scraper({self.query}, {self.kwargs})"

    def scrape(self, location: str = ""):
        raise NotImplementedError("Subclass must implement abstract method")


class LinkedInScraper(Scraper):
    def __init__(self, query, **kwargs):
        super().__init__(query, **kwargs)
        self.query = query
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        self.driver.set_window_size(2048, 768)
        self.start_url = "https://www.linkedin.com/jobs/search/"

    def scrape(self, location: str = "Canada"):
        full_url = build_url(
            self.start_url,
            {
                "keywords": self.query,
                "location": location,
                "trk": "public_jobs_jobs-search-bar_search-submit",
                "redirect": "false",
                "position": 1,
                "pageNum": 0,
            },
        )

        self.driver.get(full_url)
        rep = {",": "", "+": ""}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))

        job_count = self.driver.find_element(By.CSS_SELECTOR, "h1>span").text
        job_count = pattern.sub(lambda m: rep[re.escape(m.group(0))], job_count)
        job_count = int(job_count)

        i = 2
        curr_len = 0
        pbar = tqdm(total=job_count // 25)
        while i <= int(job_count / 25) + 1:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            i = i + 1
            pbar.update(1)
            try:
                job_lists = self.driver.find_element(
                    By.CLASS_NAME, "jobs-search__results-list"
                )
                jobs = job_lists.find_elements(By.TAG_NAME, "li")
                if curr_len == len(jobs):
                    break
                curr_len = len(jobs)
                self.driver.find_element(
                    By.CLASS_NAME, "infinite-scroller__show-more-button"
                ).click()
                time.sleep(3)
            except Exception:
                time.sleep(3)
        # return a list
        job_lists = self.driver.find_element(By.CLASS_NAME, "jobs-search__results-list")
        jobs = job_lists.find_elements(By.TAG_NAME, "li")
        job_dicts = []
        for item, job in enumerate(tqdm(jobs)):
            try:
                title = job.find_element(By.TAG_NAME, "h3").text
                company = job.find_element(By.TAG_NAME, "h4").text
                location = job.find_element(
                    By.CSS_SELECTOR, "span.job-search-card__location"
                ).text
                link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
                job_click_path = (
                    f"/html/body/div[1]/div/main/section[2]/ul/li[{item + 1}]"
                )
                job.find_element(By.XPATH, job_click_path).click()
                time.sleep(2.5)

                description = self.driver.find_element(
                    By.CLASS_NAME, "show-more-less-html__markup"
                ).get_attribute("innerHTML")

                job_dict = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "description": description,
                }
                job_dicts.append(job_dict)

            except Exception:
                pass

        pd.DataFrame(job_dicts).to_csv("linkedin_jobs.csv")

        self.jobs = job_dicts


class IndeedScraper(Scraper):
    def __init__(self, query, **kwargs):
        super().__init__(query, **kwargs)
        self.query = query
        self.start_url = "https://ca.indeed.com/jobs"
        self.jobs = []
        self.job_set = set()

    def scrape(self, location: str = "Canada"):
        url_dict = {"q": self.query, "l": location, "start": 0}
        full_url = build_url(self.start_url, url_dict)
        soup = BeautifulSoup(requests.get(full_url).text, "html.parser")

        jobs = soup.find_all('a', {'class':'result'})
        while not jobs:
            soup = BeautifulSoup(requests.get(full_url).text, "html.parser")
            jobs = soup.find_all('a', {'class':'result'})
        
        repeat = 0
        while True:
            
            for job in tqdm(jobs):
                
                title = job.find('h2', {'class': 'jobTitle'})
                company = job.find('span', {'class':'companyName'})
                location = job.find('div', {'class':'companyLocation'})
                if not title or not company or not location:
                    continue
                link = f'https://ca.indeed.com{job.get("href")}'
                
                if title.get_text()+company.get_text()+location.get_text() in self.job_set:
                    repeat += 1
                    continue
                else:
                    self.job_set.add(title.get_text()+company.get_text()+location.get_text())
                
                description_soup = BeautifulSoup(requests.get(link).text, "html.parser")
                description = description_soup.find('div', {'class':'jobsearch-jobDescriptionText'})

                job_dict = {
                    "title": title.get_text(),
                    "company": company.get_text(),
                    "location": location.get_text(),
                    "link": link,
                    "description": str(description),
                }

                
            
                self.jobs.append(job_dict)
            
            if repeat >= 10:
                break
            
            url_dict['start'] += 10
            url = build_url(self.start_url, url_dict)
            soup = BeautifulSoup(requests.get(url).text, "html.parser")
            jobs = soup.find_all('a', {'class':'result'})

            while not jobs:
                soup = BeautifulSoup(requests.get(url).text, "html.parser")
                jobs = soup.find_all('a', {'class':'result'})

            
           


    

        pd.DataFrame(self.jobs).to_csv("indeed_jobs.csv")


class MonsterScraper(Scraper):
    def __init__(self, query, **kwargs):
        super().__init__(query, **kwargs)
        self.query = query
        self.start_url = "https://www.monster.ca/jobs/search/"

        options = Options()
        #options.add_argument("--headless")
        #options.add_argument("--disable-gpu")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        self.driver.set_window_size(2048, 768)
    
    def scrape(self, location: str = "Canada"):
        url_dict = {"q": self.query, "where": location, "start": 0}
        full_url = build_url(self.start_url, url_dict)
        self.driver.get(full_url)
        self.driver.implicitly_wait(3)
        vertical = 100
        while True:
            try:

                el = self.driver.find_element(By.CLASS_NAME, "infinite-scroll-component__outerdiv")
                self.driver.execute_script("arguments[0].scrollTop = arguments[1]", el, vertical)
                vertical += 100
                button = self.driver.find_element(By.CLASS_NAME, "ds-button")
                button.click()
                

            except Exception as e:
                print(e)

            time.sleep(3)
            
        return self.query


class GlassDoorScraper(Scraper):
    def __init__(self, query, **kwargs):
        super().__init__(query, **kwargs)
        self.query = query

    def scrape(self, location: str = ""):
        return self.query


if __name__ == "__main__":
    scraper = MonsterScraper("Software Engineer")
    scraper.scrape(location="Canada")


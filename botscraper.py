import os
import time
import logging
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

class NewsBot:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.driver = self.setup_driver()
        os.environ["SEARCH_PHRASE"] = "Bitcoin"
        os.environ["TOPIC"] = "Business"

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def setup_driver(self):
        service = Service(executable_path="chromedriver.exe")
        driver = webdriver.Chrome(service=service)
        driver.maximize_window()
        return driver

    def navigate_and_search(self, search_phrase):
        self.logger.info("Navigating to the news site...")
        self.driver.get("https://www.latimes.com/")

        try:
            search_button = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-element='search-button']")))
            search_button.click()
            search_input = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-element='search-form-input']")))
            search_input.send_keys(search_phrase)
            search_input.send_keys(Keys.ENTER)
            return True
        except TimeoutException:
            self.logger.error("Timeout occurred while searching for elements.")
            return False

    def select_topic_and_latest_news(self, topic):
        self.logger.info(f"Selecting topic: {topic}")
        try:
            topic_checkbox = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.CLASS_NAME, "checkbox-input-element")))
            topic_checkbox.click()
            topic_span = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, f"//span[text()='{topic}']")))
            topic_span.click()
            return True
        except TimeoutException:
            self.logger.error("Timeout occurred while selecting topic.")
            return False

    def extract_news_data(self, search_phrase):
        self.logger.info("Extracting news data...")
        parent_ul = self.driver.find_element(By.CLASS_NAME, "search-results-module-results-menu")
        articles = parent_ul.find_elements(By.TAG_NAME, "li")
        news_data = []

        if not articles:
            self.logger.info("No articles found.")
            return news_data

        for article in articles:
            try:
                title = article.find_element(By.CLASS_NAME, "promo-title").text
                date = article.find_element(By.CLASS_NAME, "promo-timestamp").text
                description = article.find_element(By.CLASS_NAME, "promo-description").text
                title_occurrences = title.lower().count(search_phrase.lower())
                description_occurrences = description.lower().count(search_phrase.lower())
                contains_money = "$" in title or "$" in description

                try:
                    image_url = article.find_element(By.TAG_NAME, "img").get_attribute("src")
                    image_filename = self.download_image(image_url)
                except NoSuchElementException:
                    image_filename = None

                news_data.append({
                    "Title": title,
                    "Date": date,
                    "Description": description,
                    "Picture Filename": image_filename,
                    "Title Search Phrase Occurrences": title_occurrences,
                    "Description Search Phrase Occurrences": description_occurrences,
                    "Contains Money": contains_money
                })

                self.logger.info("News data extracted successfully.")
            except StaleElementReferenceException:
                self.logger.warning("StaleElementReferenceException occurred. Refreshing page and retrying extraction...")
                self.driver.refresh()
                return self.extract_news_data(search_phrase)

        return news_data

    def download_image(self, url):
        if not os.path.exists("images"):
            os.makedirs("images")
        response = requests.get(url)
        image_filename = f"image_{time.time()}.jpg"
        with open(f"images/{image_filename}", "wb") as f:
            f.write(response.content)
        return image_filename

    def save_to_excel(self, news_data):
        df = pd.DataFrame(news_data)
        df.to_excel("/output/news_data.xlsx", index=False)
        self.logger.info("News data saved to Excel.")

    def run(self):
        search_phrase = os.getenv("search_phrase")
        topic = os.getenv("topic")

        if not search_phrase or not topic:
            self.logger.error("Search phrase or topic not provided.")
            return

        if not self.navigate_and_search(search_phrase):
            self.logger.error("Navigation and search failed.")
            return

        if not self.select_topic_and_latest_news(topic):
            self.logger.error("Selecting topic and latest news failed.")
            return

        news_data = self.extract_news_data(search_phrase)

        if news_data:
            self.save_to_excel(news_data)
        else:
            self.logger.warning("No news data extracted.")

        self.driver.quit()
        self.logger.info("Script execution completed.")

if __name__ == "__main__":
    bot = NewsBot()
    bot.run()

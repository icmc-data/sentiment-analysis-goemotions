import re
import os
import time
import traceback
import psycopg2

from tqdm import tqdm
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


NUM_REVIEWS_PER_LOAD = 25
TITLES_TO_FETCH = 2

@dataclass
class ReviewInfo:
    text: str
    rating: int
    title: str
    author: str
    date: str


class DatabaseHelper:
    def __init__(self):
        print("Init DB connection")
        self.mydb = self.wait_for_db()
        self.cursor = self.mydb.cursor()

    def insert_review(self, title_id, review: ReviewInfo):
        self.cursor.execute(
            f'INSERT INTO IMDB_Reviews \
            (review_rating, review_title, review_author, review_date, review_text, title_id) \
            VALUES (%s, %s, %s, %s, %s, %s)',
            (review.rating, review.title, review.author, review.date, review.text, title_id)
        )

    def query_title(self, title_name, n_reviews) -> str:
        title_name = re.sub(r'\'', "''", title_name)
        self.cursor.execute(f"SELECT title FROM IMDB_Titles WHERE title='{title_name}'")
        title_id = self.cursor.fetchone()
        if title_id is None:
            self.cursor.execute(
                f'INSERT INTO IMDB_Titles (title, n_reviews) VALUES (%s, %s) RETURNING title_id',
                (title_name, n_reviews))
            title_id = self.cursor.fetchone()[0]
        else:
            title_id = title_id
        return title_id

    def commit_changes(self):
        self.mydb.commit()

    def close_connection(self):
        self.cursor.close()
        self.mydb.close()
        print("Close DB connection")

    @staticmethod
    def wait_for_db():
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            try:
                # Tenta conectar ao banco de dados
                mydb = psycopg2.connect(
                    host='postgresql',
                    user=os.environ.get('POSTGRES_USER'),
                    password=os.environ.get('POSTGRES_PASSWORD'),
                    database=os.environ.get('POSTGRES_NAME'),
                    port=os.environ.get('POSTGRES_PORT')
                )
                return mydb
            except Exception as err:
                print(f"Erro ao conectar ao banco de dados: {err}")
                attempts += 1
                time.sleep(5)  # Aguarda 5 segundos antes de tentar novamente
        # Caso atinja o limite de tentativas, exibe uma mensagem de erro
        print("Não foi possível conectar ao banco de dados após várias tentativas.")


class ImdbScraper:
    driver = None
    mydb = None

    def __init__(self):
        driver, wait = self.init_driver()
        self.driver = driver
        self.wait = wait
        self.db_helper = DatabaseHelper()

    @staticmethod
    def init_driver():
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument('--ignore-ssl-errors=yes')
        chrome_options.add_argument('--ignore-certificate-errors')
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        return driver, wait

    def get_number_reviews(self) -> int:
        sort_reviews = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="submissionDate"]')))
        sort_reviews.click()

        number_reviews = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, '//div[@class="lister"]/div[@class="header"]/div/span'))).text
        number_reviews = number_reviews.split()[0]
        if ',' in number_reviews:
            number_reviews = number_reviews.replace(',', '')

        return int(number_reviews)

    def fetch_reviews_info_list(self, total_reviews: int) -> list:
        if total_reviews > NUM_REVIEWS_PER_LOAD:
            # n_load_more = total_reviews // NUM_REVIEWS_PER_LOAD
            n_load_more = 1

            # Find the "load more" button using a faster locator strategy
            load_more_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#load-more-trigger')))
            for _ in range(n_load_more):
                try:
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                except Exception as e:
                    print('Exception:', e, traceback.format_exc())

        review_list = self.wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//div[@class="lister-item-content"]')))

        review_info_list = self.fetch_reviews_info(review_list)

        return review_info_list

    @staticmethod
    def pre_process_text(text: str) -> str:
        preprocessed_text = re.sub(r'\n+', '\n', text)
        preprocessed_text = re.sub(r'http\S+', '', preprocessed_text)  # removendo links
        preprocessed_text = preprocessed_text.replace('"', '')  # removendo aspas
        preprocessed_text = re.sub(r"<\S* ?/?>", '', preprocessed_text)
        preprocessed_text = re.sub("[-*!,$><:.+?=]", '', preprocessed_text)  # remove outras pontuações
        preprocessed_text = re.sub(r'[.]\s+', '', preprocessed_text)  # removendo reticências 
        preprocessed_text = re.sub(r' ', ' ', preprocessed_text)  # removendo espaços extras
        preprocessed_text = re.sub(r'\'', "''", preprocessed_text)
        return preprocessed_text.lower()

    def insert_review_info(self, reviews_info: list, title_id: str):
        for review_info in reviews_info:
            self.db_helper.insert_review(title_id, review_info)

    def fetch_reviews_info(self, reviews_list: list) -> list:
        reviews_info: list[ReviewInfo] = []
        for review in reviews_list:
            try:
                container_content = review.find_element(By.CLASS_NAME, 'content')
                review_text = container_content.find_element(By.TAG_NAME, 'div').text
                review_text = self.pre_process_text(review_text)
                if review_text == '':
                    continue
            except Exception:
                review_text = None

            try:
                container_span = review.find_element(By.CLASS_NAME, 'rating-other-user-rating')
                span = container_span.find_elements(By.TAG_NAME, 'span')[0]
                review_rating = span.text
            except Exception:
                review_rating = None

            try:
                review_title = review.find_element(By.CLASS_NAME, 'title').text
                review_title = re.sub(r'\'', "''", review_title)
            except Exception:
                review_title = None

            try:
                container_author = review.find_element(By.CLASS_NAME, 'display-name-date')
                review_author = container_author.find_element(By.TAG_NAME, 'a').text
                review_author = re.sub(r'\'', "''", review_author)
            except Exception:
                review_author = None

            try:
                review_date = container_author.find_element(By.CLASS_NAME, 'review-date').text
            except Exception:
                review_date = None

            reviews_info.append(
                ReviewInfo(review_text, review_rating, review_title, review_author, review_date)
            )

        return reviews_info

    def fetch_titles_links(self) -> list:
        try:
            elements = self.wait.until(
                EC.visibility_of_all_elements_located((By.XPATH, '//a[@class="ipc-title-link-wrapper"]')))
            url_list = [element.get_attribute('href') for element in elements]
            title_list = [url for url in url_list if url.startswith('https://www.imdb.com/title/')]
            return title_list
        except Exception as e:
            print(e)
            return []

    def fetch_title_link_list(self, reviews_category_url: str) -> list:
        self.driver.get(reviews_category_url)
        elements = self.wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//a[@class="ipc-title-link-wrapper"]')))
        url_list = [element.get_attribute('href') for element in elements]
        title_link_list = [url for url in url_list if url.startswith('https://www.imdb.com/title/')]
        
        number_titles = len(title_link_list)

        if number_titles == 0:
            raise Exception(f"Could not fetch titles from {reviews_category_url} links correctly")

        return title_link_list[:min(number_titles, TITLES_TO_FETCH)]

    def fetch_imdb_reviews(self, urls_list: list):
        print(f'Fetching {len(urls_list)} titles')
        for url in tqdm(urls_list):
            try:
                review_url = re.sub("(\?[A-Za-z0-9\_=&\\\/-]*)", 'reviews', url)
                self.driver.get(review_url)
                div_parent = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//div[@class="parent"]')))
                title_name = div_parent.find_element(By.TAG_NAME, 'a').text

                total_reviews = self.get_number_reviews()
                reviews_info = self.fetch_reviews_info_list(total_reviews)

                title_id = self.db_helper.query_title(title_name, len(reviews_info))
                self.insert_review_info(reviews_info, title_id)

            except Exception as e:
                print(traceback.format_exc())
                print('Error fetching reviews')

    def scrape_reviews(self):
        try:
            title_links1 = self.fetch_title_link_list('https://www.imdb.com/chart/top/?ref_=nv_mv_250')
            title_links2 = self.fetch_title_link_list('https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250')
        except Exception as e:
            print(e)
            exit()

        self.fetch_imdb_reviews(title_links1)
        self.fetch_imdb_reviews(title_links2)
        self.db_helper.commit_changes()
        self.db_helper.close_connection()
        print("IMDB Reviews successfully retrieved and inserted in DB")


if __name__ == "__main__":
    imdb_scraper = ImdbScraper()
    imdb_scraper.scrape_reviews()
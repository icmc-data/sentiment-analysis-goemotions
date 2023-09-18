import re
import os
import time

from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# from selenium.webdriver.chrome.options import Options as ChromeOptions
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
import traceback
import psycopg2

NUM_REVIEWS_PER_LOAD = 25


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


class DatabaseHelper:
    def __init__(self):
        self.mydb = wait_for_db()
        self.cursor = self.mydb.cursor()

    def insert_review(self, table_suffix, review_rating, review_title, review_author, review_date, review_text,
                      title_id):
        self.cursor.execute(
            f'INSERT INTO IMDB_Reviews_{table_suffix} \
            (review_rating, review_title, review_author, review_date, review_text, id_title) \
            VALUES (%s, %s, %s, %s, %s, %s)', \
            (review_rating, review_title, review_author, review_date, review_text, title_id)
        )

    def query_title(self, title_name, n_reviews, table_suffix):
        title_name = re.sub(r'\'', "''", title_name)
        print(table_suffix, title_name)
        id_title = list(self.cursor.execute(f"SELECT id_title FROM IMDB_{table_suffix} WHERE title='{title_name}'"))
        if len(id_title) == 0:
            result = self.cursor.execute(
                f'INSERT INTO IMDB_{table_suffix} (title, n_reviews) VALUES (%s, %s) RETURNING id_title',
                (title_name, n_reviews))
            id_title = result.fetchone()[0]
        else:
            id_title = id_title[0][0]
        return id_title


class ImdbScraper:
    driver = None
    mydb = None

    def __init__(self):
        driver, wait = init_driver()
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
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument('--ignore-ssl-errors=yes')
        chrome_options.add_argument('--ignore-certificate-errors')
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        return driver, wait

    def get_total_reviews(self):
        sort_reviews = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="submissionDate"]')))
        sort_reviews.click()

        number_reviews = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, '//div[@class="lister"]/div[@class="header"]/div/span'))).text
        number_reviews = number_reviews.split()[0]
        if ',' in number_reviews:
            number_reviews = number_reviews.replace(',', '')
        total_reviews = int(number_reviews)

        return total_reviews

    def load_reviews_list(self, total_reviews):
        if total_reviews > NUM_REVIEWS_PER_LOAD:
            n_load_more = total_reviews // NUM_REVIEWS_PER_LOAD
            n_load_more = 1

            # Find the "load more" button using a faster locator strategy
            load_more_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#load-more-trigger')))
            for _ in range(n_load_more):
                try:
                    # Execute JavaScript to click the "load more" button
                    self.driver.execute_script("arguments[0].click();", load_more_btn)
                except Exception as e:
                    print('Exception:', e, traceback.format_exc())

        review_list = self.wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//div[@class="lister-item-content"]')))
        return review_list

    @staticmethod
    def pre_process_text(text):
        preprocessed_text = re.sub(r'\n+', '\n', text)
        preprocessed_text = re.sub(r'http\S+', '', text)  # removendo links
        preprocessed_text = preprocessed_text.replace('"', '')  # removendo aspas
        preprocessed_text = re.sub(r"<\S*\ ?\/?>", '', preprocessed_text)
        preprocessed_text = re.sub("[-*!,$><:.+?=]", '', preprocessed_text)  # remove outras pontuações

        preprocessed_text = re.sub(r'[.]\s+', '', preprocessed_text)  # removendo reticências 
        preprocessed_text = re.sub(r'  ', ' ', preprocessed_text)  # removendo espaços extras
        preprocessed_text = re.sub(r'\'', "''", preprocessed_text)
        return preprocessed_text.lower()

    def get_review_info_and_insert(self, reviews_list, title_id, table_suffix):
        for review in reviews_list:
            try:
                container_content = review.find_element(By.CLASS_NAME, 'content')
                review_text = container_content.find_element(By.TAG_NAME, 'div').text
                review_text = self.pre_process_text(review_text)
                if review_text == '':
                    continue
            except:
                review_text = None

            try:
                container_span = review.find_element(By.CLASS_NAME, 'rating-other-user-rating')
                span = container_span.find_elements(By.TAG_NAME, 'span')[0]
                review_rating = span.text
            except:
                review_rating = None

            try:
                review_title = review.find_element(By.CLASS_NAME, 'title').text
                review_title = re.sub(r'\'', "''", review_title)
            except:
                review_title = None

            try:
                container_author = review.find_element(By.CLASS_NAME, 'display-name-date')
                review_author = container_author.find_element(By.TAG_NAME, 'a').text
                review_author = re.sub(r'\'', "''", review_author)
            except:
                review_author = None

            try:
                review_date = container_author.find_element(By.CLASS_NAME, 'review-date').text
            except:
                review_date = None

            self.db_helper.insert_review(table_suffix, review_rating, review_title, review_author, review_date,
                                         review_text, title_id)

    def imdb_scrape_reviews(self):
        total_reviews = self.get_total_reviews()
        reviews_list = self.load_reviews_list(total_reviews)
        return reviews_list

    def fetch_title_links(self):
        try:
            elements = self.wait.until(
                EC.visibility_of_all_elements_located((By.XPATH, '//a[@class="ipc-title-link-wrapper"]')))
            url_list = [element.get_attribute('href') for element in elements]
            title_list = [url for url in url_list if url.startswith('https://www.imdb.com/title/')]
            print(f'Title list: {len(title_list)}')
            return title_list
        except Exception as e:
            print(e)
            return []

    def imdb_fetch_links(self):
        self.driver.get('https://www.imdb.com/chart/top/?ref_=nv_mv_250')
        movies_links = self.fetch_title_links()
        self.driver.get('https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250')
        series_links = self.fetch_title_links()

        if len(movies_links) == 0 or len(series_links) == 0:
            raise Exception("Could not fetch movies and series links correctly")

        print(f'Fetched {len(movies_links)} links for movie titles and {len(series_links)} links for series titles')
        return movies_links, series_links

    def imdb_scrape(self, urls_list, table_suffix):
        for url in tqdm(urls_list):
            try:
                review_url = re.sub("(\?[A-Za-z0-9\_=&\\\/-]*)", 'reviews', url)
                print(f'Going to reviews page: {review_url}')
                self.driver.get(review_url)
                div_parent = self.wait.until(EC.visibility_of_element_located((By.XPATH, '//div[@class="parent"]')))

                title_name = div_parent.find_element(By.TAG_NAME, 'a').text

                print(f'Retrieving reviews for {table_suffix[:-1].lower()}: {title_name}')
                reviews = self.imdb_scrape_reviews()
                title_id = self.db_helper.query_title(title_name, len(reviews), table_suffix)
                self.get_review_info_and_insert(reviews, title_id, table_suffix)
            except Exception as e:
                print(traceback.format_exc())
                print('Error fetching reviews')
            break

    def scrape_reviews(self):
        try:
            movies_links, series_links = self.imdb_fetch_links()
        except Exception as e:
            print(e)
            exit()

        self.imdb_scrape(movies_links, table_suffix='Movies')
        self.imdb_scrape(series_links, table_suffix='Series')


if __name__ == "__main__":
    imdb_scraper = ImdbScraper()
    imdb_scraper.scrape_reviews()

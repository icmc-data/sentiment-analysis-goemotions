import re
import os 
import time

import mysql.connector

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

NUM_REVIEWS_PER_LOAD = 25

# Função para aguardar o banco de dados estar pronto
def wait_for_db():
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        try:
            # Tenta conectar ao banco de dados
            mydb = mysql.connector.connect(
                host=os.environ.get('MYSQL_HOST'),
                user=os.environ.get('MYSQL_USER'),
                password=os.environ.get('MYSQL_ROOT_PASSWORD'),
                database=os.environ.get('MYSQL_DATABASE')
            )
            mydb.close()
            break  # Conexão bem-sucedida, sai do loop
        except mysql.connector.Error as err:
            print(f"Erro ao conectar ao banco de dados: {err}")
            attempts += 1
            time.sleep(5)  # Aguarda 5 segundos antes de tentar novamente
    else:
        # Caso atinja o limite de tentativas, exibe uma mensagem de erro
        print("Não foi possível conectar ao banco de dados após várias tentativas.")

wait_for_db()

mydb = mysql.connector.connect(
    host=os.environ.get('MYSQL_HOST'),
    user=os.environ.get('MYSQL_USER'),
    password=os.environ.get('MYSQL_ROOT_PASSWORD'),
    database=os.environ.get('MYSQL_DATABASE')
)
cursor = mydb.cursor()

def get_total_reviews(driver, wait):
    sort_reviews = wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="submissionDate"]')))
    sort_reviews.click()

    number_reviews = driver.find_element(By.XPATH, '//div[@class="lister"]/div[@class="header"]/div/span').text
    number_reviews = number_reviews.split()[0]
    if ',' in number_reviews:
        number_reviews = number_reviews.replace(',', '')
    total_reviews = int(number_reviews)

    return total_reviews

def load_reviews_list(driver, wait, total_reviews):
    if total_reviews > NUM_REVIEWS_PER_LOAD:
        n_load_more = total_reviews // NUM_REVIEWS_PER_LOAD

        # Adjust the wait time dynamically
        wait_time = 5
        if n_load_more > 5:
            wait_time = 2
        if n_load_more > 10:
            wait_time = 1

        # Set implicit wait on the driver
        driver.implicitly_wait(wait_time)

        # Find the "load more" button using a faster locator strategy
        load_more_btn = driver.find_element(By.CSS_SELECTOR, 'button#load-more-trigger')
        
        n_load_more = 5
        for i in range(n_load_more):
            print(i)
            try:
                # Execute JavaScript to click the "load more" button
                driver.execute_script("arguments[0].click();", load_more_btn)
            except Exception as e:
                print('Exception:', e)

    # Reset the implicit wait to the default value
    driver.implicitly_wait(5)

    review_list = driver.find_elements(By.XPATH, '//div[@class="lister-item-content"]')
    return review_list

def pre_process_text(text):
    preprocessed_text = re.sub(r'\n+', '\n', text)
    # preprocessed_text = re.sub(r'http\S+', '', text) # removendo links
    # preprocessed_text = preprocessed_text.replace('"', '')    # removendo aspas
    preprocessed_text = re.sub("[-*!,$><:.+?=]", '', preprocessed_text) # remove outras pontuações

    # preprocessed_text = re.sub(r'[.]\s+', '', preprocessed_text)  # removendo reticências 
    preprocessed_text = re.sub(r'  ', ' ', preprocessed_text) # removendo espaços extras
    
    return preprocessed_text.lower()

def insert_reviews(reviews_list, imdb_title, table_suffix):
    for review in reviews_list:
        try:
            container_span = review.find_element(By.CLASS_NAME, 'rating-other-user-rating')
            span = container_span.find_elements(By.TAG_NAME, 'span')[0]
            review_rating = span.text
        except:
            review_rating = None

        try:
            review_title = review.find_element(By.CLASS_NAME, 'title').text
        except:
            review_title = None
        
        try:
            container_author = review.find_element(By.CLASS_NAME, 'display-name-date')
            review_author = container_author.find_element(By.TAG_NAME, 'a').text
        except:
            review_author = None
        
        try:
            review_date = container_author.find_element(By.CLASS_NAME, 'review-date').text
        except:
            review_date = None
        
        try:
            container_content = review.find_element(By.CLASS_NAME, 'content')
            review_text = container_content.find_element(By.TAG_NAME, 'div').text
            review_text = pre_process_text(review_text)
        except:
            review_text = None

        # write on sql bank
        cursor.execute(f'INSERT INTO IMDB_Reviews_{table_suffix} (review_rating, review_title, review_author, review_date, review_text, title) VALUES (%s, %s, %s, %s, %s, %s)', (review_rating, review_title, review_author, review_date, review_text, imdb_title))

    mydb.commit()

def imdb_scrape_reviews(driver, wait):
    total_reviews = get_total_reviews(driver, wait)
    reviews_list = load_reviews_list(driver, wait, total_reviews)
    return reviews_list

def imdb_scrape(driver, wait, urls_list, table_suffix):
    for url in urls_list:
        try:
            reviews_url = re.sub("(\?[A-Za-z0-9\_=&\\\/-]*)", 'reviews', url)
            print(f'Going to reviews page: {reviews_url}')
            driver.get(reviews_url)
            div_parent = driver.find_element(By.XPATH, '//div[@class="parent"]')
            title_name = div_parent.find_element(By.TAG_NAME, 'a').text
            reviews = imdb_scrape_reviews(driver, wait)
            insert_reviews(reviews, title_name, table_suffix)
        except Exception as e:
            print(e)
            print('Error fetching reviews')

def fetch_title_links(driver):
    try:
        td_elements = driver.find_elements(By.XPATH, '//td[@class="titleColumn"]')
        title_list = [td.find_element(By.TAG_NAME, 'a').get_attribute('href') for td in td_elements]
        print(f'Title list: {len(title_list)}')
        return title_list
    except:
        return []
    
def imdb_fetch_links(driver):
    driver.get('https://www.imdb.com/chart/top/?ref_=nv_mv_250')
    movies_links = fetch_title_links(driver)
    if movies_links == []:
        print('Error fetching 250 top movies')
        return

    driver.get('https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250')
    series_links = fetch_title_links(driver)
    if series_links == []:
        print('Error fetching 250 top series')
        return 
    print(f'Fetched {len(movies_links)} links for movie titles and {len(series_links)} links for series titles')
    return movies_links, series_links

def init_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
    driver = webdriver.Chrome(options=chrome_options)

    wait = WebDriverWait(driver, 5)
    return driver, wait

driver, wait = init_driver()

links = imdb_fetch_links(driver)

if links is None:
    print('Exiting')
    exit()

movies_links, series_links = links
movies_links = ['https://www.imdb.com/title/tt9362722/?a']
movie_reviews = imdb_scrape(driver, wait, movies_links, table_suffix='Movies')
# series_reviews = imdb_scrape(driver, wait, series_links, table_suffix='Series')

cursor.close()
mydb.close()
driver.close()
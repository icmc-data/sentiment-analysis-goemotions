import re
import os 
import time

from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

NUM_REVIEWS_PER_LOAD = 25

def get_total_reviews(wait):
    sort_reviews = wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="submissionDate"]')))
    sort_reviews.click()

    number_reviews = wait.until(EC.visibility_of_element_located((By.XPATH, '//div[@class="lister"]/div[@class="header"]/div/span'))).text
    number_reviews = number_reviews.split()[0]
    if ',' in number_reviews:
        number_reviews = number_reviews.replace(',', '')
    total_reviews = int(number_reviews)

    return total_reviews

# def load_reviews_list(driver, wait, total_reviews):
#     if total_reviews > NUM_REVIEWS_PER_LOAD:
#         n_load_more = total_reviews // NUM_REVIEWS_PER_LOAD

#         # Adjust the wait time dynamically
#         wait_time = 5
#         if n_load_more > 5:
#             wait_time = 2
#         if n_load_more > 10:
#             wait_time = 1

#         # Set implicit wait on the driver
#         driver.implicitly_wait(wait_time)

#         # Find the "load more" button using a faster locator strategy
#         load_more_btn = driver.find_element(By.CSS_SELECTOR, 'button#load-more-trigger')
#         for i in range(n_load_more):
#             try:
#                 # Execute JavaScript to click the "load more" button
#                 driver.execute_script("arguments[0].click();", load_more_btn)
#             except Exception as e:
#                 print('Exception:', e)

#     # Reset the implicit wait to the default value
#     driver.implicitly_wait(5)

#     review_list = driver.find_elements(By.XPATH, '//div[@class="lister-item-content"]')
#     return review_list

def load_reviews_list(driver, wait, total_reviews):
    if total_reviews > NUM_REVIEWS_PER_LOAD:
        n_load_more = total_reviews // NUM_REVIEWS_PER_LOAD

        # Find the "load more" button using a faster locator strategy
        load_more_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#load-more-trigger')))
        for _ in range(n_load_more):
            try:
                # Execute JavaScript to click the "load more" button
                driver.execute_script("arguments[0].click();", load_more_btn)
            except Exception as e:
                print('Exception:', e)

    review_list = wait.until(EC.visibility_of_all_elements_located((By.XPATH, '//div[@class="lister-item-content"]')))
    return review_list

def pre_process_text(text):
    preprocessed_text = re.sub(r'\n+', '\n', text)
    preprocessed_text = re.sub(r'http\S+', '', text) # removendo links
    preprocessed_text = preprocessed_text.replace('"', '')    # removendo aspas
    preprocessed_text = re.sub(r"<\S*\ ?\/?>", '', preprocessed_text)
    preprocessed_text = re.sub("[-*!,$><:.+?=]", '', preprocessed_text) # remove outras pontuações

    preprocessed_text = re.sub(r'[.]\s+', '', preprocessed_text)  # removendo reticências 
    preprocessed_text = re.sub(r'  ', ' ', preprocessed_text) # removendo espaços extras
    preprocessed_text = re.sub(r'\'', "''", preprocessed_text)
    return preprocessed_text.lower()

def insert_reviews(mydb, reviews_list, title_id, table_suffix):
    for review in reviews_list:
        try:
            container_content = review.find_element(By.CLASS_NAME, 'content')
            review_text = container_content.find_element(By.TAG_NAME, 'div').text
            review_text = pre_process_text(review_text)
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

        # write on sql bank
        mydb.execute(f'INSERT INTO IMDB_Reviews_{table_suffix} (review_rating, review_title, review_author, review_date, review_text, id_title) VALUES (%s, %s, %s, %s, %s, %s)', (review_rating, review_title, review_author, review_date, review_text, title_id))
        
def imdb_scrape_reviews(driver, wait):
    total_reviews = get_total_reviews(wait)
    reviews_list = load_reviews_list(driver, wait, total_reviews)
    return reviews_list

def query_title(mydb, title_name, n_reviews, table_suffix):
    title_name = re.sub(r'\'', "''", title_name)
    id = list(mydb.execute(f"SELECT id_title FROM IMDB_{table_suffix} WHERE title='{title_name}'"))
    if len(id) == 0:
        result = mydb.execute(f'INSERT INTO IMDB_{table_suffix} (title, n_reviews) VALUES (%s, %s) RETURNING id_title', (title_name, n_reviews))
        id = result.fetchone()[0]
    else:
        id = id[0][0]
    return id


def imdb_scrape(mydb, driver, wait, urls_list, table_suffix):
    for url in tqdm(urls_list):
        try:
            reviews_url = re.sub("(\?[A-Za-z0-9\_=&\\\/-]*)", 'reviews', url)
            print(f'Going to reviews page: {reviews_url}')
            driver.get(reviews_url)
            div_parent = wait.until(EC.visibility_of_element_located((By.XPATH, '//div[@class="parent"]')))
            # div_parent = driver.find_element(By.XPATH, '//div[@class="parent"]')
            
            title_name = div_parent.find_element(By.TAG_NAME, 'a').text
            
            print(f'Retrieving reviews for {table_suffix[:-1].lower()}: {title_name}')
            reviews = imdb_scrape_reviews(driver, wait)
            id = query_title(mydb, title_name, len(reviews), table_suffix)
            insert_reviews(mydb, reviews, id, table_suffix)
        except Exception as e:
            print(e)
            print('Error fetching reviews')
        break

def fetch_title_links(wait):
    try:
        td_elements = wait.until(EC.visibility_of_all_elements_located((By.XPATH, '//td[@class="titleColumn"]')))
        title_list = [td.find_element(By.TAG_NAME, 'a').get_attribute('href') for td in td_elements]
        print(f'Title list: {len(title_list)}')
        return title_list
    except Exception as e:
        print(e)
        return []
    
def imdb_fetch_links(driver, wait):
    driver.get('https://www.imdb.com/chart/top/?ref_=nv_mv_250')
    movies_links = fetch_title_links(wait)
    if movies_links == []:
        print('Error fetching 250 top movies')
        return

    driver.get('https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250')
    series_links = fetch_title_links(wait)
    if series_links == []:
        print('Error fetching 250 top series')
        return 
    print(f'Fetched {len(movies_links)} links for movie titles and {len(series_links)} links for series titles')
    return movies_links, series_links

def init_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    
    # driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
    driver = webdriver.Chrome(options=chrome_options)

    wait = WebDriverWait(driver, 10)
    return driver, wait

def scrape_reviews(mydb):
    driver, wait = init_driver()
    links = imdb_fetch_links(driver, wait)
    
    if links is None:
        print('Exiting')
        exit()

    movies_links, series_links = links
    
    imdb_scrape(mydb, driver, wait, movies_links, table_suffix='Movies')
    imdb_scrape(mydb, driver, wait, series_links, table_suffix='Series')
import re
import time

import pandas as pd
from urllib.parse import urlencode, quote

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = 'https://www.imdb.com/find/?'
query = 'O poderoso chefão'
n_reviews_query = 100

NUM_REVIEWS_PER_LOAD = 25

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("--headless=new")
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--ignore-certificate-errors')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)
action = ActionChains(driver)

driver.get(url + urlencode({'q': query}, quote_via=quote))

div_list = wait.until(EC.presence_of_element_located((By.XPATH, '//ul[@class="ipc-metadata-list ipc-metadata-list--dividers-after sc-17bafbdb-3 gAWnDM ipc-metadata-list--base"]')))
first_link = div_list.find_element(By.CSS_SELECTOR, ".ipc-metadata-list-summary-item a")
link_url = first_link.get_attribute("href")
print(f"Film/series URL: {link_url}")
reviews_url = re.sub("(\?[A-Za-z0-9\_=]*)", 'reviews', link_url)
print(f"Film/series reviews URL: {reviews_url}")

driver.get(reviews_url)

sort_reviews = wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="submissionDate"]')))
sort_reviews.click()

number_reviews = driver.find_element(By.XPATH, '//div[@class="lister"]/div[@class="header"]/div/span').text
number_reviews = number_reviews.split()[0]
if ',' in number_reviews:
    number_reviews = number_reviews.replace(',', '')
number_reviews = float(number_reviews)

print(number_reviews)

if number_reviews >= n_reviews_query and n_reviews_query > NUM_REVIEWS_PER_LOAD:
    n_load_more = n_reviews_query // NUM_REVIEWS_PER_LOAD

    for _ in range(n_load_more):
        try:
            load_more_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="load-more-trigger"]')))
            time.sleep(1)
            load_more_btn.click()
        except Exception as e:
            print('Exepction: ' + e)

review_list = driver.find_elements(By.XPATH, '//div[@class="lister-item-content"]')[:n_reviews_query]
print(len(review_list))

def pre_process_text(text):
    preprocessed_text = re.sub(r'\n+', '\n', text)
    preprocessed_text = re.sub(r'http\S+', '', text) # removendo links
    preprocessed_text = preprocessed_text.replace('"', '')    # removendo aspas
    preprocessed_text = re.sub("[-*!,$><:.+?=]", '', preprocessed_text) # remove outras pontuações

    preprocessed_text = re.sub(r'[.]\s+', '', preprocessed_text)  # removendo reticências 
    preprocessed_text = re.sub(r'  ', ' ', preprocessed_text) # removendo espaços extras
    
    return preprocessed_text.lower()

df = {'review_rating': [], 'review_title': [], 'review_author': [], 'review_date': [], 'review_text': [], 'title': []}
i = 0
for review in review_list:
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
    
    print(review_author, review_title)
    try:
        review_date = container_author.find_element(By.CLASS_NAME, 'review-date').text
    except:
        review_date = None
    
    try:
        container_content = review.find_element(By.CLASS_NAME, 'content')
        review_text = container_content.find_element(By.TAG_NAME, 'div').text
    except:
        review_text = None

    df['review_rating'].append(review_rating)
    df['review_title'].append(review_title)
    df['review_author'].append(review_author)
    df['review_text'].append(review_text)
    df['review_date'].append(review_date)

driver.quit()

df['title'] = query
dataframe = pd.DataFrame(df)

file_ref = "_".join(query.lower().split(' '))
dataframe.to_csv(f'user_reviews_{file_ref}.csv', sep='|')
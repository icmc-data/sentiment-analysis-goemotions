###### SQL test
import mysql.connector
import random
import string
import os

# Connect to MySQL server
# Create a connection
cnx = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="dentola123",
    database="review_db"
)

# Create a new database
cursor = cnx.cursor()

cursor.execute("SELECT * FROM IMDB_Reviews_Movies_Predictions")
results = cursor.fetchall()
print(results)
cursor.close()
cnx.close()

###### Driver and scrapping test
# import re
# import os 
# import time

# from urllib.parse import urlencode, quote

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


# def init_driver():
#     chrome_options = webdriver.ChromeOptions()
#     # chrome_options.add_argument('--headless')
#     chrome_options.add_argument('--no-sandbox')
#     chrome_options.add_argument('--disable-dev-shm-usage')
#     chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

#     # driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
#     driver = webdriver.Chrome(options=chrome_options)

#     wait = WebDriverWait(driver, 5)
#     return driver, wait

# driver, wait = init_driver()

# def imdb_scrape(driver, wait, urls_list):
#     imdb_reviews = []
#     for url in urls_list:
#         try:
#             print(f'{url=}')
#             reviews_url = re.sub("(\?[A-Za-z0-9\_=&\\\/-]*)", 'reviews', url)
#             print(f'{reviews_url=}')
#             driver.get(reviews_url)
#             div_parent = driver.find_element(By.XPATH, '//div[@class="parent"]')
#             title_name = div_parent.find_element(By.TAG_NAME, 'a').text
#             # imdb_reviews.append((imdb_scrape_reviews(driver, wait), title_name))
#             # print(title_name)
#             print(title_name)
#             break
#         except:
#             print('Error fetching reviews')
#     return imdb_reviews

# def imdb_list(driver, wait):
#     driver.get('https://www.imdb.com/chart/top/?ref_=nv_mv_250')
#     td_elements = driver.find_elements(By.XPATH, '//td[@class="titleColumn"]')
#     movie_list = [td.find_element(By.TAG_NAME, 'a').get_attribute('href') for td in td_elements]
#     return movie_list
    
# # movie_list = imdb_get_movie_list(driver, wait)
# movie_list = imdb_list(driver, wait)
# imdb_scrape(driver, wait, movie_list)

# driver.close()
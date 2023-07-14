import os
import time

import inference
import scraping

from sqlalchemy import create_engine, exc
from sqlalchemy.exc import IntegrityError, InternalError

# DB_NAME = os.environ.get("POSTGRES_NAME")
# DB_USER = os.environ.get("POSTGRES_USER")
# DB_PASS = os.environ.get("POSTGRES_PASSWORD")
# DB_HOST = os.environ.get("POSTGRES_HOST")
# DB_PORT = os.environ.get("POSTGRES_PORT")

DB_NAME = "imdb_reviews"
DB_USER = "postgres"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"

# Função para aguardar o banco de dados estar pronto
def wait_for_db():
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        try:
            db_string = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)
            db = create_engine(db_string)
            break  # Conexão bem-sucedida, sai do loop
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            attempts += 1
            time.sleep(5)  # Aguarda 5 segundos antes de tentar novamente
    else:
        # Caso atinja o limite de tentativas, exibe uma mensagem de erro
        print("Não foi possível conectar ao banco de dados após várias tentativas.")

wait_for_db()

db_string = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)
db = create_engine(db_string)

# Scrapa os dados do imdb
scraping.scrape_reviews(db)
# Faz a inferências nos dados da base
# inference.predict_reviews(db)
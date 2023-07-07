import os
import time
import mysql.connector

import inference
import scraping

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
            time.sleep(10)  # Aguarda 5 segundos antes de tentar novamente
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

mydb = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="dentola123",
    database="review_db"
)

cursor = mydb.cursor()

def predict_reviews():
    predictions_results = inference.predict_database(cursor)

    for id, predict in predictions_results.items():
        print('INSERT INTO IMDB_Reviews_Movies_Predictions (id, class_1, class_2) VALUES (%s, %s, %s)', (id, float(predict[0]), float(predict[1])))
        cursor.execute('INSERT INTO IMDB_Reviews_Movies_Predictions (id, class_1, class_2) VALUES (%s, %s, %s)', (id, float(predict[0]), float(predict[1])))
    mydb.commit()
    print(predictions_results)

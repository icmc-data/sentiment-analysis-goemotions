import re
import os 
import time

import mysql.connector

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from transformers import BertForSequenceClassification

MAX_LENGTH  = 512

# # Função para aguardar o banco de dados estar pronto
# def wait_for_db():
#     max_attempts = 10
#     attempts = 0
#     while attempts < max_attempts:
#         try:
#             # Tenta conectar ao banco de dados
#             mydb = mysql.connector.connect(
#                 host=os.environ.get('MYSQL_HOST'),
#                 user=os.environ.get('MYSQL_USER'),
#                 password=os.environ.get('MYSQL_ROOT_PASSWORD'),
#                 database=os.environ.get('MYSQL_DATABASE')
#             )
#             mydb.close()
#             break  # Conexão bem-sucedida, sai do loop
#         except mysql.connector.Error as err:
#             print(f"Erro ao conectar ao banco de dados: {err}")
#             attempts += 1
#             time.sleep(10)  # Aguarda 5 segundos antes de tentar novamente
#     else:
#         # Caso atinja o limite de tentativas, exibe uma mensagem de erro
#         print("Não foi possível conectar ao banco de dados após várias tentativas.")

# wait_for_db()

# mydb = mysql.connector.connect(
#     host=os.environ.get('MYSQL_HOST'),
#     user=os.environ.get('MYSQL_USER'),
#     password=os.environ.get('MYSQL_ROOT_PASSWORD'),
#     database=os.environ.get('MYSQL_DATABASE')
# )

mydb = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="dentola123",
    database="review_db"
)

cursor = mydb.cursor()

def pre_process_text(text):
    preprocessed_text = re.sub(r'http\S+', '', text) # removendo links
    preprocessed_text = preprocessed_text.replace('"', '')    # removendo aspas
    preprocessed_text = re.sub(r"<\S*\ ?\/?>", '', preprocessed_text)
    preprocessed_text = re.sub("[-*!,$><:.+?=]", '', preprocessed_text) # remove outras pontuações

    preprocessed_text = re.sub(r'[.]\s+', '', preprocessed_text)  # removendo reticências 
    preprocessed_text = re.sub(r'  ', ' ', preprocessed_text) # removendo espaços extras
    
    return preprocessed_text.lower()

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print(f'Device set to: {device}')

base = 'bert-base-uncased'
model = BertForSequenceClassification.from_pretrained(base, num_labels=2, output_attentions=False, output_hidden_states=False)

state_dict = torch.load('./../model_weights.pth')
model.load_state_dict(state_dict, strict=False)

model = model.to(device)

def get_ids_unpredicted(table_suffix):
    cursor.execute(f'SELECT R.id, R.review_text FROM IMDB_Reviews_{table_suffix} as R LEFT JOIN IMDB_Reviews_{table_suffix}_Predictions as P ON R.id=P.id_review WHERE P.classification IS NULL')
    unpredicted = cursor.fetchall()
    return unpredicted

class UnlabeledDataset(Dataset):
    def __init__(self, reviews, base):
        self.reviews = reviews
        self.tokenizer = AutoTokenizer.from_pretrained(base)
    
    def __len__(self):
        return len(self.reviews)

    def __getitem__(self, idx):
        review = self.reviews[idx][1]
        index  = self.reviews[idx][0]

        review = pre_process_text(review)

        encoded_inputs = self.tokenizer.enconde_plus(
            review,
            padding=True,
            truncation=True,
            return_tensors='pt',
            max_length=MAX_LENGTH
        )
        
        inputs = {k: v.squeeze(0) for k,v in encoded_inputs.items()}
        return index, inputs

get_ids_unpredicted('Movies')
cursor.close()
mydb.close()
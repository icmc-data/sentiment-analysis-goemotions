import re
import os 
import time

import mysql.connector

from tqdm import tqdm 

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

def get_ids_unpredicted(table_suffix):
    cursor.execute(f'SELECT R.id, R.review_text FROM IMDB_Reviews_{table_suffix} as R LEFT JOIN IMDB_Reviews_{table_suffix}_Predictions as P ON R.id=P.id WHERE P.class_1 IS NULL')
    unpredicted = cursor.fetchall()
    return unpredicted

class UnlabeledDataset(Dataset):
    def __init__(self, ids, reviews):
        self.reviews = reviews
        self.ids = ids

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, idx):
        id = self.ids[idx]
        attention_mask = self.reviews['attention_mask'][idx].squeeze(0)
        input_ids = self.reviews['input_ids'][idx].squeeze(0)
        return id, input_ids, attention_mask

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print(f'Device set to: {device}')

base = 'bert-base-uncased'
model = BertForSequenceClassification.from_pretrained(base, num_labels=2, output_attentions=False, output_hidden_states=False)

# state_dict = torch.load('./../model_weights.pth')
# model.load_state_dict(state_dict, strict=False)

model = model.to(device)
model.eval()

movie_lists = get_ids_unpredicted('Movies')

reviews = [str(pre_process_text(text)) for _, text in movie_lists]
ids = [int(id) for id, _ in movie_lists]

tokenizer = AutoTokenizer.from_pretrained(base)

encoded_inputs = tokenizer(
            reviews,
            padding=True,
            truncation=True,
            return_tensors='pt',
            max_length=MAX_LENGTH
)

dataset = UnlabeledDataset(ids, encoded_inputs)

dataloader = DataLoader(dataset, batch_size=8)

bar = tqdm(total=len(dataloader), desc=f"Inferece on imdb-dataset", unit="steps", position=0, leave=False)

predictions_results = {}
model.eval()

for i, batch in enumerate(dataloader):
    ids, input_ids, attention_mask = batch
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        for id, logit in zip(ids, logits):
            predictions_results[id.item()] = logit.numpy()
    bar.update(1)

for id, predict in predictions_results.items():
    print('INSERT INTO IMDB_Reviews_Movies_Predictions (id, class_1, class_2) VALUES (%s, %s, %s)', (id, float(predict[0]), float(predict[1])))
    cursor.execute('INSERT INTO IMDB_Reviews_Movies_Predictions (id, class_1, class_2) VALUES (%s, %s, %s)', (id, float(predict[0]), float(predict[1])))
mydb.commit()

print(predictions_results)
cursor.close()
mydb.close()
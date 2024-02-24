import re
import os 
import time
import traceback
import psycopg2
import torch
from tqdm import tqdm 
from dataclasses import dataclass
from scipy.special import softmax
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, DistilBertTokenizer
from transformers import BertForSequenceClassification
from transformers import AdamW, get_linear_schedule_with_warmup, AutoModelForSequenceClassification

MAX_LENGTH  = 512

go_emotions_labels = [
    'admiration', 
    'amusement',
    'anger',
    'annoyance',
    'approval',
    'caring',
    'confusion',
    'curiosity',
    'desire',
    'disappointment',
    'disapproval',
    'disgust',
    'embarrassment',
    'excitement',
    'fear',
    'gratitude',
    'grief',
    'joy',
    'love',
    'nervousness',
    'optimism',
    'pride',
    'realization',
    'relief',
    'remorse',
    'sadness',
    'surprise',
    'neutral'
]


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
            (review_rating, review_title, review_author, review_date, review_text, id_title) \
            VALUES (%s, %s, %s, %s, %s, %s)',
            (review.rating, review.title, review.author, review.date, review.text, title_id)
        )

    def query_title(self, title_name, n_reviews) -> str:
        title_name = re.sub(r'\'', "''", title_name)
        self.cursor.execute(f"SELECT id_title FROM IMDB_Titles WHERE title='{title_name}'")
        id_title = self.cursor.fetchone()
        if id_title is None:
            self.cursor.execute(
                f'INSERT INTO IMDB_Titles (title, n_reviews) VALUES (%s, %s) RETURNING id_title',
                (title_name, n_reviews))
            id_title = self.cursor.fetchone()[0]
        else:
            id_title = id_title
        return id_title

    def commit_changes(self):
        self.mydb.commit()

    def close_connection(self):
        self.cursor.close()
        self.mydb.close()
        print("Close DB connection")

    def get_ids_unpredicted(self) -> list:
        self.cursor.execute(
            f'SELECT R.review_id, R.review_title, R.review_text FROM IMDB_Reviews \
            as R LEFT JOIN IMDB_Reviews_Predictions as P ON \
            R.review_id=P.review_id'
        )
        return list(self.cursor.fetchall())

    def insert_predictions(self, id, review_predict, title_predict):
        for i in range(len(review_predict)):
            self.cursor.execute(
                f'INSERT INTO IMDB_Reviews_Predictions \
                (review_id, emotion, review_value, title_value) VALUES (%s, %s, %s, %s)', 
                (id, go_emotions_labels[i], float(review_predict[i]),float(title_predict[i]))
            )


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

class ImdbPredict:
    def __init__(self):
        self.db_helper = DatabaseHelper()

    @staticmethod
    def load_model(device, base):
        model = AutoModelForSequenceClassification.from_pretrained(base, num_labels=28)

        model.load_state_dict(torch.load('best_model.pt', map_location=torch.device('cpu')))

        model.eval()

        return model

    def load_reviews(self):
        movie_lists = self.db_helper.get_ids_unpredicted()
        print(len(movie_lists))

        ids, titles, reviews = zip(*movie_lists)
        ids = list(ids)
        reviews = list(reviews)
        titles = list(titles)

        return ids, reviews, titles

    @staticmethod
    def tokenize_reviews(reviews, base):
        tokenizer = AutoTokenizer.from_pretrained(base)
        
        encoded_inputs = tokenizer(
            reviews,
            padding=True,
            truncation=True,
            return_tensors='pt',
            max_length=MAX_LENGTH
        )

        return encoded_inputs

    @staticmethod
    def get_dataloader(ids, encoded_inputs, batch_size=8):
        dataset = UnlabeledDataset(ids, encoded_inputs)
        return DataLoader(dataset, batch_size=1)

    @staticmethod
    def inference_loop(device, model, encoded_inputs):
        bar = tqdm(
            total=len(encoded_inputs), 
            desc=f"Inferece on imdb-dataset", 
            unit="steps", position=0, leave=False
        )
        
        predictions_results = {}
        for batch in iter(encoded_inputs):
            ids, input_ids, attention_mask = batch
            with torch.no_grad():
                outputs = model(
                    input_ids=input_ids.to(device), 
                    attention_mask=attention_mask.to(device))
                logits = outputs.logits
                for id, logit in zip(ids, logits):
                    predictions_results[id.item()] = logit.cpu().numpy()
            bar.update(1)

        return predictions_results

    def predict_database(self):
        base = 'distilbert-base-uncased'

        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        print(f'Device set to: {device}')

        model = self.load_model(device, base)

        ids, reviews, titles = self.load_reviews()

        print(ids, reviews, titles)
        review_encoded_inputs = self.tokenize_reviews(reviews, base)
        title_encoded_inputs = self.tokenize_reviews(titles, base)

        print(review_encoded_inputs)
        review_dataloader = self.get_dataloader(ids, review_encoded_inputs)
        title_dataloader = self.get_dataloader(ids, title_encoded_inputs)
        
        review_predictions_results = self.inference_loop(device, model, review_dataloader)

        title_predictions_results =  self.inference_loop(device, model, title_dataloader)

        return review_predictions_results, title_predictions_results

    def predict_reviews(self):
        review_predictions_results, title_predictions_results = self.predict_database()
        
        for id, predict in review_predictions_results.items():
            predict = softmax(predict)
            title = title_predictions_results.get(id)
            title = softmax(title)
            self.db_helper.insert_predictions(id, predict, title)

        
if __name__ == "__main__":

    imdb_predict = ImdbPredict()
    imdb_predict.predict_reviews()
    imdb_predict.db_helper.commit_changes()
    imdb_predict.db_helper.close_connection()

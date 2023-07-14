import re
import os 
import time

from tqdm import tqdm 

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from transformers import BertForSequenceClassification

MAX_LENGTH  = 512

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

def get_ids_unpredicted(mydb, table_suffix):
    return list(mydb.execute(f'SELECT R.id, R.review_text FROM IMDB_Reviews_{table_suffix} as R LEFT JOIN IMDB_Reviews_{table_suffix}_Predictions as P ON R.id=P.id WHERE P.class_1 IS NULL'))

def load_model(device, base):
    model = BertForSequenceClassification.from_pretrained(base, num_labels=2, output_attentions=False, output_hidden_states=False)

    # state_dict = torch.load('./../model_weights.pth')
    # model.load_state_dict(state_dict, strict=False)

    model = model.to(device)
    model.eval()

    return model

def load_reviews(mydb, table_suffix):
    movie_lists = get_ids_unpredicted(mydb, 'Movies')
    print(len(movie_lists))

    reviews = [text for _, text in movie_lists]
    ids = [int(id) for id, _ in movie_lists]

    return ids, reviews

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

def get_dataloader(ids, encoded_inputs, batch_size=8):
    dataset = UnlabeledDataset(ids, encoded_inputs)
    return DataLoader(dataset, batch_size=batch_size)

def inference_loop(device, model, dataloader):
    bar = tqdm(total=len(dataloader), desc=f"Inferece on imdb-dataset", unit="steps", position=0, leave=False)
    
    predictions_results = {}
    for i, batch in enumerate(dataloader):
        ids, input_ids, attention_mask = batch
        with torch.no_grad():
            outputs = model(input_ids=input_ids.to(device), attention_mask=attention_mask.to(device))
            logits = outputs.logits
            for id, logit in zip(ids, logits):
                predictions_results[id.item()] = logit.cpu().numpy()
        bar.update(1)

    return predictions_results

def predict_database(mydb, table_suffix):
    base = 'bert-base-uncased'

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(f'Device set to: {device}')

    model = load_model(device, base)

    ids, reviews = load_reviews(mydb, table_suffix)

    encoded_inputs = tokenize_reviews(reviews, base)
    
    dataloader = get_dataloader(ids, encoded_inputs, batch_size=8)
    
    predictions_results = inference_loop(device, model, dataloader)

    return predictions_results

def predict_reviews(mydb):
    predictions_results = predict_database(mydb)
    print(predictions_results)
    
    for id, predict in predictions_results.items():
        print('INSERT INTO IMDB_Reviews_Movies_Predictions (id, class_1, class_2) VALUES (%s, %s, %s)', (id, float(predict[0]), float(predict[1])))
        mydb.execute('INSERT INTO IMDB_Reviews_Movies_Predictions (id, class_1, class_2) VALUES (%s, %s, %s)', (id, float(predict[0]), float(predict[1])))
    
    print(predictions_results)
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

def get_ids_unpredicted(cursor, table_suffix):
    cursor.execute(f'SELECT R.id, R.review_text FROM IMDB_Reviews_{table_suffix} as R LEFT JOIN IMDB_Reviews_{table_suffix}_Predictions as P ON R.id=P.id WHERE P.class_1 IS NULL')
    unpredicted = cursor.fetchall()
    return unpredicted

def predict_database(cursor):
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(f'Device set to: {device}')

    base = 'bert-base-uncased'
    model = BertForSequenceClassification.from_pretrained(base, num_labels=2, output_attentions=False, output_hidden_states=False)

    # state_dict = torch.load('./../model_weights.pth')
    # model.load_state_dict(state_dict, strict=False)

    model = model.to(device)
    model.eval()

    movie_lists = get_ids_unpredicted(cursor, 'Movies')

    reviews = [text for _, text in movie_lists]
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
    
    return predictions_results
    
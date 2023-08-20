FROM python:3.8-slim-buster

EXPOSE 5432

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install mysql \
    && pip install -r requirements.txt
  
COPY app.py .
  
 CMD [ "python", "app.py"]
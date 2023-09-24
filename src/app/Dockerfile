FROM python:3.8-slim-buster

USER root

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y postgresql \
    && apt-get install -y gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/* 

RUN service postgresql start 

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
  
COPY app.py .
  
EXPOSE 8050

# CMD [ "python", "app.py"]
CMD ["tail", "-f"]
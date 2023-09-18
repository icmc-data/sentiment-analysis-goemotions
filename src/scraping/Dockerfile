FROM selenium/standalone-chrome

USER root
RUN apt-get update && apt-get install python3-distutils -y
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY scraping.py .

# RUN ["python3", "scraping.py"]
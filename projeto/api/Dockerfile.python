FROM selenium/standalone-chrome

WORKDIR /app

COPY requirements.txt chromedriver .
USER root
RUN apt-get update && apt-get install python3-distutils -y && apt-get install -y libglib2.0-0
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "scraping.py"]
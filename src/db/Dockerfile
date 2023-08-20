# Use an official Python runtime as the base imag
FROM python:3.9


# Set the working directory
WORKDIR /app


# Copy the requirements file into the container
COPY requirements.txt .


# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt


# Copy the application code into the container
COPY . .


# Run the command to start the scraping script
CMD ["python", "run.py"]


# # Use uma imagem base do Python com o ChromeDriver
# FROM python:3.9-slim-buster

# # Defina o diretório de trabalho dentro do contêiner
# WORKDIR /database_scripts

# # Instale as dependências do sistema
# RUN apt-get update && apt-get install -yq \
#     wget \
#     curl \
#     unzip \
#     gnupg \
#     && apt-get clean

# # Instale o Chrome e o ChromeDriver
# RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
#     && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
#     && apt-get update && apt-get install -yq \
#     google-chrome-stable \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# # Instale as dependências do Python
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Download and install Chrome
# RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
# RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
# RUN apt-get -y update
# RUN apt-get install -y google-chrome-stable

# # Baixe o ChromeDriver correspondente à versão do Chrome instalada
# RUN CHROME_VERSION=$(google-chrome-stable --version | awk '{ print $3 }' | cut -d '.' -f 1) \
#     && CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION) \
#     && wget -q --continue -P /chromedriver "https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip" \
#     && unzip /chromedriver/chromedriver* -d /usr/local/bin \
#     && rm -rf /chromedriver

# # Copie o arquivo de scraping para o diretório de trabalho
# COPY . .

# # Run the application
# CMD ["python", "./src/run.py"]

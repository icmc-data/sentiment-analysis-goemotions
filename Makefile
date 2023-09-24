# Set the Docker Compose file name
DOCKER_COMPOSE_FILE = docker-compose.yaml

# Define the Docker Compose commands
DOCKER_COMPOSE_BUILD = docker-compose build
DOCKER_COMPOSE_UP = docker-compose up -d
DOCKER_COMPOSE_DOWN = docker-compose down --volumes

# Load environment variables from .env file
include .env

build:
	$(DOCKER_COMPOSE_BUILD)

down:
	$(DOCKER_COMPOSE_DOWN)

up:
	POSTGRES_NAME=$(POSTGRES_NAME) \
	POSTGRES_USER=$(POSTGRES_USER) \
	POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
	POSTGRES_HOST=$(POSTGRES_HOST) \
	POSTGRES_PORT=$(POSTGRES_PORT) \
	$(DOCKER_COMPOSE_UP) 

clean:
	docker image prune -a

scraping:
	docker exec -it scraping sh -c 'python3 scraping.py'

app:
	docker exec -it dashapp sh -c 'python3 app.py'

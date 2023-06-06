# Set the Docker Compose file name
DOCKER_COMPOSE_FILE = docker-compose.yaml

# Define the Docker Compose commands
DOCKER_COMPOSE_BUILD = docker-compose build
DOCKER_COMPOSE_UP = docker-compose up -d
DOCKER_COMPOSE_DOWN = docker-compose down

# Load environment variables from .env file
include .env

build:
	docker build -t $(MYSQL_IMAGE_NAME) -f Dockerfile.mysql .
	docker build -t $(PYTHON_IMAGE_NAME) -f Dockerfile.python .

down:
	$(DOCKER_COMPOSE_DOWN)

up: build
	MYSQL_ROOT_PASSWORD=$(MYSQL_ROOT_PASSWORD) MYSQL_DATABASE=$(MYSQL_DATABASE) MYSQL_HOST=$(MYSQL_HOST) \
	$(DOCKER_COMPOSE_UP)
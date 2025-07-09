.PHONY: help build up down logs restart clean

help:
	@echo "LinkedIn Auto Publisher - Docker Commands"
	@echo "======================================="
	@echo "make build    - Build Docker image"
	@echo "make up       - Start application"
	@echo "make down     - Stop application"
	@echo "make logs     - View logs"
	@echo "make restart  - Restart application"
	@echo "make dev      - Start in development mode"
	@echo "make clean    - Clean up containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

dev:
	docker-compose -f docker-compose.dev.yml up

clean:
	docker-compose down -v
	rm -rf data/*.db logs/*.log
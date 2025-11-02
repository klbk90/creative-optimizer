.PHONY: help install dev prod migrate test clean

help:
	@echo "UTM Tracking - Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make dev      - Run development server"
	@echo "  make prod     - Run with Docker Compose"
	@echo "  make migrate  - Run database migrations"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up"

install:
	pip install -r requirements.txt

dev:
	uvicorn api.main:app --reload

prod:
	docker-compose up -d

migrate:
	alembic upgrade head

test:
	pytest tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose down -v

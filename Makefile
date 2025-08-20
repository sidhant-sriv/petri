# Petri Project Makefile
# Unified commands for development and deployment

.PHONY: help build up down logs clean dev-up prod-up

help: ## Show this help message
	@echo "Petri Project Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build:
	docker compose build

up:
	docker compose up -d

dev-up:
	docker compose up -d db neo4j redis world agent-dev

prod-up:
	docker compose --profile production up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

jupyter:
	@echo "Jupyter is available at: http://localhost:8888"
	@echo "Token: petri_jupyter_token (or check logs if using custom token)"

world-api:
	@echo "World API is available at: http://localhost:8000/docs"

neo4j-browser:
	@echo "Neo4j browser is available at: http://localhost:7474"
	@echo "Username: neo4j, Password: neo4j_password"

setup:
	cp env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Run 'make dev-up' to start development services"

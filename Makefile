.PHONY: setup deploy destroy validate test dev clean help

# Default environment
ENV ?= dev

# Python interpreter
PYTHON := python3
PIP := pip3

# Pulumi settings
PULUMI_STACK := superset-$(ENV)

help: ## Show this help message
	@echo 'Usage: make [target] ENV=<environment>'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo 'Environments: dev, staging, production'

setup: ## Initial project setup
	@echo "Setting up Apache Superset deployment environment..."
	$(PIP) install -r requirements.txt
	npm install
	@echo "Creating .env from template..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "Initializing Pulumi..."
	cd pulumi && pulumi login --local
	@echo "Setup complete!"

validate: ## Validate configuration files
	@echo "Validating system.yaml..."
	$(PYTHON) scripts/validate.py
	@echo "Checking Docker configurations..."
	docker-compose -f docker/docker-compose.yaml config --quiet
	@echo "Validation passed!"

deploy: validate ## Deploy stack to specified environment
	@echo "Deploying $(ENV) stack..."
	cd pulumi && pulumi stack select $(PULUMI_STACK) 2>/dev/null || pulumi stack init $(PULUMI_STACK)
	cd pulumi && pulumi config set environment $(ENV)
	cd pulumi && pulumi up

destroy: ## Destroy stack in specified environment
	@echo "Destroying $(ENV) stack..."
	cd pulumi && pulumi stack select $(PULUMI_STACK)
	cd pulumi && pulumi destroy

dev: ## Start local development environment
	@echo "Starting local Superset development environment..."
	docker-compose -f docker/docker-compose.yaml up

dev-down: ## Stop local development environment
	docker-compose -f docker/docker-compose.yaml down

dev-tunnel: ## Start local development with Cloudflare tunnel
	@echo "Starting local Superset with Cloudflare tunnel..."
	docker-compose -f docker/docker-compose.yaml --profile cloudflare up

setup-tunnel: ## Setup Cloudflare tunnel
	@echo "Setting up Cloudflare tunnel..."
	./scripts/setup-tunnel.sh

test: ## Run all tests
	@echo "Running tests..."
	$(PYTHON) -m pytest tests/ -v
	@echo "Tests complete!"

clean: ## Clean up generated files and caches
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose -f docker/docker-compose.yaml down -v
	@echo "Cleanup complete!"

logs: ## Show logs for specified environment
	@if [ "$(ENV)" = "dev" ]; then \
		docker-compose -f docker/docker-compose.yaml logs -f; \
	else \
		cd pulumi && pulumi stack select $(PULUMI_STACK) && pulumi logs -f; \
	fi

status: ## Show status of specified environment
	@echo "Status for $(ENV) environment:"
	@if [ "$(ENV)" = "dev" ]; then \
		docker-compose -f docker/docker-compose.yaml ps; \
	else \
		cd pulumi && pulumi stack select $(PULUMI_STACK) && pulumi stack; \
	fi
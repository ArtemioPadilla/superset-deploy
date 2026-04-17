.PHONY: setup deploy destroy validate test dev clean help

# Default environment
ENV ?= dev

# Python interpreter
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip3

# Check Python version
PYTHON_VERSION := $(shell python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_VERSION_OK := $(shell python3 -c 'import sys; print("1" if (3,8) <= sys.version_info[:2] <= (3,11) else "0")')

# Pulumi settings
PULUMI_STACK := superset-$(ENV)

help: ## Show this help message
	@echo 'Usage: make [target] ENV=<environment>'
	@echo ''
	@echo 'Quick Start:'
	@echo '  ./quick-start.sh  - Interactive setup (recommended!)'
	@echo '  make dev         - Minimal setup (SQLite only)'
	@echo '  make full-stack  - Full stack with PostgreSQL + monitoring'
	@echo ''
	@echo 'All Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo 'Environments: dev, staging, production (for cloud deployments)'

$(VENV): ## Create virtual environment
	@if [ "$(PYTHON_VERSION_OK)" != "1" ]; then \
		echo "❌ Error: Python 3.8-3.11 is required (found Python $(PYTHON_VERSION))"; \
		echo "   Python 3.11 is recommended for best compatibility."; \
		exit 1; \
	fi
	@echo "Creating Python virtual environment with Python $(PYTHON_VERSION)..."
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip

$(VENV)/bin/pytest: $(VENV) requirements-dev.txt ## Install development dependencies
	@echo "Installing development dependencies in virtual environment..."
	@$(PIP) install -r requirements-dev.txt

install-full: $(VENV) ## Install all dependencies including Pulumi
	@echo "Installing all dependencies (this may take a while)..."
	@$(PIP) install -r requirements.txt

quick-start: ## Quick start - Superset running in under 2 minutes!
	@./quick-start.sh

full-stack: ## Start full stack with PostgreSQL, Redis, and monitoring
	@./quick-start-full.sh

full-stack-down: ## Stop the full stack
	@docker-compose -f docker/docker-compose.full-stack.yaml down

full-stack-clean: ## Stop and remove all full stack data
	@docker-compose -f docker/docker-compose.full-stack.yaml down -v

setup: $(VENV)/bin/pytest ## Initial project setup
	@echo "Setting up Apache Superset deployment environment..."
	@./scripts/setup.sh

validate: $(VENV)/bin/pytest ## Validate configuration files
	@echo "Validating system.yaml..."
	$(PYTHON) scripts/validate.py
	@echo "Checking Docker configurations..."
	docker-compose -f docker/docker-compose.yaml config --quiet
	@echo "Validation passed!"

deploy: validate install-full ## Deploy stack to specified environment
	@echo "Deploying $(ENV) stack..."
	cd pulumi && pulumi stack select $(PULUMI_STACK) 2>/dev/null || pulumi stack init $(PULUMI_STACK)
	cd pulumi && pulumi config set environment $(ENV)
	cd pulumi && pulumi up

destroy: ## Destroy stack in specified environment
	@echo "Destroying $(ENV) stack..."
	cd pulumi && pulumi stack select $(PULUMI_STACK)
	cd pulumi && pulumi destroy

dev: ## Start local development environment (minimal - SQLite only)
	@echo "Starting local Superset development environment..."
	docker-compose -f docker/docker-compose.minimal.yaml up

dev-postgres: ## Start local development with PostgreSQL
	@echo "Starting Superset with PostgreSQL..."
	docker-compose -f docker/docker-compose.yaml --profile postgres up

dev-down: ## Stop local development environment
	docker-compose -f docker/docker-compose.minimal.yaml down
	docker-compose -f docker/docker-compose.yaml down

dev-tunnel: ## Start local development with Cloudflare tunnel
	@echo "Starting local Superset with Cloudflare tunnel..."
	docker-compose -f docker/docker-compose.yaml --profile cloudflare up

setup-tunnel: ## Setup Cloudflare tunnel
	@echo "Setting up Cloudflare tunnel..."
	./scripts/setup-tunnel.sh

test: $(VENV)/bin/pytest ## Run all tests
	@echo "Running tests..."
	$(PYTHON) -m pytest tests/ -v
	@echo "Tests complete!"

clean: ## Clean up generated files and caches
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose -f docker/docker-compose.yaml down -v
	@echo "Cleanup complete!"

clean-venv: ## Remove virtual environment
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Virtual environment removed!"

clean-all: clean clean-venv ## Clean everything including virtual environment
	@echo "Full cleanup complete!"

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
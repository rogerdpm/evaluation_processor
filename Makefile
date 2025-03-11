.PHONY: install  clean  docker-up docker-down

.ONESHELL:


# Define working directory
WORKDIR := $(shell pwd)/src


# include the .env file
include $(WORKDIR)/.env
export $(shell sed 's/=.*//' $(WORKDIR)/.env)


docker-up:
	docker compose -f $(shell pwd)/docker-compose.yaml up -d



docker-down:
	@if ! docker compose -f $(shell pwd)/docker-compose.yaml ps --quiet 2>/dev/null; then \
		echo "No containers are currently running"; \
		exit 0; \
	fi
	docker compose -f $(shell pwd)/docker-compose.yaml down
	@echo "Containers downed"


venv:
	@echo "WORKDIR: $(WORKDIR). Activating virtual environment..."
	@if [ ! -d "$(WORKDIR)/.venv" ]; then \
		echo "Virtual environment not found in $(WORKDIR). Creating it..."; \
		cd $(WORKDIR) && uv venv && . .venv/bin/activate && uv sync; \
	else \
		echo "Virtual environment already exists in $(WORKDIR). Activating..."; \
		cd $(WORKDIR) && . .venv/bin/activate && uv sync; \
	fi



install: docker-up venv
	@echo "Installing dependencies..."
	@echo "WORKDIR: $(WORKDIR)"
	cd $(WORKDIR) && . .venv/bin/activate && uv sync


clean: docker-down
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .venv/
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find ../ -type d -name .pytest_cache -exec rm -rf {} +

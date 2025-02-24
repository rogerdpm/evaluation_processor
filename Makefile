.PHONY: install test clean build publish docker-up docker-down create-db destroy-db

.ONESHELL:


venv:
	uv venv
	@echo "Virtual environment created! To activate, run:"
	@echo "source .venv/bin/activate"
	. .venv/bin/activate && uv sync


clean: 
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .venv/
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find ../ -type d -name .pytest_cache -exec rm -rf {} +

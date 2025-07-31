.PHONY: help install install-dev format lint test clean run

# Default target
help:
	@echo "Flask API Template - Available Commands"
	@echo "======================================"
	@echo "Development:"
	@echo "  install-dev    Install development dependencies and setup pre-commit"
	@echo "  format         Format code with black and isort"
	@echo "  lint           Run code quality checks (flake8, black, isort)"
	@echo "  test           Run tests with coverage"
	@echo "  clean          Clean up temporary files"
	@echo ""
	@echo "Application:"
	@echo "  install        Install production dependencies"
	@echo "  run            Run the Flask development server"
	@echo "  run-prod       Run the Flask production server"
	@echo ""
	@echo "Database:"
	@echo "  db-init        Initialize database"
	@echo "  db-migrate     Create database migration"
	@echo "  db-upgrade     Apply database migrations"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	./scripts/setup_dev.sh

# Code quality
format:
	@echo "🎨 Formatting code..."
	isort app/ tests/ scripts/
	black app/ tests/ scripts/
	@echo "✅ Code formatting complete!"

lint:
	@echo "🔍 Running code quality checks..."
	@echo "  - Checking import order with isort..."
	isort app/ tests/ scripts/ --check-only --diff
	@echo "  - Checking code format with black..."
	black app/ tests/ scripts/ --check --diff
	@echo "  - Running flake8..."
	flake8 app/ tests/ scripts/
	@echo "✅ Code quality checks passed!"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=app --cov-report=term-missing
	@echo "✅ Tests complete!"

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/ -v -m "unit" --cov=app --cov-report=term-missing

test-integration:
	@echo "🧪 Running integration tests..."
	pytest tests/ -v -m "integration" --cov=app --cov-report=term-missing

# Application
run:
	@echo "🚀 Starting Flask development server..."
	python run.py

run-prod:
	@echo "🚀 Starting Flask production server..."
	gunicorn -c gunicorn.conf.py wsgi:app

# Database
db-init:
	@echo "🗄️  Initializing database..."
	python scripts/init_db.py

db-migrate:
	@echo "🗄️  Creating database migration..."
	flask db migrate

db-upgrade:
	@echo "🗄️  Applying database migrations..."
	flask db upgrade

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "✅ Cleanup complete!"
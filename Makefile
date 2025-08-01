.PHONY: help install install-dev format lint test clean run run-dev run-prod shell debug-config validate-env configure-pip test-pip docker-build docker-build-dev network-test setup-china verify quick-setup

# Default target
help:
	@echo "Flask API Template - Available Commands"
	@echo "======================================"
	@echo "Development:"
	@echo "  install-dev    Install development dependencies and setup pre-commit"
	@echo "  setup-china    One-click setup for China mainland users"
	@echo "  quick-setup    Quick pip mirror setup (China users)"
	@echo "  format         Format code with black and isort"
	@echo "  lint           Run code quality checks (flake8, black, isort)"
	@echo "  test           Run tests with coverage"
	@echo "  clean          Clean up temporary files"
	@echo ""
	@echo "Application:"
	@echo "  install        Install production dependencies"
	@echo "  run            Run the Flask development server"
	@echo "  run-dev        Run enhanced development server with debugging"
	@echo "  run-prod       Run the Flask production server"
	@echo "  shell          Start interactive Flask shell with pre-loaded context"
	@echo "  debug-config   Show current configuration and environment"
	@echo "  validate-env   Validate development environment setup"
	@echo "  verify         Verify complete project setup"
	@echo "  configure-pip  Configure pip mirror source (China users)"
	@echo "  test-pip       Test pip mirror source speed"
	@echo "  network-test   Run comprehensive network diagnostic"
	@echo ""
	@echo "Database:"
	@echo "  db-init        Initialize database"
	@echo "  db-migrate     Create database migration"
	@echo "  db-upgrade     Apply database migrations"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build production Docker image (optimized)"
	@echo "  docker-build-dev Build development Docker image (optimized)"

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

run-dev:
	@echo "🚀 Starting enhanced development server..."
	python scripts/dev_server.py

run-prod:
	@echo "🚀 Starting Flask production server..."
	gunicorn -c gunicorn.conf.py wsgi:app

shell:
	@echo "🐚 Starting interactive Flask shell..."
	python scripts/shell_context.py

debug-config:
	@echo "🔍 Showing current configuration..."
	python scripts/debug_config.py

validate-env:
	@echo "✅ Validating development environment..."
	python scripts/validate_dev_env.py

configure-pip:
	@echo "🔧 Configuring pip mirror source..."
	./scripts/configure_pip_mirror.sh -m aliyun

test-pip:
	@echo "🧪 Testing pip mirror source speed..."
	python scripts/test_pip_mirror.py

network-test:
	@echo "🌐 Running network diagnostic..."
	python scripts/network_diagnostic.py

# Docker
docker-build:
	@echo "🐳 Building production Docker image (optimized)..."
	./scripts/docker_build_optimized.sh -e prod -m aliyun

docker-build-dev:
	@echo "🐳 Building development Docker image (optimized)..."
	./scripts/docker_build_optimized.sh -e dev -m aliyun

# China setup
setup-china:
	@echo "🇨🇳 One-click setup for China mainland users..."
	./scripts/setup_china.sh

verify:
	@echo "🔍 Verifying project setup..."
	python scripts/verify_setup.py

quick-setup:
	@echo "🚀 Quick setup for China mainland users..."
	./scripts/quick_setup.sh

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

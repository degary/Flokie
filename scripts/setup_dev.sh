#!/bin/bash

# Flask API Template - Development Setup Script
# This script sets up the development environment with code quality tools

set -e

echo "🚀 Setting up Flask API Template development environment..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected. Please activate your virtual environment first."
    echo "   Example: source venv/bin/activate"
    exit 1
fi

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install -r requirements/development.txt

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Run initial code formatting
echo "🎨 Running initial code formatting..."
echo "  - Running isort..."
isort app/ tests/ scripts/ --check-only --diff || {
    echo "    Fixing import order..."
    isort app/ tests/ scripts/
}

echo "  - Running black..."
black app/ tests/ scripts/ --check --diff || {
    echo "    Formatting code..."
    black app/ tests/ scripts/
}

echo "  - Running flake8..."
flake8 app/ tests/ scripts/

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  - Format code:           make format"
echo "  - Check code quality:    make lint"
echo "  - Run tests:            make test"
echo "  - Run pre-commit:       pre-commit run --all-files"
echo ""
echo "🎯 Pre-commit hooks are now installed and will run automatically on git commit."
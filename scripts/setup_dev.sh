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

# Create necessary directories
echo "📁 Creating development directories..."
mkdir -p logs
mkdir -p profiles
mkdir -p uploads
mkdir -p temp

# Set up environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f .env ]; then
    echo "   Copying .env.example to .env..."
    cp .env.example .env
    echo "   ✅ Created .env file - please review and update the values"
else
    echo "   ✅ .env file already exists"
fi

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Initialize database if needed
echo "🗄️  Checking database setup..."
if [ ! -f "dev_app.db" ]; then
    echo "   Initializing development database..."
    python scripts/init_db.py
else
    echo "   ✅ Development database already exists"
fi

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
flake8 app/ tests/ scripts/ || echo "    ⚠️  Some code quality issues found - run 'make lint' for details"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  - Start dev server:      make run-dev"
echo "  - Interactive shell:     make shell"
echo "  - Format code:           make format"
echo "  - Check code quality:    make lint"
echo "  - Run tests:             make test"
echo "  - Run pre-commit:        pre-commit run --all-files"
echo ""
echo "🌐 Development URLs:"
echo "  - API Server:            http://localhost:5000"
echo "  - API Documentation:     http://localhost:5000/docs"
echo "  - Health Check:          http://localhost:5000/health"
echo "  - Dev Info:              http://localhost:5000/dev/info"
echo ""
echo "🎯 Pre-commit hooks are now installed and will run automatically on git commit."
echo "🚀 Start developing with: make run-dev"

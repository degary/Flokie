# ⚡ Quick Start Guide

Get up and running with Flokie in just a few minutes! This guide will walk you through the fastest way to set up and start using the Flask API template.

## 🎯 What You'll Build

By the end of this guide, you'll have:
- ✅ A running Flask API with authentication
- ✅ Interactive API documentation
- ✅ A test user account
- ✅ Working API endpoints

## 📋 Prerequisites

Before you start, make sure you have:

- **Python 3.9+** installed ([Download Python](https://python.org/downloads/))
- **Git** installed ([Download Git](https://git-scm.com/downloads/))
- **Basic terminal/command line** knowledge

Optional but recommended:
- **Docker** for containerized development ([Download Docker](https://docker.com/get-started/))
- **VS Code** or your preferred code editor

## 🚀 Method 1: Local Development (Recommended for beginners)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/flokie.git
cd flokie

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# The default settings work for local development
# No changes needed for quick start!
```

### Step 3: Initialize Database

```bash
# Create database tables
flask db upgrade

# Optional: Create sample data
python scripts/init_db.py
```

### Step 4: Start the Server

```bash
# Start development server
python run.py

# Or use the Makefile
make run-dev
```

🎉 **Success!** Your API is now running at http://localhost:5000

## 🐳 Method 2: Docker (Recommended for experienced users)

### Quick Docker Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/flokie.git
cd flokie

# Start with Docker Compose
docker-compose -f docker-compose.dev.yml up --build
```

That's it! The API will be available at http://localhost:5000

## 🧪 Test Your Setup

### 1. Check API Health

```bash
# Test the health endpoint
curl http://localhost:5000/api/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. View API Documentation

Open your browser and go to:
- **Swagger UI**: http://localhost:5000/docs
- **API Info**: http://localhost:5000/

### 3. Register a Test User

```bash
# Register a new user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 4. Login and Get Tokens

```bash
# Login to get JWT tokens
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "testuser",
    "password": "testpassword123"
  }'
```

Save the `access_token` from the response for the next step.

### 5. Make Authenticated Request

```bash
# Get user profile (replace YOUR_TOKEN with actual token)
curl -X GET http://localhost:5000/api/users/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎮 Interactive Testing

### Using the Swagger UI

1. Go to http://localhost:5000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

### Using Python Requests

```python
import requests

# Base URL
base_url = "http://localhost:5000/api"

# Register a user
response = requests.post(f"{base_url}/auth/register", json={
    "username": "pythonuser",
    "email": "python@example.com",
    "password": "pythonpassword123"
})

print("Registration:", response.status_code)

# Login
response = requests.post(f"{base_url}/auth/login", json={
    "username_or_email": "pythonuser",
    "password": "pythonpassword123"
})

tokens = response.json()["tokens"]
access_token = tokens["access_token"]

# Get profile
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{base_url}/users/profile", headers=headers)

print("Profile:", response.json())
```

## 🔧 Development Commands

Once you have the basic setup running, here are useful commands:

```bash
# Code formatting
make format

# Run tests
make test

# Run tests with coverage
make test-coverage

# Check code quality
make lint

# Database operations
make migrate message="Add new field"  # Create migration
make upgrade                          # Apply migrations
make downgrade                        # Rollback migrations

# Development server with debug
make run-dev

# Flask shell
make shell
```

## 📁 Project Structure Overview

Here's what you'll find in the project:

```
flokie/
├── app/                    # Main application code
│   ├── api/               # API documentation
│   ├── controllers/       # HTTP request handlers
│   ├── services/          # Business logic
│   ├── models/            # Database models
│   └── config/            # Configuration files
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── requirements/          # Python dependencies
```

## 🎯 Next Steps

Now that you have Flokie running, here's what to explore next:

### 1. **Explore the API** 📖
- Check out the [API Guide](api-guide.md) for detailed endpoint documentation
- Try different endpoints in the Swagger UI
- Test authentication flows

### 2. **Understand the Architecture** 🏗️
- Read the [Project Overview](project-overview.md)
- Explore the code structure
- Understand the service layer pattern

### 3. **Customize for Your Project** ⚙️
- Modify the User model for your needs
- Add new endpoints and business logic
- Configure for your specific requirements

### 4. **Set Up Development Environment** 🛠️
- Read the [Development Guide](development.md)
- Set up your IDE with proper linting and formatting
- Configure pre-commit hooks

### 5. **Deploy to Production** 🚀
- Check out the [Deployment Guide](deployment.md)
- Set up CI/CD pipelines
- Configure production environment

## 🆘 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# If port 5000 is busy, use a different port
export FLASK_RUN_PORT=5001
python run.py
```

#### Database Issues
```bash
# Reset database
rm instance/flokie.db  # SQLite only
flask db upgrade
```

#### Permission Issues (macOS/Linux)
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

#### Python Version Issues
```bash
# Check Python version
python --version

# Use specific Python version
python3.9 -m venv venv
```

### Getting Help

If you run into issues:

1. **Check the logs** in your terminal
2. **Review the [FAQ](faq-troubleshooting.md)**
3. **Search existing [GitHub Issues](https://github.com/yourusername/flokie/issues)**
4. **Create a new issue** with details about your problem

## 🎉 Congratulations!

You now have a fully functional Flask API with:

- ✅ JWT authentication
- ✅ User management
- ✅ Interactive documentation
- ✅ Comprehensive testing
- ✅ Production-ready structure

Ready to build something amazing? Start customizing Flokie for your specific needs!

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/14/tutorial/)
- [JWT Introduction](https://jwt.io/introduction)
- [REST API Best Practices](https://restfulapi.net/)

---

**Happy coding!** 🚀 If this guide helped you, consider giving the project a ⭐ on GitHub!

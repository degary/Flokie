# 🚀 Flokie - Production-Ready Flask API Template

[![CI](https://github.com/yourusername/flokie/workflows/Continuous%20Integration/badge.svg)](https://github.com/yourusername/flokie/actions)
[![CD](https://github.com/yourusername/flokie/workflows/Continuous%20Deployment/badge.svg)](https://github.com/yourusername/flokie/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![Flask Version](https://img.shields.io/badge/flask-2.3%2B-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)](https://github.com/yourusername/flokie)

> 🏗️ **A comprehensive, enterprise-grade Flask API template** designed for building scalable, maintainable web applications with modern development practices, complete CI/CD pipelines, and production-ready deployment configurations.

## 🌟 Why Choose Flokie?

Flokie eliminates the repetitive setup work and provides a solid foundation for your Flask API projects with:

- ⚡ **Rapid Development**: Get started in minutes with pre-configured development environment
- 🔒 **Security First**: Built-in JWT authentication, input validation, and security best practices
- 🧪 **Test-Driven**: Comprehensive test suite with 80%+ coverage and automated testing
- 🚀 **Production Ready**: Docker containers, CI/CD pipelines, and deployment configurations
- 📚 **Well Documented**: Interactive API docs, comprehensive guides, and code examples
- 🛠️ **Developer Experience**: Hot reload, code formatting, linting, and debugging tools

## ✨ Key Features

<details>
<summary><strong>🔐 Authentication & Security</strong></summary>

- **JWT Authentication**: Secure token-based authentication with access/refresh tokens
- **Password Security**: Bcrypt hashing with account lockout protection
- **Email Verification**: Account activation via email verification
- **Password Reset**: Secure password reset with time-limited tokens
- **Account Management**: User activation, deactivation, and admin controls
- **Security Headers**: CORS, CSP, and other security headers configured
- **Input Validation**: Comprehensive request validation with detailed error messages

</details>

<details>
<summary><strong>👥 User Management</strong></summary>

- **User Registration**: Complete signup flow with validation
- **Profile Management**: User profile CRUD operations
- **User Search**: Advanced search and filtering capabilities
- **Account States**: Active, inactive, verified, locked account states
- **Admin Features**: User management for administrative users
- **Audit Trail**: Login tracking and security event logging

</details>

<details>
<summary><strong>🗄️ Database & ORM</strong></summary>

- **SQLAlchemy Integration**: Powerful ORM with relationship management
- **Database Migrations**: Alembic-powered schema versioning
- **Multiple Database Support**: PostgreSQL (recommended), MySQL, SQLite
- **Connection Pooling**: Optimized database connection management
- **Query Optimization**: Built-in query performance monitoring
- **Data Validation**: Model-level validation with custom validators

</details>

<details>
<summary><strong>📚 API Documentation</strong></summary>

- **Interactive Swagger UI**: Auto-generated API documentation
- **Flask-RESTX Integration**: Automatic schema generation
- **Request/Response Models**: Comprehensive data model definitions
- **API Examples**: Working code examples and test cases
- **Postman Collection**: Ready-to-use API collection for testing

</details>

<details>
<summary><strong>🧪 Testing & Quality</strong></summary>

- **Comprehensive Test Suite**: Unit, integration, and API tests
- **80%+ Test Coverage**: High code coverage with detailed reporting
- **Pytest Framework**: Modern testing with fixtures and parametrization
- **Test Factories**: Reusable test data generation
- **Performance Testing**: Load testing with Locust integration
- **Code Quality Tools**: Black, isort, flake8, and pre-commit hooks

</details>

<details>
<summary><strong>🚀 DevOps & Deployment</strong></summary>

- **Docker Support**: Multi-stage builds for development and production
- **Docker Compose**: Complete environment orchestration
- **CI/CD Pipelines**: GitHub Actions for automated testing and deployment
- **Multi-Environment**: Development, acceptance, and production configurations
- **Health Checks**: Application and infrastructure health monitoring
- **Blue-Green Deployment**: Zero-downtime deployment strategy

</details>

## 🚀 Quick Start

### 🔧 Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/flokie.git
cd flokie

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
make install-dev

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Initialize database
make upgrade

# 6. Run the application
make run-dev
```

🎉 **Your API is now running at `http://localhost:5000`**

### 🐳 Docker Quick Start

```bash
# Development environment
docker-compose -f docker-compose.dev.yml up --build

# Production environment
docker-compose -f docker-compose.prod.yml up -d
```

### ⚡ One-Command Setup

```bash
# Automated setup script
./scripts/quick_setup.sh
```

## 📖 API Documentation & Examples

### 🔗 Interactive Documentation
- **Swagger UI**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/api/health
- **API Status**: http://localhost:5000/

### 🔑 Authentication Flow

```python
import requests

# Register a new user
response = requests.post('http://localhost:5000/api/auth/register', json={
    'username': 'johndoe',
    'email': 'john@example.com',
    'password': 'securepassword123'
})

# Login and get tokens
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username_or_email': 'johndoe',
    'password': 'securepassword123'
})

tokens = response.json()['tokens']
access_token = tokens['access_token']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {access_token}'}
profile = requests.get('http://localhost:5000/api/users/profile', headers=headers)
```

### 📋 Core API Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/register` | POST | User registration | ❌ |
| `/api/auth/login` | POST | User login | ❌ |
| `/api/auth/refresh` | POST | Refresh access token | ✅ (Refresh) |
| `/api/auth/logout` | POST | User logout | ✅ |
| `/api/auth/password/reset-request` | POST | Request password reset | ❌ |
| `/api/auth/password/reset` | POST | Reset password | ❌ |
| `/api/auth/password/change` | POST | Change password | ✅ |
| `/api/auth/email/verify` | POST | Verify email address | ❌ |
| `/api/users/profile` | GET/PUT | User profile management | ✅ |
| `/api/users` | GET | List users (admin) | ✅ (Admin) |
| `/api/health` | GET | Basic health check | ❌ |
| `/api/health/detailed` | GET | Detailed system status | ❌ |

## 🏗️ Architecture Overview

```
flokie/
├── 📁 app/                          # Application core
│   ├── 📁 api/                      # Flask-RESTX API documentation
│   │   ├── auth_namespace.py        # Authentication API docs
│   │   ├── user_namespace.py        # User management API docs
│   │   ├── health_namespace.py      # Health check API docs
│   │   └── models.py                # API response models
│   ├── 📁 controllers/              # Request handlers (Flask blueprints)
│   │   ├── auth_controller.py       # Authentication endpoints
│   │   ├── user_controller.py       # User management endpoints
│   │   ├── health_controller.py     # Health check endpoints
│   │   └── doc_controller.py        # Documentation endpoints
│   ├── 📁 services/                 # Business logic layer
│   │   ├── auth_service.py          # Authentication business logic
│   │   └── user_service.py          # User management business logic
│   ├── 📁 models/                   # Database models (SQLAlchemy)
│   │   ├── base.py                  # Base model with common fields
│   │   └── user.py                  # User model with authentication
│   ├── 📁 schemas/                  # Data validation schemas (Marshmallow)
│   │   ├── auth_schemas.py          # Authentication request/response schemas
│   │   ├── user_schemas.py          # User management schemas
│   │   └── common_schemas.py        # Shared validation schemas
│   ├── 📁 middleware/               # Custom middleware
│   │   ├── auth_middleware.py       # JWT authentication middleware
│   │   ├── logging_middleware.py    # Request/response logging
│   │   └── performance_middleware.py # Performance monitoring
│   ├── 📁 utils/                    # Utility functions
│   │   ├── exceptions.py            # Custom exception classes
│   │   ├── error_handlers.py        # Global error handling
│   │   ├── error_helpers.py         # Error handling utilities
│   │   ├── validation.py            # Input validation helpers
│   │   └── logging_config.py        # Logging configuration
│   ├── 📁 config/                   # Environment configurations
│   │   ├── base.py                  # Base configuration
│   │   ├── development.py           # Development settings
│   │   ├── testing.py               # Testing settings
│   │   ├── acceptance.py            # Acceptance testing settings
│   │   └── production.py            # Production settings
│   └── extensions.py                # Flask extensions initialization
├── 📁 tests/                        # Comprehensive test suite
│   ├── 📁 unit/                     # Unit tests for individual components
│   ├── 📁 integration/              # Integration tests for workflows
│   ├── conftest.py                  # Pytest configuration and fixtures
│   ├── factories.py                 # Test data factories
│   └── utils.py                     # Test utilities and helpers
├── 📁 scripts/                      # Utility and deployment scripts
├── 📁 docs/                         # Project documentation
├── 📁 .github/                      # GitHub Actions CI/CD workflows
├── 📁 docker/                       # Docker configurations
├── 📁 nginx/                        # Nginx reverse proxy configuration
└── 📁 requirements/                 # Python dependencies by environment
```

## 🧪 Development & Testing

### 🔧 Development Commands

```bash
# Code quality and formatting
make format                 # Format code with Black and isort
make lint                   # Run flake8 linting
make security-check         # Run security scans

# Testing
make test                   # Run all tests
make test-coverage          # Run tests with coverage report
make test-unit              # Run unit tests only
make test-integration       # Run integration tests only

# Database operations
make migrate message="Add new field"  # Create migration
make upgrade                # Apply migrations
make downgrade              # Rollback migrations

# Development server
make run-dev                # Development server with debug
make run                    # Standard development server
make shell                  # Flask shell with context
```

### 🧪 Testing Strategy

The project includes a comprehensive testing strategy with multiple test types:

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test component interactions
- **API Tests**: Test complete request/response cycles
- **Performance Tests**: Load testing and benchmarking
- **Security Tests**: Vulnerability scanning and security validation

```bash
# Run specific test categories
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests
pytest -m "auth" -v                      # Authentication tests
pytest -m "not slow" -v                  # Skip slow tests
pytest --cov=app --cov-report=html       # Coverage report
```

### 📊 Code Quality Metrics

- **Test Coverage**: 80%+ required
- **Code Style**: Black formatting enforced
- **Import Sorting**: isort configuration
- **Linting**: flake8 with custom rules
- **Type Hints**: Encouraged throughout codebase
- **Security**: Bandit security linting
- **Dependencies**: Safety vulnerability checking

## 🚀 Deployment

### 🐳 Docker Deployment

The project includes optimized Docker configurations for different environments:

```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Acceptance Testing
docker-compose -f docker-compose.acc.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### ☁️ Cloud Deployment

Ready-to-use configurations for major cloud providers:

- **AWS**: ECS, Elastic Beanstalk, Lambda
- **Google Cloud**: Cloud Run, GKE, App Engine
- **Azure**: Container Instances, App Service
- **Heroku**: One-click deployment
- **DigitalOcean**: App Platform, Droplets

### 🔄 CI/CD Pipeline

Automated GitHub Actions workflows:

- **Continuous Integration**: Code quality, testing, security scans
- **Continuous Deployment**: Multi-environment deployment pipeline
- **Security Scanning**: Dependency and container vulnerability scans
- **Performance Testing**: Automated performance benchmarks
- **Release Management**: Automated versioning and changelog generation

## 📚 Documentation

### 📖 Available Guides

- [**Quick Start Guide**](docs/quick-start.md) - Get up and running in minutes
- [**Project Overview**](docs/project-overview.md) - Architecture and design principles
- [**Features Documentation**](docs/features.md) - Comprehensive feature list with examples
- [**API Guide**](docs/api-guide.md) - Comprehensive API documentation with examples
- [**Development Guide**](docs/development.md) - Local development setup and workflows
- [**Deployment Guide**](docs/deployment.md) - Production deployment and infrastructure
- [**Security Guide**](docs/security.md) - Security features and best practices
- [**FAQ & Troubleshooting**](docs/faq-troubleshooting.md) - Common issues and solutions

### 🔧 Configuration

The application supports multiple configuration environments:

- **Development** (`.env.dev`): Local development with debug enabled
- **Testing** (`.env.test`): Automated testing configuration
- **Acceptance** (`.env.acc`): Acceptance testing environment
- **Production** (`.env.prod`): Production deployment settings

Key configuration options:

```bash
# Application
FLASK_CONFIG=production
SECRET_KEY=your-secret-key
DEBUG=False

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES_HOURS=1
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Monitoring (optional)
SENTRY_DSN=your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-newrelic-key
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### 🔄 Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with tests
4. **Run** the test suite (`make test`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### 📋 Code Standards

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints where appropriate
- Follow conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - The web framework that powers this template
- [SQLAlchemy](https://www.sqlalchemy.org/) - The Python SQL toolkit and ORM
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) - JWT token management
- [Flask-RESTX](https://flask-restx.readthedocs.io/) - API documentation framework
- [Pytest](https://pytest.org/) - Testing framework

## 📞 Support & Community

- 📖 **Documentation**: [Project Wiki](https://github.com/yourusername/flokie/wiki)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/flokie/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/flokie/discussions)
- 📧 **Email**: support@example.com

---

<div align="center">

**⭐ If this project helped you, please consider giving it a star! ⭐**

Made with ❤️ by the Flokie team

</div>

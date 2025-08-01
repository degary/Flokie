# Development Environment Guide

This guide covers setting up and using the development environment for the Flask API Template.

## Quick Start

1. **Install dependencies:**
   ```bash
   make install-dev
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development server:**
   ```bash
   make run-dev
   ```

## Development Commands

### Environment Setup
- `make install-dev` - Install all development dependencies and set up pre-commit hooks
- `make validate-env` - Validate your development environment setup
- `make debug-config` - Show current configuration and environment variables

### Code Quality
- `make format` - Format code with Black and isort
- `make lint` - Run code quality checks (flake8, Black, isort)
- `pre-commit run --all-files` - Run all pre-commit hooks

### Testing
- `make test` - Run all tests with coverage
- `make test-unit` - Run only unit tests
- `make test-integration` - Run only integration tests

### Development Server
- `make run` - Start basic Flask development server
- `make run-dev` - Start enhanced development server with debugging features
- `make shell` - Start interactive Flask shell with pre-loaded context

### Database
- `make db-init` - Initialize database with tables
- `make db-migrate` - Create new database migration
- `make db-upgrade` - Apply database migrations

## Environment Variables

### Flask Configuration
- `FLASK_CONFIG` - Configuration environment (development, testing, production)
- `FLASK_DEBUG` - Enable/disable debug mode (true/false)
- `FLASK_HOST` - Server host (default: 0.0.0.0)
- `FLASK_PORT` - Server port (default: 5000)
- `FLASK_USE_RELOADER` - Enable auto-reload on code changes (true/false)
- `FLASK_USE_DEBUGGER` - Enable interactive debugger (true/false)

### Database
- `DEV_DATABASE_URL` - Development database URL
- `TEST_DATABASE_URL` - Testing database URL

### Security
- `SECRET_KEY` - Flask secret key for sessions
- `JWT_SECRET_KEY` - JWT token signing key

### Logging
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_TO_FILE` - Enable file logging (true/false)
- `LOG_FILE_PATH` - Log file path

### Development Features
- `ERROR_INCLUDE_DETAILS` - Include error details in responses (true/false)
- `ERROR_INCLUDE_TRACEBACK` - Include traceback in error responses (true/false)
- `ERROR_MONITORING_ENABLED` - Enable error monitoring (true/false)
- `ENABLE_PROFILING` - Enable request profiling (true/false)
- `SLOW_REQUEST_THRESHOLD` - Threshold for slow request logging (seconds)

## Development Tools

### Enhanced Development Server
The enhanced development server (`make run-dev`) provides:
- Automatic environment variable loading from `.env`
- Database initialization check
- Detailed startup information
- Better error handling and logging

### Interactive Shell
The interactive shell (`make shell`) provides:
- Pre-loaded Flask app context
- Common models and services imported
- Helper functions for development:
  - `show_users()` - Display all users
  - `create_sample_data()` - Create sample users
  - `reset_database()` - Reset database with sample data
  - `login_user(username, password)` - Test user login

### Code Quality Tools
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Code linting with docstring checks
- **pre-commit** - Git hooks for code quality

## Development Workflow

1. **Start development:**
   ```bash
   make run-dev
   ```

2. **Make code changes** - The server will automatically reload

3. **Run tests:**
   ```bash
   make test
   ```

4. **Check code quality:**
   ```bash
   make lint
   ```

5. **Format code:**
   ```bash
   make format
   ```

6. **Commit changes** - Pre-commit hooks will run automatically

## Debugging

### Interactive Debugging
When `FLASK_DEBUG=true`, the development server provides:
- Interactive debugger in browser for exceptions
- Automatic reloading on code changes
- Detailed error pages

### Configuration Debugging
Use `make debug-config` to see:
- Current configuration values
- Environment variables
- Database connection status
- Available routes

### Database Debugging
Use the interactive shell to inspect database state:
```python
# Start shell
make shell

# Show all users
show_users()

# Create test data
create_sample_data()

# Test login
login_user('admin', 'admin123')
```

## Common Issues

### Database Issues
- **Database not found**: Run `make db-init` to initialize
- **Migration errors**: Check database URL and permissions
- **Sample data errors**: Ensure database is initialized first

### Environment Issues
- **Missing .env file**: Copy from `.env.example`
- **Import errors**: Ensure virtual environment is activated
- **Port conflicts**: Change `FLASK_PORT` in `.env`

### Code Quality Issues
- **Formatting errors**: Run `make format`
- **Linting errors**: Fix issues reported by `make lint`
- **Pre-commit failures**: Fix issues and commit again

## Performance Monitoring

Enable profiling in development:
```bash
# In .env
ENABLE_PROFILING=true
SLOW_REQUEST_THRESHOLD=0.5
```

This will log slow requests and provide performance metrics.

## Security in Development

Development mode includes additional security features:
- Detailed error messages (disabled in production)
- Request/response logging
- Debug toolbar (if installed)
- CORS enabled for local development

Remember to use different secrets for development and production!

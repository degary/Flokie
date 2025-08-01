#!/bin/bash
# Environment setup script for Flask API Template
# Sets up environment-specific configurations and dependencies

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [OPTIONS]

Set up environment-specific configurations for Flask API Template.

ENVIRONMENTS:
    dev         Development environment (default)
    test        Testing environment
    acc         Acceptance environment
    prod        Production environment

OPTIONS:
    -h, --help          Show this help message
    -f, --force         Force setup without confirmation
    -s, --secrets       Generate secrets for production environments
    -d, --database      Initialize database
    -c, --check         Check environment setup
    --skip-deps         Skip dependency installation
    --skip-db           Skip database setup

EXAMPLES:
    $0 dev                      # Setup development environment
    $0 prod --secrets           # Setup production with secrets
    $0 acc --database           # Setup acceptance with database
    $0 test --check             # Check test environment setup

EOF
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system dependencies
check_system_deps() {
    log "Checking system dependencies..."

    local missing_deps=()

    # Check Python
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi

    # Check pip
    if ! command_exists pip3; then
        missing_deps+=("python3-pip")
    fi

    # Check Docker (optional but recommended)
    if ! command_exists docker; then
        warn "Docker not found (optional but recommended)"
    fi

    # Check Docker Compose (optional but recommended)
    if ! command_exists docker-compose; then
        warn "Docker Compose not found (optional but recommended)"
    fi

    # Check OpenSSL for secrets generation
    if ! command_exists openssl; then
        missing_deps+=("openssl")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "Missing system dependencies: ${missing_deps[*]}"
        error "Please install missing dependencies and try again"
        exit 1
    fi

    log "System dependencies check passed"
}

# Install Python dependencies
install_python_deps() {
    local env="$1"
    local skip_deps="$2"

    if [[ "$skip_deps" == "true" ]]; then
        info "Skipping dependency installation"
        return 0
    fi

    log "Installing Python dependencies for $env environment..."

    # Determine requirements file
    local req_file="requirements/base.txt"
    case "$env" in
        dev)
            req_file="requirements/development.txt"
            ;;
        test)
            req_file="requirements/testing.txt"
            ;;
        prod|acc)
            req_file="requirements/production.txt"
            ;;
    esac

    if [[ ! -f "$req_file" ]]; then
        error "Requirements file not found: $req_file"
        exit 1
    fi

    # Install dependencies
    if command_exists pip3; then
        pip3 install -r "$req_file"
    else
        error "pip3 not found"
        exit 1
    fi

    log "Python dependencies installed successfully"
}

# Setup environment file
setup_env_file() {
    local env="$1"
    local force="$2"

    log "Setting up environment file for $env..."

    local env_file=".env"
    local source_env_file=".env.$env"

    if [[ ! -f "$source_env_file" ]]; then
        error "Environment template not found: $source_env_file"
        exit 1
    fi

    if [[ -f "$env_file" && "$force" != "true" ]]; then
        warn "Environment file already exists: $env_file"
        read -p "Overwrite existing .env file? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            info "Keeping existing .env file"
            return 0
        fi
    fi

    # Copy environment template
    cp "$source_env_file" "$env_file"

    log "Environment file created: $env_file"

    # Set appropriate permissions
    chmod 600 "$env_file"

    if [[ "$env" == "prod" || "$env" == "acc" ]]; then
        warn "Remember to update production secrets in $env_file"
        warn "Use 'scripts/manage_secrets.sh generate $env' to generate secrets"
    fi
}

# Initialize database
init_database() {
    local env="$1"
    local skip_db="$2"

    if [[ "$skip_db" == "true" ]]; then
        info "Skipping database initialization"
        return 0
    fi

    log "Initializing database for $env environment..."

    # Set environment
    export FLASK_CONFIG="$env"

    # Check if Flask app can be imported
    if ! python3 -c "from app import create_app; create_app('$env')" >/dev/null 2>&1; then
        error "Failed to import Flask app. Check your configuration."
        exit 1
    fi

    # Initialize database migrations
    if [[ ! -d "migrations" ]]; then
        log "Initializing database migrations..."
        python3 -c "
from flask_migrate import init
from app import create_app, db
app = create_app('$env')
with app.app_context():
    init()
"
    fi

    # Run database migrations
    log "Running database migrations..."
    python3 -c "
from flask_migrate import upgrade
from app import create_app, db
app = create_app('$env')
with app.app_context():
    upgrade()
"

    log "Database initialized successfully"
}

# Generate secrets for production environments
generate_secrets() {
    local env="$1"

    if [[ "$env" != "acc" && "$env" != "prod" ]]; then
        info "Secret generation not needed for $env environment"
        return 0
    fi

    log "Generating secrets for $env environment..."

    if [[ -x "$SCRIPT_DIR/manage_secrets.sh" ]]; then
        "$SCRIPT_DIR/manage_secrets.sh" generate "$env"
    else
        error "Secrets management script not found or not executable"
        exit 1
    fi
}

# Validate environment setup
validate_setup() {
    local env="$1"

    log "Validating environment setup for $env..."

    local errors=0

    # Check environment file
    if [[ ! -f ".env" ]]; then
        error "Environment file not found: .env"
        errors=$((errors + 1))
    fi

    # Check Python dependencies
    if ! python3 -c "import flask" >/dev/null 2>&1; then
        error "Flask not installed or not accessible"
        errors=$((errors + 1))
    fi

    # Check Flask app
    export FLASK_CONFIG="$env"
    if ! python3 -c "from app import create_app; create_app('$env')" >/dev/null 2>&1; then
        error "Failed to create Flask app"
        errors=$((errors + 1))
    fi

    # Validate configuration
    if [[ -x "$SCRIPT_DIR/validate_config.py" ]]; then
        if ! python3 "$SCRIPT_DIR/validate_config.py" "$env"; then
            error "Configuration validation failed"
            errors=$((errors + 1))
        fi
    fi

    # Check database connection (for non-test environments)
    if [[ "$env" != "test" ]]; then
        if ! python3 -c "
from app import create_app, db
app = create_app('$env')
with app.app_context():
    db.engine.execute('SELECT 1')
" >/dev/null 2>&1; then
            warn "Database connection test failed (this may be expected if DB is not running)"
        fi
    fi

    if [[ $errors -eq 0 ]]; then
        log "Environment setup validation passed"
    else
        error "Environment setup validation failed with $errors errors"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    local env="$1"

    log "Creating necessary directories..."

    local dirs=("logs" "instance" "uploads")

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done

    # Set appropriate permissions
    chmod 755 logs instance uploads
}

# Setup development tools
setup_dev_tools() {
    local env="$1"

    if [[ "$env" != "dev" ]]; then
        return 0
    fi

    log "Setting up development tools..."

    # Setup pre-commit hooks
    if command_exists pre-commit && [[ -f ".pre-commit-config.yaml" ]]; then
        pre-commit install
        log "Pre-commit hooks installed"
    fi

    # Create development database if it doesn't exist
    if [[ ! -f "instance/dev_app.db" ]]; then
        log "Creating development database..."
        export FLASK_CONFIG=development
        python3 -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
"
        log "Development database created"
    fi
}

# Parse command line arguments
parse_args() {
    ENVIRONMENT="dev"
    FORCE=false
    GENERATE_SECRETS=false
    INIT_DATABASE=false
    CHECK_SETUP=false
    SKIP_DEPS=false
    SKIP_DB=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -s|--secrets)
                GENERATE_SECRETS=true
                shift
                ;;
            -d|--database)
                INIT_DATABASE=true
                shift
                ;;
            -c|--check)
                CHECK_SETUP=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            dev|test|acc|prod)
                ENVIRONMENT="$1"
                shift
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    cd "$PROJECT_ROOT"

    parse_args "$@"

    log "Setting up $ENVIRONMENT environment..."

    # Check system dependencies
    check_system_deps

    # Create necessary directories
    create_directories "$ENVIRONMENT"

    # Install Python dependencies
    install_python_deps "$ENVIRONMENT" "$SKIP_DEPS"

    # Setup environment file
    setup_env_file "$ENVIRONMENT" "$FORCE"

    # Generate secrets if requested
    if [[ "$GENERATE_SECRETS" == "true" ]]; then
        generate_secrets "$ENVIRONMENT"
    fi

    # Initialize database if requested
    if [[ "$INIT_DATABASE" == "true" ]]; then
        init_database "$ENVIRONMENT" "$SKIP_DB"
    fi

    # Setup development tools
    setup_dev_tools "$ENVIRONMENT"

    # Validate setup if requested
    if [[ "$CHECK_SETUP" == "true" ]]; then
        validate_setup "$ENVIRONMENT"
    fi

    log "Environment setup completed successfully!"

    # Show next steps
    info "Next steps:"
    case "$ENVIRONMENT" in
        dev)
            info "  1. Run 'python run.py' to start development server"
            info "  2. Visit http://localhost:5000/api/health to test"
            ;;
        test)
            info "  1. Run 'pytest' to execute tests"
            info "  2. Run 'pytest --cov=app' for coverage report"
            ;;
        acc|prod)
            info "  1. Update secrets in .env file or use manage_secrets.sh"
            info "  2. Run 'scripts/deploy.sh $ENVIRONMENT up' to deploy"
            info "  3. Run 'scripts/validate_config.py $ENVIRONMENT' to validate"
            ;;
    esac
}

# Run main function
main "$@"

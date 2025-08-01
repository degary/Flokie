#!/bin/bash
# Main deployment script for Flask API Template
# Supports multiple environments: dev, test, acc, staging, prod

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_ENV="dev"
COMPOSE_PROJECT_NAME="flask-api-template"

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
Usage: $0 [OPTIONS] ENVIRONMENT [ACTION]

Deploy Flask API Template to different environments.

ENVIRONMENTS:
    dev         Development environment (default)
    test        Testing environment
    acc         Acceptance environment
    staging     Staging environment
    prod        Production environment

ACTIONS:
    up          Start services (default)
    down        Stop services
    restart     Restart services
    logs        Show logs
    status      Show service status
    build       Build images
    pull        Pull latest images
    backup      Backup data (prod/staging only)
    restore     Restore data (prod/staging only)

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -f, --force         Force action without confirmation
    -b, --build         Force rebuild images
    --no-cache          Build without cache
    --scale N           Scale app service to N replicas
    --env-file FILE     Use custom environment file

EXAMPLES:
    $0 dev                      # Deploy to development
    $0 prod up --build          # Deploy to production with rebuild
    $0 staging restart          # Restart staging environment
    $0 prod logs                # Show production logs
    $0 acc down                 # Stop acceptance environment

EOF
}

# Parse command line arguments
parse_args() {
    ENVIRONMENT=""
    ACTION="up"
    VERBOSE=false
    FORCE=false
    BUILD=false
    NO_CACHE=false
    SCALE=""
    ENV_FILE=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -b|--build)
                BUILD=true
                shift
                ;;
            --no-cache)
                NO_CACHE=true
                shift
                ;;
            --scale)
                SCALE="$2"
                shift 2
                ;;
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            dev|test|acc|staging|prod)
                if [[ -z "$ENVIRONMENT" ]]; then
                    ENVIRONMENT="$1"
                else
                    ACTION="$1"
                fi
                shift
                ;;
            up|down|restart|logs|status|build|pull|backup|restore)
                ACTION="$1"
                shift
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Set default environment if not provided
    if [[ -z "$ENVIRONMENT" ]]; then
        ENVIRONMENT="$DEFAULT_ENV"
    fi
}

# Validate environment
validate_environment() {
    case "$ENVIRONMENT" in
        dev|test|acc|staging|prod)
            ;;
        *)
            error "Invalid environment: $ENVIRONMENT"
            error "Valid environments: dev, test, acc, staging, prod"
            exit 1
            ;;
    esac
}

# Get docker-compose file for environment
get_compose_file() {
    local env="$1"
    case "$env" in
        dev)
            echo "docker-compose.dev.yml"
            ;;
        test)
            echo "docker-compose.test.yml"
            ;;
        acc)
            echo "docker-compose.acc.yml"
            ;;
        staging)
            echo "docker-compose.staging.yml"
            ;;
        prod)
            echo "docker-compose.prod.yml"
            ;;
        *)
            echo "docker-compose.yml"
            ;;
    esac
}

# Check if environment file exists
check_env_file() {
    local env="$1"
    local env_file

    if [[ -n "$ENV_FILE" ]]; then
        env_file="$ENV_FILE"
    else
        env_file=".env.$env"
        if [[ ! -f "$env_file" ]]; then
            env_file=".env"
        fi
    fi

    if [[ ! -f "$env_file" ]]; then
        warn "Environment file not found: $env_file"
        warn "Using default configuration"
        return 1
    fi

    export ENV_FILE="$env_file"
    log "Using environment file: $env_file"
    return 0
}

# Build Docker images
build_images() {
    local compose_file="$1"
    local build_args=""

    if [[ "$NO_CACHE" == "true" ]]; then
        build_args="--no-cache"
    fi

    log "Building Docker images for $ENVIRONMENT environment..."

    if [[ "$VERBOSE" == "true" ]]; then
        docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" build $build_args
    else
        docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" build $build_args > /dev/null 2>&1
    fi

    log "Docker images built successfully"
}

# Start services
start_services() {
    local compose_file="$1"
    local scale_args=""

    if [[ -n "$SCALE" ]]; then
        scale_args="--scale app=$SCALE"
    fi

    log "Starting services for $ENVIRONMENT environment..."

    if [[ "$BUILD" == "true" ]]; then
        build_images "$compose_file"
    fi

    docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" up -d $scale_args

    log "Services started successfully"

    # Show service status
    show_status "$compose_file"
}

# Stop services
stop_services() {
    local compose_file="$1"

    log "Stopping services for $ENVIRONMENT environment..."

    docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" down

    log "Services stopped successfully"
}

# Restart services
restart_services() {
    local compose_file="$1"

    log "Restarting services for $ENVIRONMENT environment..."

    docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" restart

    log "Services restarted successfully"

    # Show service status
    show_status "$compose_file"
}

# Show logs
show_logs() {
    local compose_file="$1"

    info "Showing logs for $ENVIRONMENT environment..."

    docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" logs -f
}

# Show service status
show_status() {
    local compose_file="$1"

    info "Service status for $ENVIRONMENT environment:"

    docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" ps
}

# Pull latest images
pull_images() {
    local compose_file="$1"

    log "Pulling latest images for $ENVIRONMENT environment..."

    docker-compose -f "$compose_file" -p "$COMPOSE_PROJECT_NAME-$ENVIRONMENT" pull

    log "Images pulled successfully"
}

# Backup data (production/staging only)
backup_data() {
    local env="$1"

    if [[ "$env" != "prod" && "$env" != "staging" ]]; then
        error "Backup is only supported for production and staging environments"
        exit 1
    fi

    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    log "Creating backup for $env environment..."

    # Backup database
    if docker-compose -f "$(get_compose_file "$env")" -p "$COMPOSE_PROJECT_NAME-$env" exec -T db pg_dump -U flask_user "flask_$env" > "$backup_dir/database.sql"; then
        log "Database backup created: $backup_dir/database.sql"
    else
        error "Failed to create database backup"
        exit 1
    fi

    # Backup application data
    docker-compose -f "$(get_compose_file "$env")" -p "$COMPOSE_PROJECT_NAME-$env" exec -T app tar -czf - /app/instance > "$backup_dir/app_data.tar.gz"
    log "Application data backup created: $backup_dir/app_data.tar.gz"

    log "Backup completed: $backup_dir"
}

# Restore data (production/staging only)
restore_data() {
    local env="$1"

    if [[ "$env" != "prod" && "$env" != "staging" ]]; then
        error "Restore is only supported for production and staging environments"
        exit 1
    fi

    error "Restore functionality not implemented yet"
    error "Please restore manually from backup files"
    exit 1
}

# Confirm action for production
confirm_production_action() {
    if [[ "$ENVIRONMENT" == "prod" && "$FORCE" != "true" ]]; then
        warn "You are about to perform '$ACTION' on PRODUCTION environment!"
        read -p "Are you sure? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            info "Operation cancelled"
            exit 0
        fi
    fi
}

# Main function
main() {
    cd "$PROJECT_ROOT"

    parse_args "$@"
    validate_environment

    local compose_file
    compose_file=$(get_compose_file "$ENVIRONMENT")

    if [[ ! -f "$compose_file" ]]; then
        error "Docker compose file not found: $compose_file"
        exit 1
    fi

    check_env_file "$ENVIRONMENT"
    confirm_production_action

    log "Executing '$ACTION' for '$ENVIRONMENT' environment"

    case "$ACTION" in
        up)
            start_services "$compose_file"
            ;;
        down)
            stop_services "$compose_file"
            ;;
        restart)
            restart_services "$compose_file"
            ;;
        logs)
            show_logs "$compose_file"
            ;;
        status)
            show_status "$compose_file"
            ;;
        build)
            build_images "$compose_file"
            ;;
        pull)
            pull_images "$compose_file"
            ;;
        backup)
            backup_data "$ENVIRONMENT"
            ;;
        restore)
            restore_data "$ENVIRONMENT"
            ;;
        *)
            error "Unknown action: $ACTION"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

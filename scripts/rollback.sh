#!/bin/bash

# Flask API Template - Deployment Rollback Script
# This script handles rollback operations for different environments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/rollback-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
Flask API Template - Rollback Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Target environment (development|acceptance|production)
    -v, --version VERSION    Version to rollback to (e.g., v1.2.3)
    -t, --target TARGET      Rollback target (previous|specific|backup)
    -f, --force             Force rollback without confirmation
    -d, --dry-run           Show what would be done without executing
    -h, --help              Show this help message

EXAMPLES:
    $0 -e production -t previous
    $0 -e acceptance -v v1.2.3
    $0 -e development -t backup -f
    $0 -e production -d

ENVIRONMENT VARIABLES:
    KUBECONFIG              Path to Kubernetes config (for k8s deployments)
    DOCKER_HOST             Docker daemon host (for Docker deployments)
    ROLLBACK_TIMEOUT        Timeout for rollback operations (default: 300s)

EOF
}

# Parse command line arguments
parse_args() {
    ENVIRONMENT=""
    VERSION=""
    TARGET="previous"
    FORCE=false
    DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -t|--target)
                TARGET="$2"
                shift 2
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$ENVIRONMENT" ]]; then
        error "Environment is required"
        show_help
        exit 1
    fi

    if [[ ! "$ENVIRONMENT" =~ ^(development|acceptance|production)$ ]]; then
        error "Invalid environment: $ENVIRONMENT"
        exit 1
    fi

    if [[ "$TARGET" == "specific" && -z "$VERSION" ]]; then
        error "Version is required when target is 'specific'"
        exit 1
    fi
}

# Get current deployment info
get_current_deployment() {
    log "Getting current deployment information for $ENVIRONMENT..."

    case "$DEPLOYMENT_TYPE" in
        kubernetes)
            CURRENT_IMAGE=$(kubectl get deployment flask-api-template -n "$ENVIRONMENT" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "unknown")
            ;;
        docker-compose)
            CURRENT_IMAGE=$(docker-compose -f "docker-compose.$ENVIRONMENT.yml" images -q flask-api-template 2>/dev/null || echo "unknown")
            ;;
        *)
            CURRENT_IMAGE="unknown"
            ;;
    esac

    log "Current deployment: $CURRENT_IMAGE"
}

# Get rollback target
get_rollback_target() {
    log "Determining rollback target..."

    case "$TARGET" in
        previous)
            # Get previous deployment from history
            case "$DEPLOYMENT_TYPE" in
                kubernetes)
                    ROLLBACK_IMAGE=$(kubectl rollout history deployment/flask-api-template -n "$ENVIRONMENT" --revision=1 | grep -o 'ghcr.io/[^[:space:]]*' | head -1 || echo "")
                    ;;
                docker-compose)
                    # For Docker Compose, we'd need to maintain our own history
                    ROLLBACK_IMAGE=$(cat "$PROJECT_ROOT/.deployment-history/$ENVIRONMENT" 2>/dev/null | tail -2 | head -1 || echo "")
                    ;;
            esac
            ;;
        specific)
            ROLLBACK_IMAGE="ghcr.io/$GITHUB_REPOSITORY:$VERSION"
            ;;
        backup)
            # Get latest backup
            ROLLBACK_IMAGE=$(cat "$PROJECT_ROOT/.deployment-backup/$ENVIRONMENT" 2>/dev/null || echo "")
            ;;
    esac

    if [[ -z "$ROLLBACK_IMAGE" ]]; then
        error "Could not determine rollback target"
        exit 1
    fi

    log "Rollback target: $ROLLBACK_IMAGE"
}

# Validate rollback target
validate_rollback_target() {
    log "Validating rollback target..."

    # Check if image exists
    if ! docker manifest inspect "$ROLLBACK_IMAGE" >/dev/null 2>&1; then
        error "Rollback image does not exist: $ROLLBACK_IMAGE"
        exit 1
    fi

    # Check if it's different from current
    if [[ "$CURRENT_IMAGE" == "$ROLLBACK_IMAGE" ]]; then
        warning "Rollback target is the same as current deployment"
        if [[ "$FORCE" != true ]]; then
            error "Use --force to proceed anyway"
            exit 1
        fi
    fi

    success "Rollback target validated"
}

# Create backup before rollback
create_backup() {
    log "Creating backup before rollback..."

    BACKUP_DIR="$PROJECT_ROOT/.deployment-backup"
    mkdir -p "$BACKUP_DIR"

    # Save current deployment info
    echo "$CURRENT_IMAGE" > "$BACKUP_DIR/$ENVIRONMENT"
    echo "$(date): $CURRENT_IMAGE" >> "$BACKUP_DIR/$ENVIRONMENT.history"

    # Backup database if configured
    if [[ -n "${DATABASE_BACKUP_ENABLED:-}" ]]; then
        log "Creating database backup..."
        # Database backup logic would go here
        # pg_dump, mysqldump, etc.
    fi

    success "Backup created"
}

# Perform rollback
perform_rollback() {
    log "Starting rollback to $ROLLBACK_IMAGE..."

    if [[ "$DRY_RUN" == true ]]; then
        log "DRY RUN: Would rollback $ENVIRONMENT to $ROLLBACK_IMAGE"
        return 0
    fi

    case "$DEPLOYMENT_TYPE" in
        kubernetes)
            rollback_kubernetes
            ;;
        docker-compose)
            rollback_docker_compose
            ;;
        *)
            error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
}

# Kubernetes rollback
rollback_kubernetes() {
    log "Performing Kubernetes rollback..."

    # Update deployment image
    kubectl set image deployment/flask-api-template flask-api-template="$ROLLBACK_IMAGE" -n "$ENVIRONMENT"

    # Wait for rollout to complete
    kubectl rollout status deployment/flask-api-template -n "$ENVIRONMENT" --timeout=300s

    success "Kubernetes rollback completed"
}

# Docker Compose rollback
rollback_docker_compose() {
    log "Performing Docker Compose rollback..."

    # Update environment variable for image
    export FLASK_API_IMAGE="$ROLLBACK_IMAGE"

    # Pull new image
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" pull flask-api-template

    # Recreate container
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" up -d flask-api-template

    success "Docker Compose rollback completed"
}

# Verify rollback
verify_rollback() {
    log "Verifying rollback..."

    # Wait for service to be ready
    sleep 30

    # Health check
    case "$ENVIRONMENT" in
        development)
            HEALTH_URL="https://dev-api.example.com/api/health"
            ;;
        acceptance)
            HEALTH_URL="https://acc-api.example.com/api/health"
            ;;
        production)
            HEALTH_URL="https://api.example.com/api/health"
            ;;
    esac

    # Perform health check
    for i in {1..10}; do
        if curl -f -s "$HEALTH_URL" >/dev/null 2>&1; then
            success "Health check passed"
            return 0
        fi
        log "Health check attempt $i/10 failed, retrying..."
        sleep 10
    done

    error "Health check failed after rollback"
    return 1
}

# Send notifications
send_notifications() {
    local status=$1

    log "Sending rollback notifications..."

    if [[ "$status" == "success" ]]; then
        MESSAGE="✅ Rollback completed successfully for $ENVIRONMENT environment to $ROLLBACK_IMAGE"
    else
        MESSAGE="❌ Rollback failed for $ENVIRONMENT environment"
    fi

    # Slack notification (if configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$MESSAGE\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi

    # Email notification (if configured)
    if [[ -n "${EMAIL_RECIPIENTS:-}" ]]; then
        echo "$MESSAGE" | mail -s "Rollback Notification - $ENVIRONMENT" "$EMAIL_RECIPIENTS" || true
    fi

    log "Notifications sent"
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    # Cleanup logic here
}

# Main function
main() {
    log "Starting rollback process..."
    log "Log file: $LOG_FILE"

    # Determine deployment type
    if command -v kubectl >/dev/null 2>&1 && [[ -n "${KUBECONFIG:-}" ]]; then
        DEPLOYMENT_TYPE="kubernetes"
    elif command -v docker-compose >/dev/null 2>&1; then
        DEPLOYMENT_TYPE="docker-compose"
    else
        error "No supported deployment tool found (kubectl or docker-compose)"
        exit 1
    fi

    log "Deployment type: $DEPLOYMENT_TYPE"

    # Confirmation prompt
    if [[ "$FORCE" != true && "$DRY_RUN" != true ]]; then
        echo
        warning "You are about to rollback $ENVIRONMENT environment"
        warning "Current: $CURRENT_IMAGE"
        warning "Target:  $ROLLBACK_IMAGE"
        echo
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Rollback cancelled by user"
            exit 0
        fi
    fi

    # Execute rollback steps
    get_current_deployment
    get_rollback_target
    validate_rollback_target

    if [[ "$DRY_RUN" != true ]]; then
        create_backup
        perform_rollback

        if verify_rollback; then
            success "Rollback completed successfully!"
            send_notifications "success"
        else
            error "Rollback verification failed!"
            send_notifications "failure"
            exit 1
        fi
    else
        log "DRY RUN completed - no changes made"
    fi

    log "Rollback process finished"
    log "Log file saved: $LOG_FILE"
}

# Trap for cleanup
trap cleanup EXIT

# Parse arguments and run main function
parse_args "$@"
main

#!/bin/bash
# Secrets management script for Flask API Template
# Helps generate and manage environment secrets securely

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="$PROJECT_ROOT/.secrets"

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
Usage: $0 [COMMAND] [OPTIONS]

Manage secrets for Flask API Template environments.

COMMANDS:
    generate ENV        Generate secrets for environment (acc, prod)
    rotate ENV          Rotate secrets for environment
    export ENV          Export secrets as environment variables
    validate ENV        Validate secrets for environment
    backup ENV          Backup secrets to encrypted file
    restore ENV FILE    Restore secrets from encrypted file

OPTIONS:
    -h, --help          Show this help message
    -f, --force         Force action without confirmation
    -o, --output FILE   Output file for export/backup

EXAMPLES:
    $0 generate prod                    # Generate production secrets
    $0 rotate acc                       # Rotate acceptance secrets
    $0 export prod -o prod.env          # Export production secrets
    $0 validate prod                    # Validate production secrets

SECURITY NOTES:
    - Secrets are stored in .secrets/ directory (git-ignored)
    - Use strong encryption for backup files
    - Rotate secrets regularly
    - Never commit secrets to version control

EOF
}

# Generate random secret
generate_secret() {
    local length="${1:-64}"
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Generate database password
generate_db_password() {
    local length="${1:-32}"
    openssl rand -base64 "$length" | tr -d "=+/\n" | cut -c1-"$length"
}

# Create secrets directory
create_secrets_dir() {
    if [[ ! -d "$SECRETS_DIR" ]]; then
        mkdir -p "$SECRETS_DIR"
        chmod 700 "$SECRETS_DIR"
        log "Created secrets directory: $SECRETS_DIR"
    fi
}

# Generate secrets for environment
generate_secrets() {
    local env="$1"
    local force="$2"

    if [[ "$env" != "acc" && "$env" != "prod" ]]; then
        error "Secret generation only supported for 'acc' and 'prod' environments"
        exit 1
    fi

    local secrets_file="$SECRETS_DIR/$env.env"

    if [[ -f "$secrets_file" && "$force" != "true" ]]; then
        warn "Secrets file already exists: $secrets_file"
        read -p "Overwrite existing secrets? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            info "Operation cancelled"
            exit 0
        fi
    fi

    create_secrets_dir

    log "Generating secrets for $env environment..."

    # Generate secrets
    local secret_key
    local jwt_secret_key
    local postgres_password
    local redis_password

    secret_key=$(generate_secret 64)
    jwt_secret_key=$(generate_secret 64)
    postgres_password=$(generate_db_password 32)
    redis_password=$(generate_db_password 32)

    # Create secrets file
    cat > "$secrets_file" << EOF
# Generated secrets for $env environment
# Generated on: $(date)
# WARNING: Keep this file secure and never commit to version control

# Application Secrets
SECRET_KEY=$secret_key
JWT_SECRET_KEY=$jwt_secret_key

# Database Secrets
POSTGRES_PASSWORD=$postgres_password

# Redis Secrets
REDIS_PASSWORD=$redis_password

# Additional secrets (set manually as needed)
# SENTRY_DSN=
# NEW_RELIC_LICENSE_KEY=
# NEW_RELIC_APP_NAME=Flask-API-Template-$env
# MAIL_USERNAME=
# MAIL_PASSWORD=
# MAIL_DEFAULT_SENDER=
# CORS_ORIGINS=
EOF

    chmod 600 "$secrets_file"

    log "Secrets generated successfully: $secrets_file"
    warn "Please review and update additional secrets manually"
    warn "Remember to set these secrets in your deployment environment"
}

# Rotate secrets for environment
rotate_secrets() {
    local env="$1"
    local force="$2"

    if [[ "$env" != "acc" && "$env" != "prod" ]]; then
        error "Secret rotation only supported for 'acc' and 'prod' environments"
        exit 1
    fi

    local secrets_file="$SECRETS_DIR/$env.env"

    if [[ ! -f "$secrets_file" ]]; then
        error "Secrets file not found: $secrets_file"
        error "Run 'generate $env' first"
        exit 1
    fi

    if [[ "$force" != "true" ]]; then
        warn "This will rotate all secrets for $env environment"
        warn "Make sure to update your deployment after rotation"
        read -p "Continue with secret rotation? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            info "Operation cancelled"
            exit 0
        fi
    fi

    # Backup current secrets
    local backup_file="$SECRETS_DIR/$env.env.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$secrets_file" "$backup_file"
    log "Current secrets backed up to: $backup_file"

    # Generate new secrets
    generate_secrets "$env" "true"

    log "Secrets rotated successfully"
    warn "Update your deployment with new secrets"
    warn "Old secrets backed up to: $backup_file"
}

# Export secrets as environment variables
export_secrets() {
    local env="$1"
    local output_file="$2"

    local secrets_file="$SECRETS_DIR/$env.env"

    if [[ ! -f "$secrets_file" ]]; then
        error "Secrets file not found: $secrets_file"
        error "Run 'generate $env' first"
        exit 1
    fi

    if [[ -n "$output_file" ]]; then
        log "Exporting secrets to: $output_file"

        # Create export file with proper format
        {
            echo "# Environment secrets for $env"
            echo "# Generated on: $(date)"
            echo "# Source these variables in your deployment environment"
            echo ""
            grep -v '^#' "$secrets_file" | grep -v '^$' | while IFS='=' read -r key value; do
                echo "export $key='$value'"
            done
        } > "$output_file"

        chmod 600 "$output_file"
        log "Secrets exported to: $output_file"
    else
        log "Exporting secrets for $env environment:"
        echo ""
        grep -v '^#' "$secrets_file" | grep -v '^$' | while IFS='=' read -r key value; do
            echo "export $key='$value'"
        done
    fi
}

# Validate secrets for environment
validate_secrets() {
    local env="$1"

    local secrets_file="$SECRETS_DIR/$env.env"

    if [[ ! -f "$secrets_file" ]]; then
        error "Secrets file not found: $secrets_file"
        error "Run 'generate $env' first"
        exit 1
    fi

    log "Validating secrets for $env environment..."

    local errors=0

    # Check required secrets
    local required_secrets=("SECRET_KEY" "JWT_SECRET_KEY" "POSTGRES_PASSWORD" "REDIS_PASSWORD")

    for secret in "${required_secrets[@]}"; do
        if ! grep -q "^$secret=" "$secrets_file"; then
            error "Missing required secret: $secret"
            errors=$((errors + 1))
        else
            local value
            value=$(grep "^$secret=" "$secrets_file" | cut -d'=' -f2-)
            if [[ -z "$value" ]]; then
                error "Empty value for secret: $secret"
                errors=$((errors + 1))
            elif [[ ${#value} -lt 16 ]]; then
                warn "Secret $secret is shorter than recommended (16+ characters)"
            fi
        fi
    done

    # Check file permissions
    local file_perms
    file_perms=$(stat -c "%a" "$secrets_file" 2>/dev/null || stat -f "%A" "$secrets_file" 2>/dev/null)
    if [[ "$file_perms" != "600" ]]; then
        warn "Secrets file has incorrect permissions: $file_perms (should be 600)"
    fi

    if [[ $errors -eq 0 ]]; then
        log "Secrets validation passed"
    else
        error "Secrets validation failed with $errors errors"
        exit 1
    fi
}

# Backup secrets to encrypted file
backup_secrets() {
    local env="$1"
    local output_file="$2"

    local secrets_file="$SECRETS_DIR/$env.env"

    if [[ ! -f "$secrets_file" ]]; then
        error "Secrets file not found: $secrets_file"
        exit 1
    fi

    if [[ -z "$output_file" ]]; then
        output_file="$env-secrets-backup-$(date +%Y%m%d_%H%M%S).enc"
    fi

    log "Creating encrypted backup of $env secrets..."

    # Create encrypted backup using OpenSSL
    if openssl enc -aes-256-cbc -salt -in "$secrets_file" -out "$output_file"; then
        log "Encrypted backup created: $output_file"
        warn "Store the backup file and password securely"
    else
        error "Failed to create encrypted backup"
        exit 1
    fi
}

# Restore secrets from encrypted file
restore_secrets() {
    local env="$1"
    local backup_file="$2"

    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi

    local secrets_file="$SECRETS_DIR/$env.env"

    if [[ -f "$secrets_file" ]]; then
        warn "Secrets file already exists: $secrets_file"
        read -p "Overwrite existing secrets? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            info "Operation cancelled"
            exit 0
        fi
    fi

    create_secrets_dir

    log "Restoring secrets from encrypted backup..."

    # Decrypt backup file
    if openssl enc -aes-256-cbc -d -in "$backup_file" -out "$secrets_file"; then
        chmod 600 "$secrets_file"
        log "Secrets restored successfully: $secrets_file"
    else
        error "Failed to restore secrets from backup"
        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    COMMAND=""
    ENVIRONMENT=""
    FORCE=false
    OUTPUT_FILE=""
    BACKUP_FILE=""

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
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            generate|rotate|export|validate|backup|restore)
                COMMAND="$1"
                shift
                ;;
            acc|prod)
                ENVIRONMENT="$1"
                shift
                ;;
            *)
                if [[ "$COMMAND" == "restore" && -z "$BACKUP_FILE" ]]; then
                    BACKUP_FILE="$1"
                else
                    error "Unknown option: $1"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Main function
main() {
    cd "$PROJECT_ROOT"

    parse_args "$@"

    if [[ -z "$COMMAND" ]]; then
        error "No command specified"
        usage
        exit 1
    fi

    if [[ -z "$ENVIRONMENT" ]]; then
        error "No environment specified"
        usage
        exit 1
    fi

    case "$COMMAND" in
        generate)
            generate_secrets "$ENVIRONMENT" "$FORCE"
            ;;
        rotate)
            rotate_secrets "$ENVIRONMENT" "$FORCE"
            ;;
        export)
            export_secrets "$ENVIRONMENT" "$OUTPUT_FILE"
            ;;
        validate)
            validate_secrets "$ENVIRONMENT"
            ;;
        backup)
            backup_secrets "$ENVIRONMENT" "$OUTPUT_FILE"
            ;;
        restore)
            if [[ -z "$BACKUP_FILE" ]]; then
                error "Backup file required for restore command"
                usage
                exit 1
            fi
            restore_secrets "$ENVIRONMENT" "$BACKUP_FILE"
            ;;
        *)
            error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

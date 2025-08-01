#!/bin/bash
# Docker health check script for Flask API Template
# This script performs comprehensive health checks for the application

set -e

# Configuration
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-http://localhost:5001/api/health}"
TIMEOUT="${TIMEOUT:-10}"
MAX_RETRIES="${MAX_RETRIES:-3}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${2:-$GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Error logging function
error() {
    log "$1" "$RED" >&2
}

# Warning logging function
warn() {
    log "$1" "$YELLOW"
}

# Check if curl is available
if ! command -v curl &> /dev/null; then
    error "curl is not available. Installing..."
    if command -v apk &> /dev/null; then
        apk add --no-cache curl
    elif command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y curl
    else
        error "Cannot install curl. Package manager not found."
        exit 1
    fi
fi

# Function to check HTTP endpoint
check_http_endpoint() {
    local endpoint="$1"
    local expected_status="${2:-200}"
    local timeout="${3:-$TIMEOUT}"

    log "Checking HTTP endpoint: $endpoint"

    local response
    local http_code

    response=$(curl -s -w "%{http_code}" --max-time "$timeout" "$endpoint" || echo "000")
    http_code="${response: -3}"

    if [[ "$http_code" == "$expected_status" ]]; then
        log "✓ HTTP endpoint is healthy (status: $http_code)"
        return 0
    else
        error "✗ HTTP endpoint is unhealthy (status: $http_code)"
        return 1
    fi
}

# Function to check database connectivity (if DATABASE_URL is set)
check_database() {
    if [[ -n "$DATABASE_URL" ]]; then
        log "Checking database connectivity..."

        # Try to connect using Python
        python3 -c "
import os
import sys
from urllib.parse import urlparse

try:
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgresql://'):
        import psycopg2
        conn = psycopg2.connect(database_url)
        conn.close()
        print('✓ Database connection successful')
    elif database_url.startswith('sqlite://'):
        import sqlite3
        db_path = database_url.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.close()
        print('✓ Database connection successful')
    else:
        print('? Database type not recognized, skipping check')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
" || return 1
    else
        warn "DATABASE_URL not set, skipping database check"
    fi
}

# Function to check Redis connectivity (if REDIS_URL is set)
check_redis() {
    if [[ -n "$REDIS_URL" ]]; then
        log "Checking Redis connectivity..."

        # Extract Redis connection details
        local redis_host redis_port redis_password
        redis_host=$(echo "$REDIS_URL" | sed -n 's|redis://\([^:]*\).*|\1|p')
        redis_port=$(echo "$REDIS_URL" | sed -n 's|redis://[^:]*:\([0-9]*\).*|\1|p')
        redis_password=$(echo "$REDIS_URL" | sed -n 's|redis://[^@]*@\([^:]*\).*|\1|p')

        redis_host="${redis_host:-localhost}"
        redis_port="${redis_port:-6379}"

        if [[ -n "$redis_password" ]]; then
            redis-cli -h "$redis_host" -p "$redis_port" -a "$redis_password" ping > /dev/null 2>&1 || return 1
        else
            redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1 || return 1
        fi

        log "✓ Redis connection successful"
    else
        warn "REDIS_URL not set, skipping Redis check"
    fi
}

# Function to check disk space
check_disk_space() {
    log "Checking disk space..."

    local usage
    usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [[ "$usage" -gt 90 ]]; then
        error "✗ Disk usage is critical: ${usage}%"
        return 1
    elif [[ "$usage" -gt 80 ]]; then
        warn "⚠ Disk usage is high: ${usage}%"
    else
        log "✓ Disk usage is normal: ${usage}%"
    fi
}

# Function to check memory usage
check_memory() {
    log "Checking memory usage..."

    if command -v free &> /dev/null; then
        local mem_usage
        mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

        if [[ "$mem_usage" -gt 90 ]]; then
            error "✗ Memory usage is critical: ${mem_usage}%"
            return 1
        elif [[ "$mem_usage" -gt 80 ]]; then
            warn "⚠ Memory usage is high: ${mem_usage}%"
        else
            log "✓ Memory usage is normal: ${mem_usage}%"
        fi
    else
        warn "free command not available, skipping memory check"
    fi
}

# Main health check function
main() {
    log "Starting comprehensive health check..."

    local exit_code=0
    local retry_count=0

    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        log "Health check attempt $((retry_count + 1))/$MAX_RETRIES"

        # Reset exit code for this attempt
        exit_code=0

        # Check HTTP endpoint
        check_http_endpoint "$HEALTH_ENDPOINT" || exit_code=1

        # Check database connectivity
        check_database || exit_code=1

        # Check Redis connectivity
        check_redis || exit_code=1

        # Check system resources
        check_disk_space || exit_code=1
        check_memory || exit_code=1

        if [[ $exit_code -eq 0 ]]; then
            log "✓ All health checks passed!"
            exit 0
        else
            error "✗ Some health checks failed"
            retry_count=$((retry_count + 1))

            if [[ $retry_count -lt $MAX_RETRIES ]]; then
                warn "Retrying in 5 seconds..."
                sleep 5
            fi
        fi
    done

    error "Health check failed after $MAX_RETRIES attempts"
    exit 1
}

# Run main function
main "$@"

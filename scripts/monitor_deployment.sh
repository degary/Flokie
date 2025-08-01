#!/bin/bash

# Flask API Template - Deployment Monitoring Script
# This script monitors deployment health and metrics

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/deployment-monitor-$(date +%Y%m%d-%H%M%S).log"

# Default values
ENVIRONMENT=""
DURATION="300"  # 5 minutes default
INTERVAL="30"   # 30 seconds default
ALERT_THRESHOLD_ERROR_RATE="5"
ALERT_THRESHOLD_RESPONSE_TIME="2000"
ALERT_THRESHOLD_AVAILABILITY="95"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
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
Flask API Template - Deployment Monitoring Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV       Target environment (development|acceptance|production)
    -d, --duration SECONDS      Monitoring duration in seconds (default: 300)
    -i, --interval SECONDS      Check interval in seconds (default: 30)
    -t, --error-threshold PCT   Error rate alert threshold percentage (default: 5)
    -r, --response-threshold MS Response time alert threshold in ms (default: 2000)
    -a, --availability-threshold PCT Availability alert threshold percentage (default: 95)
    -c, --continuous           Run continuously until stopped
    -h, --help                 Show this help message

EXAMPLES:
    $0 -e production -d 600 -i 60
    $0 -e acceptance -c
    $0 -e development -t 10 -r 1000

EOF
}

# Parse command line arguments
parse_args() {
    CONTINUOUS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -d|--duration)
                DURATION="$2"
                shift 2
                ;;
            -i|--interval)
                INTERVAL="$2"
                shift 2
                ;;
            -t|--error-threshold)
                ALERT_THRESHOLD_ERROR_RATE="$2"
                shift 2
                ;;
            -r|--response-threshold)
                ALERT_THRESHOLD_RESPONSE_TIME="$2"
                shift 2
                ;;
            -a|--availability-threshold)
                ALERT_THRESHOLD_AVAILABILITY="$2"
                shift 2
                ;;
            -c|--continuous)
                CONTINUOUS=true
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

    if [[ -z "$ENVIRONMENT" ]]; then
        error "Environment is required"
        show_help
        exit 1
    fi

    if [[ ! "$ENVIRONMENT" =~ ^(development|acceptance|production)$ ]]; then
        error "Invalid environment: $ENVIRONMENT"
        exit 1
    fi
}

# Get environment URLs
get_environment_urls() {
    case "$ENVIRONMENT" in
        development)
            BASE_URL="https://dev-api.example.com"
            ;;
        acceptance)
            BASE_URL="https://acc-api.example.com"
            ;;
        production)
            BASE_URL="https://api.example.com"
            ;;
    esac

    HEALTH_URL="$BASE_URL/api/health"
    METRICS_URL="$BASE_URL/api/metrics"
    VERSION_URL="$BASE_URL/api/version"
}

# Check health endpoint
check_health() {
    local start_time=$(date +%s%3N)
    local http_code
    local response_time

    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")
    local end_time=$(date +%s%3N)
    response_time=$((end_time - start_time))

    if [[ "$http_code" == "200" ]]; then
        echo "healthy,$response_time"
    else
        echo "unhealthy,$response_time"
    fi
}

# Check version endpoint
check_version() {
    local version
    version=$(curl -s --max-time 5 "$VERSION_URL" 2>/dev/null | jq -r '.version // "unknown"' 2>/dev/null || echo "unknown")
    echo "$version"
}

# Get application metrics
get_metrics() {
    local metrics
    metrics=$(curl -s --max-time 10 "$METRICS_URL" 2>/dev/null || echo "{}")

    # Extract key metrics
    local requests_total=$(echo "$metrics" | jq -r '.requests_total // 0' 2>/dev/null || echo "0")
    local requests_failed=$(echo "$metrics" | jq -r '.requests_failed // 0' 2>/dev/null || echo "0")
    local avg_response_time=$(echo "$metrics" | jq -r '.avg_response_time // 0' 2>/dev/null || echo "0")
    local active_connections=$(echo "$metrics" | jq -r '.active_connections // 0' 2>/dev/null || echo "0")

    echo "$requests_total,$requests_failed,$avg_response_time,$active_connections"
}

# Calculate error rate
calculate_error_rate() {
    local total=$1
    local failed=$2

    if [[ "$total" -gt 0 ]]; then
        echo "scale=2; $failed * 100 / $total" | bc -l 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Send alert
send_alert() {
    local alert_type=$1
    local message=$2

    log "ALERT: $alert_type - $message"

    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload="{\"text\":\"🚨 $ENVIRONMENT Alert: $alert_type\\n$message\"}"
        curl -X POST -H 'Content-type: application/json' \
            --data "$payload" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi

    # Email notification
    if [[ -n "${EMAIL_RECIPIENTS:-}" ]]; then
        echo "$message" | mail -s "$ENVIRONMENT Alert: $alert_type" "$EMAIL_RECIPIENTS" || true
    fi

    # PagerDuty integration (if configured)
    if [[ -n "${PAGERDUTY_INTEGRATION_KEY:-}" ]]; then
        local pd_payload="{
            \"routing_key\": \"$PAGERDUTY_INTEGRATION_KEY\",
            \"event_action\": \"trigger\",
            \"payload\": {
                \"summary\": \"$alert_type in $ENVIRONMENT\",
                \"source\": \"deployment-monitor\",
                \"severity\": \"error\",
                \"custom_details\": {\"message\": \"$message\"}
            }
        }"
        curl -X POST -H 'Content-Type: application/json' \
            --data "$pd_payload" \
            "https://events.pagerduty.com/v2/enqueue" >/dev/null 2>&1 || true
    fi
}

# Monitor deployment
monitor_deployment() {
    local start_time=$(date +%s)
    local end_time=$((start_time + DURATION))
    local check_count=0
    local healthy_count=0
    local total_response_time=0
    local max_response_time=0
    local min_response_time=999999
    local error_count=0

    # Initialize metrics tracking
    local prev_requests_total=0
    local prev_requests_failed=0

    log "Starting deployment monitoring for $ENVIRONMENT"
    log "Duration: ${DURATION}s, Interval: ${INTERVAL}s"
    log "Monitoring URL: $BASE_URL"

    # Get initial version
    local current_version
    current_version=$(check_version)
    log "Current version: $current_version"

    # Create monitoring report header
    echo "timestamp,status,response_time,version,requests_total,requests_failed,error_rate,avg_response_time,active_connections" > "/tmp/monitoring-$ENVIRONMENT-$(date +%s).csv"

    while [[ $(date +%s) -lt $end_time ]] || [[ "$CONTINUOUS" == true ]]; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        check_count=$((check_count + 1))

        # Health check
        local health_result
        health_result=$(check_health)
        local health_status=$(echo "$health_result" | cut -d',' -f1)
        local response_time=$(echo "$health_result" | cut -d',' -f2)

        # Version check
        local version
        version=$(check_version)

        # Metrics check
        local metrics_result
        metrics_result=$(get_metrics)
        local requests_total=$(echo "$metrics_result" | cut -d',' -f1)
        local requests_failed=$(echo "$metrics_result" | cut -d',' -f2)
        local avg_response_time=$(echo "$metrics_result" | cut -d',' -f3)
        local active_connections=$(echo "$metrics_result" | cut -d',' -f4)

        # Calculate current error rate
        local current_error_rate
        if [[ $requests_total -gt $prev_requests_total ]]; then
            local period_total=$((requests_total - prev_requests_total))
            local period_failed=$((requests_failed - prev_requests_failed))
            current_error_rate=$(calculate_error_rate $period_total $period_failed)
        else
            current_error_rate="0"
        fi

        # Update statistics
        if [[ "$health_status" == "healthy" ]]; then
            healthy_count=$((healthy_count + 1))
        else
            error_count=$((error_count + 1))
        fi

        total_response_time=$((total_response_time + response_time))
        if [[ $response_time -gt $max_response_time ]]; then
            max_response_time=$response_time
        fi
        if [[ $response_time -lt $min_response_time ]]; then
            min_response_time=$response_time
        fi

        # Log current status
        local availability=$(echo "scale=2; $healthy_count * 100 / $check_count" | bc -l)
        log "Check $check_count: $health_status (${response_time}ms) | Error Rate: ${current_error_rate}% | Availability: ${availability}%"

        # Write to CSV
        echo "$timestamp,$health_status,$response_time,$version,$requests_total,$requests_failed,$current_error_rate,$avg_response_time,$active_connections" >> "/tmp/monitoring-$ENVIRONMENT-$(date +%s).csv"

        # Check for alerts
        if [[ "$health_status" != "healthy" ]]; then
            send_alert "Health Check Failed" "Health check failed at $timestamp. Response time: ${response_time}ms"
        fi

        if (( $(echo "$current_error_rate > $ALERT_THRESHOLD_ERROR_RATE" | bc -l) )); then
            send_alert "High Error Rate" "Error rate ${current_error_rate}% exceeds threshold ${ALERT_THRESHOLD_ERROR_RATE}% at $timestamp"
        fi

        if [[ $response_time -gt $ALERT_THRESHOLD_RESPONSE_TIME ]]; then
            send_alert "High Response Time" "Response time ${response_time}ms exceeds threshold ${ALERT_THRESHOLD_RESPONSE_TIME}ms at $timestamp"
        fi

        if (( $(echo "$availability < $ALERT_THRESHOLD_AVAILABILITY" | bc -l) )); then
            send_alert "Low Availability" "Availability ${availability}% below threshold ${ALERT_THRESHOLD_AVAILABILITY}% at $timestamp"
        fi

        # Check for version changes
        if [[ "$version" != "$current_version" ]]; then
            log "Version change detected: $current_version -> $version"
            current_version="$version"
        fi

        # Update previous metrics
        prev_requests_total=$requests_total
        prev_requests_failed=$requests_failed

        # Break if continuous mode and interrupted
        if [[ "$CONTINUOUS" == true ]]; then
            sleep "$INTERVAL"
        else
            if [[ $(date +%s) -lt $end_time ]]; then
                sleep "$INTERVAL"
            fi
        fi
    done

    # Generate final report
    generate_report $check_count $healthy_count $total_response_time $max_response_time $min_response_time $error_count
}

# Generate monitoring report
generate_report() {
    local total_checks=$1
    local healthy_checks=$2
    local total_response_time=$3
    local max_response_time=$4
    local min_response_time=$5
    local error_count=$6

    local availability=$(echo "scale=2; $healthy_checks * 100 / $total_checks" | bc -l)
    local avg_response_time=$(echo "scale=2; $total_response_time / $total_checks" | bc -l)
    local error_rate=$(echo "scale=2; $error_count * 100 / $total_checks" | bc -l)

    log "=== MONITORING REPORT ==="
    log "Environment: $ENVIRONMENT"
    log "Duration: ${DURATION}s"
    log "Total Checks: $total_checks"
    log "Successful Checks: $healthy_checks"
    log "Failed Checks: $error_count"
    log "Availability: ${availability}%"
    log "Average Response Time: ${avg_response_time}ms"
    log "Min Response Time: ${min_response_time}ms"
    log "Max Response Time: ${max_response_time}ms"
    log "Error Rate: ${error_rate}%"

    # Determine overall health
    if (( $(echo "$availability >= 99" | bc -l) )) && (( $(echo "$avg_response_time <= 1000" | bc -l) )); then
        success "Deployment is HEALTHY"
    elif (( $(echo "$availability >= 95" | bc -l) )) && (( $(echo "$avg_response_time <= 2000" | bc -l) )); then
        warning "Deployment is DEGRADED"
    else
        error "Deployment is UNHEALTHY"
    fi

    log "=========================="
}

# Cleanup function
cleanup() {
    log "Cleaning up monitoring session..."
    # Any cleanup logic here
}

# Signal handlers
handle_interrupt() {
    log "Monitoring interrupted by user"
    cleanup
    exit 0
}

# Main function
main() {
    log "Starting deployment monitoring..."
    log "Log file: $LOG_FILE"

    get_environment_urls

    # Check if required tools are available
    if ! command -v curl >/dev/null 2>&1; then
        error "curl is required but not installed"
        exit 1
    fi

    if ! command -v jq >/dev/null 2>&1; then
        warning "jq is not installed - metrics parsing may be limited"
    fi

    if ! command -v bc >/dev/null 2>&1; then
        error "bc is required but not installed"
        exit 1
    fi

    # Start monitoring
    monitor_deployment

    log "Monitoring completed"
    log "Log file saved: $LOG_FILE"
}

# Set up signal handlers
trap handle_interrupt SIGINT SIGTERM
trap cleanup EXIT

# Parse arguments and run
parse_args "$@"
main

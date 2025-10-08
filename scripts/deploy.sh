#!/bin/bash

# Carnatic Music Learning Platform - Deployment Script
# Production deployment automation with health checks and rollback capabilities

set -euo pipefail

# Configuration
PROJECT_NAME="carnatic-music-learning"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io/yourusername/carnatic-music-app}"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost/api/v1/health}"
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
        log_warning "Attempting rollback..."
        rollback_deployment
    fi
    exit 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check Docker availability
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed or not in PATH"
    fi

    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed or not in PATH"
    fi

    # Check required files
    local required_files=(
        "docker-compose.prod.yml"
        "Dockerfile"
        "requirements-v2.txt"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error_exit "Required file not found: $file"
        fi
    done

    # Check secrets directory
    if [[ ! -d "secrets" ]]; then
        log_warning "Secrets directory not found, creating..."
        mkdir -p secrets
        generate_secrets
    fi

    # Check environment variables
    local required_env_vars=(
        "POSTGRES_HOST"
        "POSTGRES_DB"
        "POSTGRES_USER"
    )

    for var in "${required_env_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_warning "Environment variable $var is not set"
        fi
    done

    log_success "Pre-deployment checks completed"
}

# Generate secrets if they don't exist
generate_secrets() {
    log_info "Generating secrets..."

    local secrets_dir="secrets"

    # Generate PostgreSQL password
    if [[ ! -f "$secrets_dir/postgres_password.txt" ]]; then
        openssl rand -base64 32 > "$secrets_dir/postgres_password.txt"
        log_success "Generated PostgreSQL password"
    fi

    # Generate Redis password
    if [[ ! -f "$secrets_dir/redis_password.txt" ]]; then
        openssl rand -base64 32 > "$secrets_dir/redis_password.txt"
        log_success "Generated Redis password"
    fi

    # Generate application secret key
    if [[ ! -f "$secrets_dir/app_secret_key.txt" ]]; then
        python3 -c "import secrets; print(secrets.token_urlsafe(32))" > "$secrets_dir/app_secret_key.txt"
        log_success "Generated application secret key"
    fi

    # Generate JWT secret key
    if [[ ! -f "$secrets_dir/jwt_secret_key.txt" ]]; then
        python3 -c "import secrets; print(secrets.token_urlsafe(32))" > "$secrets_dir/jwt_secret_key.txt"
        log_success "Generated JWT secret key"
    fi

    # Set proper permissions
    chmod 600 "$secrets_dir"/*.txt
    log_success "Set proper permissions on secrets"
}

# Database backup
backup_database() {
    log_info "Creating database backup..."

    local backup_dir="backups"
    mkdir -p "$backup_dir"

    local backup_filename="carnatic_backup_$(date +%Y%m%d_%H%M%S).sql"

    if docker-compose -f docker-compose.prod.yml exec -T carnatic-postgres pg_dump -U carnatic_user carnatic_production > "$backup_dir/$backup_filename"; then
        log_success "Database backup created: $backup_filename"

        # Keep only last 7 backups
        ls -1t "$backup_dir"/carnatic_backup_*.sql | tail -n +8 | xargs -r rm
        log_info "Cleaned up old backups"
    else
        log_warning "Database backup failed, but continuing deployment"
    fi
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."

    local image_tag="${DOCKER_REGISTRY}:${DEPLOYMENT_ENV}-$(git rev-parse --short HEAD)"

    # Build the image
    if docker build -t "$image_tag" .; then
        log_success "Docker image built successfully: $image_tag"
    else
        error_exit "Failed to build Docker image"
    fi

    # Push to registry (if registry is configured)
    if [[ "$DOCKER_REGISTRY" != "local" ]]; then
        if docker push "$image_tag"; then
            log_success "Docker image pushed successfully: $image_tag"
        else
            error_exit "Failed to push Docker image"
        fi
    fi

    # Update image tag in compose file
    export CARNATIC_IMAGE_TAG="$image_tag"
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."

    # Stop existing containers gracefully
    if docker-compose -f docker-compose.prod.yml ps -q | grep -q .; then
        log_info "Stopping existing containers..."
        docker-compose -f docker-compose.prod.yml down --timeout 30
    fi

    # Start new containers
    log_info "Starting new containers..."
    if docker-compose -f docker-compose.prod.yml up -d; then
        log_success "Containers started successfully"
    else
        error_exit "Failed to start containers"
    fi

    # Wait for services to be ready
    wait_for_services
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."

    local max_attempts=60
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if docker-compose -f docker-compose.prod.yml ps | grep -q "Up (healthy)"; then
            log_success "Services are healthy"
            return 0
        fi

        log_info "Waiting for services... (attempt $((attempt + 1))/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    error_exit "Services failed to become healthy within timeout"
}

# Health check
health_check() {
    log_info "Running health checks..."

    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
            log_success "Health check passed"

            # Detailed health check
            local health_response
            if health_response=$(curl -s "$HEALTH_CHECK_URL"); then
                log_info "Health check response: $health_response"
            fi

            return 0
        fi

        log_info "Health check failed, retrying... (attempt $((attempt + 1))/$max_attempts)"
        sleep 5
        ((attempt++))
    done

    error_exit "Health check failed after $max_attempts attempts"
}

# Performance validation
performance_validation() {
    log_info "Running performance validation..."

    # Basic performance test
    local response_time
    if response_time=$(curl -w "%{time_total}" -o /dev/null -s "$HEALTH_CHECK_URL"); then
        if (( $(echo "$response_time < 1.0" | bc -l) )); then
            log_success "Performance validation passed (${response_time}s)"
        else
            log_warning "Performance validation warning: slow response (${response_time}s)"
        fi
    else
        log_warning "Performance validation failed"
    fi

    # Check resource usage
    log_info "Checking container resource usage..."
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose -f docker-compose.prod.yml ps -q)
}

# Smoke tests
smoke_tests() {
    log_info "Running smoke tests..."

    local endpoints=(
        "/"
        "/carnatic"
        "/api/v1/health"
    )

    local failed_tests=0

    for endpoint in "${endpoints[@]}"; do
        local url="${HEALTH_CHECK_URL%/api/v1/health}$endpoint"

        if curl -f -s "$url" > /dev/null; then
            log_success "Smoke test passed: $endpoint"
        else
            log_error "Smoke test failed: $endpoint"
            ((failed_tests++))
        fi
    done

    if [[ $failed_tests -gt 0 ]]; then
        error_exit "$failed_tests smoke tests failed"
    fi

    log_success "All smoke tests passed"
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."

    # Get the previous image tag from backup
    local previous_tag_file="backups/previous_image_tag.txt"

    if [[ -f "$previous_tag_file" ]]; then
        local previous_tag=$(cat "$previous_tag_file")
        log_info "Rolling back to previous image: $previous_tag"

        # Update image tag and redeploy
        export CARNATIC_IMAGE_TAG="$previous_tag"

        docker-compose -f docker-compose.prod.yml down --timeout 30
        docker-compose -f docker-compose.prod.yml up -d

        if wait_for_services && health_check; then
            log_success "Rollback successful"
        else
            log_error "Rollback failed"
        fi
    else
        log_error "No previous image tag found for rollback"
    fi
}

# Save current deployment state
save_deployment_state() {
    local backup_dir="backups"
    mkdir -p "$backup_dir"

    # Save current image tag for potential rollback
    if [[ -n "${CARNATIC_IMAGE_TAG:-}" ]]; then
        echo "$CARNATIC_IMAGE_TAG" > "$backup_dir/previous_image_tag.txt"
    fi

    # Save deployment timestamp
    date > "$backup_dir/last_deployment.txt"

    log_success "Deployment state saved"
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."

    # Remove unused Docker images
    docker image prune -f --filter="label=carnatic.version<v2.0"

    # Remove unused volumes (be careful with this)
    # docker volume prune -f --filter="label=carnatic.cleanup=true"

    log_success "Cleanup completed"
}

# Send deployment notification
send_notification() {
    local status="$1"
    local message="$2"

    log_info "Sending deployment notification..."

    # Webhook notification (customize as needed)
    if [[ -n "${WEBHOOK_URL:-}" ]]; then
        curl -X POST -H "Content-Type: application/json" \
            -d "{\"text\":\"🎵 Carnatic Music Platform Deployment\\n**Status:** $status\\n**Message:** $message\\n**Environment:** $DEPLOYMENT_ENV\\n**Time:** $(date)\"}" \
            "$WEBHOOK_URL" || log_warning "Failed to send webhook notification"
    fi

    # Email notification (if configured)
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]] && command -v mail &> /dev/null; then
        echo "Carnatic Music Platform Deployment: $status - $message" | \
            mail -s "Deployment Notification - $DEPLOYMENT_ENV" "$NOTIFICATION_EMAIL" || \
            log_warning "Failed to send email notification"
    fi
}

# Main deployment function
main() {
    log_info "🚀 Starting Carnatic Music Learning Platform deployment"
    log_info "Environment: $DEPLOYMENT_ENV"
    log_info "Registry: $DOCKER_REGISTRY"

    local start_time=$(date +%s)

    # Save current state before deployment
    save_deployment_state

    # Run deployment steps
    pre_deployment_checks
    backup_database
    build_and_push_images
    deploy_application
    health_check
    performance_validation
    smoke_tests
    cleanup

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "🎉 Deployment completed successfully in ${duration}s"
    send_notification "SUCCESS" "Deployment completed successfully in ${duration}s"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        log_info "🔄 Starting rollback process"
        rollback_deployment
        ;;
    "health-check")
        health_check
        ;;
    "backup")
        backup_database
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health-check|backup|cleanup}"
        echo ""
        echo "Commands:"
        echo "  deploy      - Full deployment process (default)"
        echo "  rollback    - Rollback to previous version"
        echo "  health-check - Run health checks only"
        echo "  backup      - Create database backup only"
        echo "  cleanup     - Clean up old resources"
        exit 1
        ;;
esac
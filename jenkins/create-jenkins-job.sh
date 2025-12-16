#!/usr/bin/env bash

###############################################################################
# Jenkins Job Creation Script for Music Multi-Arch Pipeline
#
# This script creates a Jenkins pipeline job for building and deploying
# the Carnatic Music Learning App using multi-architecture Docker builds.
#
# Prerequisites:
# - Jenkins server running at http://192.168.68.136:8081
# - Jenkins CLI jar downloaded or Jenkins API accessible
# - Valid Jenkins credentials
#
# Usage:
#   ./create-jenkins-job.sh [OPTIONS]
#
# Options:
#   -u, --username USER     Jenkins username (default: admin)
#   -p, --password PASS     Jenkins password/token
#   -j, --jenkins-url URL   Jenkins server URL (default: http://192.168.68.136:8081)
#   -n, --job-name NAME     Job name (default: music-app-build)
#   -f, --force             Delete existing job and recreate
#   -h, --help              Show this help message
#
# Examples:
#   # Create job with default settings (will prompt for password)
#   ./create-jenkins-job.sh
#
#   # Create job with credentials
#   ./create-jenkins-job.sh -u admin -p mytoken
#
#   # Recreate existing job
#   ./create-jenkins-job.sh -f -u admin -p mytoken
#
###############################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
JENKINS_URL="${JENKINS_URL:-http://192.168.68.136:8081}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_PASSWORD="${JENKINS_PASSWORD:-}"
JOB_NAME="music-app-build"
FORCE_CREATE=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
JOB_CONFIG_FILE="${SCRIPT_DIR}/job-config.xml"

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

show_help() {
    sed -n '/^###############################################################################/,/^###############################################################################/p' "$0" |
        grep -v "^###" |
        sed 's/^# //'
    exit 0
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if job config exists
    if [[ ! -f "$JOB_CONFIG_FILE" ]]; then
        log_error "Job configuration file not found: $JOB_CONFIG_FILE"
        exit 1
    fi

    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi

    log_success "Prerequisites satisfied"
}

get_crumb() {
    log_info "Getting Jenkins crumb for CSRF protection..."

    CRUMB_RESPONSE=$(curl -s -u "${JENKINS_USER}:${JENKINS_PASSWORD}" \
        "${JENKINS_URL}/crumbIssuer/api/json" 2>/dev/null || echo "")

    if [[ -z "$CRUMB_RESPONSE" ]] || [[ "$CRUMB_RESPONSE" == *"error"* ]]; then
        log_warning "Could not get crumb - Jenkins might not require CSRF protection"
        CRUMB=""
        CRUMB_HEADER=""
    else
        CRUMB=$(echo "$CRUMB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['crumb'])" 2>/dev/null || echo "")
        CRUMB_FIELD=$(echo "$CRUMB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['crumbRequestField'])" 2>/dev/null || echo "Jenkins-Crumb")
        CRUMB_HEADER="-H ${CRUMB_FIELD}: ${CRUMB}"
    fi
}

check_job_exists() {
    log_info "Checking if job '$JOB_NAME' exists..."

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -u "${JENKINS_USER}:${JENKINS_PASSWORD}" \
        "${JENKINS_URL}/job/${JOB_NAME}/api/json" 2>/dev/null || echo "000")

    if [[ "$RESPONSE" == "200" ]]; then
        return 0  # Job exists
    else
        return 1  # Job doesn't exist
    fi
}

delete_job() {
    log_info "Deleting existing job '$JOB_NAME'..."

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        -u "${JENKINS_USER}:${JENKINS_PASSWORD}" \
        ${CRUMB_HEADER} \
        "${JENKINS_URL}/job/${JOB_NAME}/doDelete" 2>/dev/null || echo "000")

    if [[ "$RESPONSE" == "302" ]] || [[ "$RESPONSE" == "200" ]]; then
        log_success "Job deleted successfully"
    else
        log_error "Failed to delete job (HTTP $RESPONSE)"
        exit 1
    fi
}

create_job() {
    log_info "Creating Jenkins job '$JOB_NAME'..."

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        -u "${JENKINS_USER}:${JENKINS_PASSWORD}" \
        ${CRUMB_HEADER} \
        -H "Content-Type: application/xml" \
        --data-binary "@${JOB_CONFIG_FILE}" \
        "${JENKINS_URL}/createItem?name=${JOB_NAME}" 2>/dev/null || echo "000")

    if [[ "$RESPONSE" == "200" ]]; then
        log_success "Job created successfully!"
        log_info "Access your job at: ${JENKINS_URL}/job/${JOB_NAME}"
    else
        log_error "Failed to create job (HTTP $RESPONSE)"
        log_info "Check Jenkins logs for more details"
        exit 1
    fi
}

###############################################################################
# Parse Arguments
###############################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            JENKINS_USER="$2"
            shift 2
            ;;
        -p|--password)
            JENKINS_PASSWORD="$2"
            shift 2
            ;;
        -j|--jenkins-url)
            JENKINS_URL="$2"
            shift 2
            ;;
        -n|--job-name)
            JOB_NAME="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_CREATE=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

###############################################################################
# Main Execution
###############################################################################

log_info "Music App Jenkins Job Setup"
log_info "=============================="
log_info "Jenkins URL: $JENKINS_URL"
log_info "Job Name: $JOB_NAME"
log_info ""

# Prompt for password if not provided
if [[ -z "$JENKINS_PASSWORD" ]]; then
    log_info "Enter Jenkins password for user '$JENKINS_USER':"
    read -s JENKINS_PASSWORD
    echo ""
fi

check_prerequisites
get_crumb

if check_job_exists; then
    if [[ "$FORCE_CREATE" == "true" ]]; then
        log_warning "Job exists - force flag set, will recreate"
        delete_job
        sleep 2
        create_job
    else
        log_warning "Job '$JOB_NAME' already exists"
        log_info "Use -f/--force to delete and recreate"
        exit 0
    fi
else
    create_job
fi

log_success ""
log_success "Jenkins job setup complete!"
log_success ""
log_info "Next steps:"
log_info "1. Go to ${JENKINS_URL}/job/${JOB_NAME}"
log_info "2. Configure GitHub webhook at your repo Settings > Webhooks"
log_info "3. Add webhook URL: ${JENKINS_URL}/github-webhook/"
log_info "4. Set content type to application/json"
log_info "5. Select 'Just the push event'"
log_info ""
log_info "To manually trigger a build:"
log_info "   ${JENKINS_URL}/job/${JOB_NAME}/build"

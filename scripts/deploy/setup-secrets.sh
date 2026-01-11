#!/bin/bash

# CBSC System Secrets Setup Script
# Creates and manages Kubernetes secrets for the CBSC system

set -euo pipefail

# Default values
ENVIRONMENT=${1:-staging}
NAMESPACE="cbsc-${ENVIRONMENT}"
DRY_RUN=false
UPDATE=false
FROM_ENV=false
ENV_FILE=".env.${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Print usage
print_usage() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    dev         Setup secrets for development environment
    staging     Setup secrets for staging environment (default)
    production  Setup secrets for production environment

OPTIONS:
    --dry-run       Perform a dry run without creating secrets
    --update        Update existing secrets
    --from-env      Load secrets from environment file
    --env-file FILE Specify custom environment file
    --help, -h      Show this help message

EXAMPLES:
    $0 production --from-env
    $0 staging --update
    $0 dev --dry-run

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --update)
                UPDATE=true
                shift
                ;;
            --from-env)
                FROM_ENV=true
                shift
                ;;
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --help|-h)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
}

# Load secrets from environment file
load_env_secrets() {
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Create the file with the required secrets or run without --from-env"
        exit 1
    fi

    log_info "Loading secrets from $ENV_FILE"

    # Source the environment file
    set -a
    source "$ENV_FILE"
    set +a

    log_success "Secrets loaded from environment file"
}

# Create or update a secret
create_secret() {
    local secret_name=$1
    local secret_type=${2:-Opaque}
    shift 2
    local data_pairs=("$@")

    log_verbose "Creating secret: $secret_name"

    # Check if secret already exists
    if kubectl get secret "$secret_name" -n "$NAMESPACE" &> /dev/null; then
        if [ "$UPDATE" = false ]; then
            log_warning "Secret $secret_name already exists. Use --update to overwrite."
            return 0
        fi
        log_info "Updating existing secret: $secret_name"
    fi

    # Build kubectl command
    local cmd=("kubectl" "create" "secret" "generic" "$secret_name" "-n" "$NAMESPACE" "--type=$secret_type")

    # Add data pairs
    for pair in "${data_pairs[@]}"; do
        cmd+=("--from-literal=$pair")
    done

    if [ "$DRY_RUN" = true ]; then
        cmd+=("--dry-run=client" "-o" "yaml")
    else
        if kubectl get secret "$secret_name" -n "$NAMESPACE" &> /dev/null; then
            cmd=("kubectl" "create" "secret" "generic" "$secret_name" "-n" "$NAMESPACE" "--type=$secret_type" "--dry-run=client" "-o" "yaml" "|" "kubectl" "apply" "-f" "-")
        fi
    fi

    # Execute command
    if [ "$DRY_RUN" = true ] || [ "${cmd[0]}" = "kubectl" ] && [ "${cmd[1]}" = "create" ]; then
        "${cmd[@]}"
    else
        eval "${cmd[@]}"
    fi
}

# Create database secrets
create_database_secrets() {
    log_info "Creating database secrets..."

    # Load from environment if available
    local db_user="${POSTGRES_USER:-postgres}"
    local db_password="${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}"
    local db_name="${POSTGRES_DB:-cbsc}"
    local repl_user="${POSTGRES_REPLICATION_USER:-replicator}"
    local repl_password="${POSTGRES_REPLICATION_PASSWORD:-$(openssl rand -base64 32)}"

    # Build connection URL
    local db_url="postgresql://$db_user:$db_password@postgres:5432/$db_name"

    create_secret "postgres-secrets" \
        "POSTGRES_USER=$db_user" \
        "POSTGRES_PASSWORD=$db_password" \
        "POSTGRES_DB=$db_name" \
        "POSTGRES_REPLICATION_USER=$repl_user" \
        "POSTGRES_REPLICATION_PASSWORD=$repl_password" \
        "DATABASE_URL=$db_url"
}

# Create Redis secrets
create_redis_secrets() {
    log_info "Creating Redis secrets..."

    local redis_password="${REDIS_PASSWORD:-$(openssl rand -base64 32)}"
    local redis_url="redis://:$redis_password@redis:6379/0"

    create_secret "redis-secrets" \
        "REDIS_PASSWORD=$redis_password" \
        "REDIS_URL=$redis_url"
}

# Create JWT secrets
create_jwt_secrets() {
    log_info "Creating JWT secrets..."

    local jwt_secret="${JWT_SECRET:-$(openssl rand -hex 32)}"
    local jwt_refresh_secret="${JWT_REFRESH_SECRET:-$(openssl rand -hex 32)}"

    create_secret "jwt-secrets" \
        "JWT_SECRET=$jwt_secret" \
        "JWT_REFRESH_SECRET=$jwt_refresh_secret"
}

# Create external API secrets
create_external_api_secrets() {
    log_info "Creating external API secrets..."

    local market_api_key="${MARKET_API_KEY:-your_market_api_key}"
    local market_api_secret="${MARKET_API_SECRET:-your_market_api_secret}"
    local slack_webhook="${SLACK_WEBHOOK_URL:-https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK}"
    local smtp_password="${SMTP_PASSWORD:-your_smtp_password}"
    local aws_access_key="${AWS_ACCESS_KEY:-your_aws_access_key}"
    local aws_secret_key="${AWS_SECRET_KEY:-your_aws_secret_key}"

    create_secret "external-api-secrets" \
        "MARKET_API_KEY=$market_api_key" \
        "MARKET_API_SECRET=$market_api_secret" \
        "SLACK_WEBHOOK_URL=$slack_webhook" \
        "SMTP_PASSWORD=$smtp_password" \
        "AWS_ACCESS_KEY=$aws_access_key" \
        "AWS_SECRET_KEY=$aws_secret_key"
}

# Create Docker registry secret
create_docker_registry_secret() {
    log_info "Creating Docker registry secret..."

    local docker_username="${DOCKER_USERNAME:-}"
    local docker_password="${DOCKER_PASSWORD:-}"

    if [ -z "$docker_username" ] || [ -z "$docker_password" ]; then
        log_warning "Docker credentials not provided. Skipping registry secret creation."
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        kubectl create secret docker-registry ghcr-secret \
            -n "$NAMESPACE" \
            --docker-server=ghcr.io \
            --docker-username="$docker_username" \
            --docker-password="$docker_password" \
            --dry-run=client -o yaml
    else
        kubectl create secret docker-registry ghcr-secret \
            -n "$NAMESPACE" \
            --docker-server=ghcr.io \
            --docker-username="$docker_username" \
            --docker-password="$docker_password" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
}

# Create TLS certificates secret
create_tls_secrets() {
    log_info "Creating TLS certificates secret..."

    local tls_cert="${TLS_CERT_PATH:-}"
    local tls_key="${TLS_KEY_PATH:-}"

    if [ -z "$tls_cert" ] || [ -z "$tls_key" ]; then
        log_warning "TLS certificates not provided. Generating self-signed certificate..."

        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /tmp/tls.key -out /tmp/tls.crt \
            -subj "/CN=cbsc-${ENVIRONMENT}.com"

        tls_cert="/tmp/tls.crt"
        tls_key="/tmp/tls.key"
    fi

    if [ "$DRY_RUN" = true ]; then
        kubectl create secret tls tls-certs \
            -n "$NAMESPACE" \
            --cert="$tls_cert" \
            --key="$tls_key" \
            --dry-run=client -o yaml
    else
        kubectl create secret tls tls-certs \
            -n "$NAMESPACE" \
            --cert="$tls_cert" \
            --key="$tls_key" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
}

# Create monitoring secrets
create_monitoring_secrets() {
    log_info "Creating monitoring secrets..."

    local grafana_password="${GRAFANA_ADMIN_PASSWORD:-admin}"
    local alertmanager_webhook="${ALERTMANAGER_SLACK_WEBHOOK:-https://hooks.slack.com/services/YOUR/ALERTMANAGER/WEBHOOK}"

    create_secret "monitoring-secrets" \
        "GRAFANA_ADMIN_PASSWORD=$grafana_password" \
        "ALERTMANAGER_SLACK_WEBHOOK=$alertmanager_webhook"
}

# Save secrets to file
save_secrets_to_file() {
    if [ "$DRY_RUN" = true ]; then
        log_info "Dry run: secrets not saved to file"
        return 0
    fi

    log_info "Saving secrets to .env.${ENVIRONMENT} file..."

    # Get all secrets and save them
    {
        echo "# CBSC System Secrets for $ENVIRONMENT environment"
        echo "# Generated on $(date)"
        echo ""

        # Database secrets
        kubectl get secret postgres-secrets -n "$NAMESPACE" -o json | \
            jq -r '.data | to_entries[] | "\(.key | ascii_upcase)=\(.value | @base64d)"'

        # Redis secrets
        kubectl get secret redis-secrets -n "$NAMESPACE" -o json | \
            jq -r '.data | to_entries[] | "\(.key | ascii_upcase)=\(.value | @base64d)"'

        # JWT secrets
        kubectl get secret jwt-secrets -n "$NAMESPACE" -o json | \
            jq -r '.data | to_entries[] | "\(.key | ascii_upcase)=\(.value | @base64d)"'
    } > ".env.${ENVIRONMENT}"

    log_success "Secrets saved to .env.${ENVIRONMENT}"
}

# Main execution
main() {
    log_info "Setting up secrets for $ENVIRONMENT environment..."

    # Parse arguments
    parse_args "${@:2}"

    # Load secrets from environment file if requested
    if [ "$FROM_ENV" = true ]; then
        load_env_secrets
    fi

    # Create namespace if it doesn't exist
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace: $NAMESPACE"
        if [ "$DRY_RUN" = false ]; then
            kubectl create namespace "$NAMESPACE"
        fi
    fi

    # Create all secrets
    create_database_secrets
    create_redis_secrets
    create_jwt_secrets
    create_external_api_secrets
    create_docker_registry_secret
    create_tls_secrets
    create_monitoring_secrets

    # Save secrets to file
    if [ "$FROM_ENV" = false ]; then
        save_secrets_to_file
    fi

    log_success "Secrets setup completed for $ENVIRONMENT environment"
}

# Set verbose mode
log_verbose() {
    if [ "${VERBOSE:-false}" = "true" ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Run main function
main "$@"
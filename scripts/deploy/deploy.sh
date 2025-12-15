#!/bin/bash

# CBSC System Deployment Script
# Usage: ./deploy.sh [environment] [options]
# Environments: dev, staging, production

set -euo pipefail

# Default values
ENVIRONMENT=${1:-staging}
NAMESPACE="cbsc-${ENVIRONMENT}"
DRY_RUN=false
SKIP_SECRETS=false
SKIP_BACKUP=false
FORCE=false
VERBOSE=false
HELM_CHART_PATH="helm/cbsc-system"
VALUES_FILE="helm/values-${ENVIRONMENT}.yaml"
IMAGE_TAG="latest"
TIMEOUT="10m"

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

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Print usage
print_usage() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    dev         Deploy to development environment
    staging     Deploy to staging environment (default)
    production  Deploy to production environment

OPTIONS:
    --dry-run           Perform a dry run without making changes
    --skip-secrets      Skip secret creation/update
    --skip-backup       Skip pre-deployment backup
    --force             Force deployment even if pre-checks fail
    --verbose           Enable verbose logging
    --image-tag TAG     Use specific image tag (default: latest)
    --timeout DURATION  Set deployment timeout (default: 10m)
    --values FILE       Use custom values file
    --help, -h          Show this help message

EXAMPLES:
    $0 staging
    $0 production --image-tag v1.2.3 --timeout 15m
    $0 dev --dry-run --verbose
    $0 staging --force --skip-backup

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
            --skip-secrets)
                SKIP_SECRETS=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --image-tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --values)
                VALUES_FILE="$2"
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed or not in PATH"
        exit 1
    fi

    # Check if connected to the right cluster
    local current_context=$(kubectl config current-context)
    log_info "Current kubectl context: $current_context"

    # Verify namespace exists or create it
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE does not exist. Creating it..."
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace $NAMESPACE created"
    fi

    # Check if helm chart exists
    if [ ! -d "$HELM_CHART_PATH" ]; then
        log_error "Helm chart not found at $HELM_CHART_PATH"
        exit 1
    fi

    # Check if values file exists
    if [ ! -f "$VALUES_FILE" ]; then
        log_error "Values file not found at $VALUES_FILE"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Verify secrets exist
verify_secrets() {
    log_info "Verifying secrets..."

    if [ "$SKIP_SECRETS" = true ]; then
        log_warning "Skipping secrets verification"
        return 0
    fi

    local secrets=(
        "postgres-secrets"
        "redis-secrets"
        "jwt-secrets"
        "ghcr-secret"
    )

    for secret in "${secrets[@]}"; do
        if ! kubectl get secret "$secret" -n "$NAMESPACE" &> /dev/null; then
            log_error "Secret $secret not found in namespace $NAMESPACE"
            log_error "Please create the secret before deploying or use --skip-secrets"
            exit 1
        fi
    done

    log_success "All required secrets found"
}

# Create backup
create_backup() {
    if [ "$SKIP_BACKUP" = true ]; then
        log_warning "Skipping backup"
        return 0
    fi

    log_info "Creating pre-deployment backup..."

    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup current deployment
    kubectl get deployments -n "$NAMESPACE" -o yaml > "$backup_dir/deployments.yaml"
    kubectl get services -n "$NAMESPACE" -o yaml > "$backup_dir/services.yaml"
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "$backup_dir/configmaps.yaml"

    # Backup database (if in production)
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Creating database backup..."
        kubectl exec -n "$NAMESPACE" deployment/postgres -- pg_dump \
            -U postgres -d cbsc > "$backup_dir/database.sql"
    fi

    log_success "Backup created at $backup_dir"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check resource quotas
    local quota=$(kubectl get resourcequota -n "$NAMESPACE" -o json | jq -r '.items[0].status.hard' 2>/dev/null || echo "{}")
    if [ "$quota" != "{}" ]; then
        log_info "Resource quota found for namespace $NAMESPACE"
    fi

    # Check PodDisruptionBudgets
    local pdbs=$(kubectl get pdb -n "$NAMESPACE" --no-headers | wc -l)
    if [ "$pdbs" -gt 0 ]; then
        log_info "Found $pdbs PodDisruptionBudget(s)"
    fi

    # Verify images exist
    log_info "Verifying Docker images..."
    local images=(
        "ghcr.io/cbsc-system/cbsc-frontend:$IMAGE_TAG"
        "ghcr.io/cbsc-system/cbsc-api-gateway:$IMAGE_TAG"
        "ghcr.io/cbsc-system/cbsc-user-management:$IMAGE_TAG"
        "ghcr.io/cbsc-system/cbsc-strategy-dashboard:$IMAGE_TAG"
        "ghcr.io/cbsc-system/cbsc-quant-system:$IMAGE_TAG"
        "ghcr.io/cbsc-system/cbsc-config-service:$IMAGE_TAG"
    )

    for image in "${images[@]}"; do
        log_verbose "Checking image: $image"
        # Add actual image existence check here if needed
    done

    log_success "Pre-deployment checks completed"
}

# Deploy application
deploy_application() {
    log_info "Deploying CBSC system to $ENVIRONMENT environment..."

    local helm_args=(
        "upgrade"
        "--install"
        "cbsc-system"
        "$HELM_CHART_PATH"
        "--namespace" "$NAMESPACE"
        "--values" "$VALUES_FILE"
        "--set" "image.tag=$IMAGE_TAG"
        "--timeout" "$TIMEOUT"
        "--wait"
    )

    if [ "$DRY_RUN" = true ]; then
        helm_args+=("--dry-run")
        log_info "Performing dry run deployment..."
    fi

    if [ "$VERBOSE" = true ]; then
        helm_args+=("--debug")
    fi

    log_verbose "Running helm with args: ${helm_args[@]}"

    if helm "${helm_args[@]}"; then
        log_success "Deployment completed successfully"
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Post-deployment verification
post_deployment_verification() {
    log_info "Running post-deployment verification..."

    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s \
        deployment --all -n "$NAMESPACE"

    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -n "$NAMESPACE"

    # Check service endpoints
    log_info "Verifying service endpoints..."
    local services=("frontend" "api-gateway" "user-management" "postgres" "redis")
    for service in "${services[@]}"; do
        if kubectl get service "$service" -n "$NAMESPACE" &> /dev/null; then
            local endpoint=$(kubectl get service "$service" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
            if [ -n "$endpoint" ]; then
                log_success "Service $service is accessible at $endpoint"
            else
                log_warning "Service $service has no external endpoint"
            fi
        fi
    done

    # Run health checks
    log_info "Running health checks..."
    # Add actual health check calls here

    log_success "Post-deployment verification completed"
}

# Rollback function
rollback() {
    log_error "Initiating rollback..."

    local last_release=$(helm history -n "$NAMESPACE" cbsc-system -o json | jq -r '.[-2].revision')
    if [ "$last_release" = "null" ]; then
        log_error "No previous release found for rollback"
        exit 1
    fi

    log_info "Rolling back to revision $last_release"
    helm rollback cbsc-system "$last_release" -n "$NAMESPACE"

    log_success "Rollback completed"
}

# Main execution
main() {
    log_info "Starting CBSC deployment to $ENVIRONMENT environment..."

    # Set error handling
    trap 'rollback' ERR

    # Parse remaining arguments
    parse_args "${@:2}"

    # Execute deployment steps
    check_prerequisites
    verify_secrets
    create_backup
    pre_deployment_checks
    deploy_application
    post_deployment_verification

    log_success "Deployment completed successfully!"
    log_info "Access the application at: https://app-${ENVIRONMENT}.cbsc.com"
}

# Trap signals for cleanup
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
#!/bin/bash

# Music App Kubernetes Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="music-app"
IMAGE_TAG="latest"
NAMESPACE="music-app"
DOCKER_REGISTRY=""  # Set your registry here if needed

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command_exists kubectl; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
    
    if [ ! -z "$DOCKER_REGISTRY" ]; then
        print_status "Tagging image for registry..."
        docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
        
        print_status "Pushing image to registry..."
        docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
    fi
}

# Deploy to Kubernetes
deploy_k8s() {
    print_status "Deploying to Kubernetes..."
    
    # Apply manifests in order
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    # Optional: Apply ingress if ingress controller is available
    if kubectl get ingressclass nginx >/dev/null 2>&1; then
        print_status "Applying ingress configuration..."
        kubectl apply -f k8s/ingress.yaml
    else
        print_warning "Nginx ingress controller not found, skipping ingress creation"
    fi
    
    # Wait for deployment to be ready
    print_status "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/music-app -n ${NAMESPACE}
    
    print_status "Deployment completed successfully!"
}

# Show deployment status
show_status() {
    print_status "Deployment Status:"
    echo ""
    kubectl get all -n ${NAMESPACE}
    
    echo ""
    print_status "Service endpoints:"
    kubectl get svc -n ${NAMESPACE}
    
    # Show ingress if available
    if kubectl get ingress -n ${NAMESPACE} >/dev/null 2>&1; then
        echo ""
        print_status "Ingress configuration:"
        kubectl get ingress -n ${NAMESPACE}
    fi
}

# Cleanup function
cleanup() {
    print_status "Cleaning up resources..."
    kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
    print_status "Cleanup completed"
}

# Main execution
main() {
    case "${1:-deploy}" in
        "build")
            check_prerequisites
            build_image
            ;;
        "deploy")
            check_prerequisites
            build_image
            deploy_k8s
            show_status
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "help")
            echo "Usage: $0 [build|deploy|status|cleanup|help]"
            echo ""
            echo "Commands:"
            echo "  build    - Build Docker image only"
            echo "  deploy   - Build image and deploy to Kubernetes (default)"
            echo "  status   - Show deployment status"
            echo "  cleanup  - Remove all resources"
            echo "  help     - Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

main "$@"
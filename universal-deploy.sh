#!/bin/bash
# universal-deploy.sh - Deploy to Kubernetes, Docker, or Local

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    echo "Usage: $0 [kubernetes|docker|local|all]"
    echo ""
    echo "Options:"
    echo "  kubernetes  - Deploy to Kubernetes with monitoring"
    echo "  docker      - Deploy using Docker Compose"
    echo "  local       - Run locally for development"
    echo "  all         - Show status of all environments"
    echo ""
    echo "Examples:"
    echo "  $0 kubernetes   # Deploy to K8s"
    echo "  $0 docker       # Deploy with Docker Compose"
    echo "  $0 local        # Run local development server"
    echo "  $0 all          # Check all environments"
}

check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check if we have the GCP key
    if [ ! -f "/users/shrinidhirajagopal/Downloads/GCP_SA_Key.json" ]; then
        print_warning "GCP key file not found. Some features may not work."
    fi
    
    print_success "Prerequisites checked"
}

build_images() {
    print_status "Building Docker images..."
    
    # Build backend
    docker build -t mental-health-backend:latest .
    
    # Build frontend (with universal HTML)
    docker build -t mental-health-frontend:latest -f frontend/Dockerfile .
    
    print_success "Images built successfully"
}

deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is required for Kubernetes deployment"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    build_images
    
    # Create GCP secret
    if [ -f "/users/shrinidhirajagopal/Downloads/GCP_SA_Key.json" ]; then
        kubectl delete secret genai-secret 2>/dev/null || true
        kubectl create secret generic genai-secret \
            --from-file=api_key=/users/shrinidhirajagopal/Downloads/GCP_SA_Key.json
        print_success "GCP secret created"
    fi
    
    # Deploy monitoring stack
    print_status "Deploying monitoring stack..."
    kubectl apply -f k8s-monitoring-stack.yaml 2>/dev/null || true
    kubectl apply -f k8s-prometheus.yaml 2>/dev/null || true
    kubectl apply -f k8s-grafana-jaeger.yaml 2>/dev/null || true
    kubectl apply -f k8s-grafana-dashboard.yaml 2>/dev/null || true
    
    # Deploy application
    print_status "Deploying application..."
    kubectl apply -f k8s-mental-health-app.yaml
    
    # Wait for deployments
    print_status "Waiting for deployments..."
    kubectl wait --for=condition=available --timeout=180s deployment/mental-health-app
    kubectl wait --for=condition=available --timeout=180s deployment/mental-health-frontend
    
    # Set up port forwarding
    print_status "Setting up port forwarding..."
    pkill -f "kubectl port-forward" 2>/dev/null || true
    
    kubectl port-forward svc/backend-service 8080:80 > /dev/null 2>&1 &
    kubectl port-forward svc/frontend-service 3000:80 > /dev/null 2>&1 &
    
    # Port forward monitoring (if available)
    kubectl port-forward svc/grafana 3001:3000 -n mental-health-monitoring > /dev/null 2>&1 &
    kubectl port-forward svc/jaeger 16686:16686 -n mental-health-monitoring > /dev/null 2>&1 &
    kubectl port-forward svc/prometheus 9090:9090 -n mental-health-monitoring > /dev/null 2>&1 &
    
    sleep 5
    
    print_success " Kubernetes deployment complete!"
    echo ""
    echo "Access URLs:"
    echo "   App: http://localhost:8080"
    echo "   Grafana: http://localhost:3001 (admin/admin123)"
    echo "   Jaeger: http://localhost:16686"
    echo "   Prometheus: http://localhost:9090"
}

deploy_docker() {
    print_status "Deploying with Docker Compose..."
    
    # Check docker-compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "docker-compose is required"
        exit 1
    fi
    
    build_images
    
    # Use docker-compose
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    # Wait for services
    sleep 10
    
    print_success " Docker Compose deployment complete!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   App: http://localhost:8000"
    echo "   Grafana: http://localhost:3001 (admin/admin123)"
    echo "   Jaeger: http://localhost:16686"
}

deploy_local() {
    print_status "Setting up local development..."
    
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_status "Starting backend server..."
    export OTEL_TRACES_EXPORTER=none
    python app.py
    echo ""
    echo "Frontend will be served by the backend at:"
    echo "http://localhost:8000"
    
    print_success " Local development setup complete!"
}

check_all_environments() {
    print_status "Checking all environments..."
    echo ""
    
    # Check Kubernetes
    echo "Kubernetes:"
    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        K8S_PODS=$(kubectl get pods 2>/dev/null | grep mental-health | wc -l)
        if [ $K8S_PODS -gt 0 ]; then
            echo "   Running ($K8S_PODS pods active)"
            echo "     App: http://localhost:8080"
        else
            echo "Available but not deployed"
        fi
    else
        echo " Not available"
    fi
    
    echo ""
    
    # Check Docker
    echo "Docker Compose:"
    if command -v docker &> /dev/null; then
        DOCKER_CONTAINERS=$(docker ps | grep mental-health | wc -l)
        if [ $DOCKER_CONTAINERS -gt 0 ]; then
            echo "   Running ($DOCKER_CONTAINERS containers active)"
            echo "     App: http://localhost:8000"
        else
            echo "Available but not running"
        fi
    else
        echo "Not available"
    fi
    
    echo ""
    
    # Check Local
    echo "Local Development:"
    if [ -f "app.py" ]; then
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "   Running"
            echo "     Access: http://localhost:8000"
        else
            echo "Available but not running"
        fi
    else
        echo "app.py not found"
    fi
    
    
    # Check what's actually responding
    print_status "Testing backend connectivity..."
    
    for port in 8000 8080; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo "App responding on port $port"
        else
            echo "No backend on port $port"
        fi
    done
}

test_deployment() {
    print_status "Testing deployment..."
    
    # Test backend on multiple ports
    for port in 8000 8080; do
        if curl -s http://localhost:$port/health > /dev/null; then
            print_success "Backend responding on port $port"
            
            # Test API
            RESPONSE=$(curl -s -X POST http://localhost:$port/api/mental-health \
                -H "Content-Type: application/json" \
                -d '{"prompt": "test"}' || echo "failed")
            
            if [[ "$RESPONSE" != "failed" ]] && [[ "$RESPONSE" != *"error"* ]]; then
                print_success "API test successful on port $port"
            else
                print_warning "API test failed on port $port"
            fi
            
            break
        fi
    done
    
}

cleanup() {
    print_status "Cleaning up..."
    
    # Stop Kubernetes port forwards
    pkill -f "kubectl port-forward" 2>/dev/null || true
    
    # Stop Docker containers
    if command -v docker-compose &> /dev/null; then
        docker-compose down 2>/dev/null || true
    else
        docker compose down 2>/dev/null || true
    fi
    
    print_success "Cleanup complete"
}

# Main script logic
case "$1" in
    kubernetes|k8s)
        check_prerequisites
        deploy_kubernetes
        test_deployment
        ;;
    docker|compose)
        check_prerequisites
        deploy_docker
        test_deployment
        ;;
    local|dev)
        check_prerequisites
        deploy_local
        ;;
    all|status)
        check_all_environments
        ;;
    test)
        test_deployment
        ;;
    cleanup|clean)
        cleanup
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
#!/bin/bash

# AI Content Generation Service Deployment Script
# This script sets up and deploys the service with all dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_status "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_status "Docker Compose is installed"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    print_status "Docker daemon is running"
}

# Setup environment
setup_environment() {
    print_header "Setting Up Environment"
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        print_status "Creating .env file from template"
        cp .env.example .env
        print_warning "Please edit .env file with your actual configuration values"
        print_warning "Especially set your OPENAI_API_KEY"
    else
        print_status ".env file already exists"
    fi
    
    # Check if OpenAI API key is set
    if [[ -f .env ]]; then
        source .env
        if [[ -z "$OPENAI_API_KEY" || "$OPENAI_API_KEY" == "your_openai_api_key_here" ]]; then
            print_warning "OpenAI API key is not set properly in .env file"
            print_warning "The service will not work without a valid OpenAI API key"
        fi
    fi
    
    # Create necessary directories
    print_status "Creating necessary directories"
    mkdir -p data/raw data/processed logs nginx/ssl monitoring
    
    # Set permissions
    chmod 755 data logs
    chmod 644 .env 2>/dev/null || true
}

# Build and deploy
deploy_service() {
    print_header "Building and Deploying Service"
    
    print_status "Building Docker images..."
    docker-compose build
    
    print_status "Starting services..."
    docker-compose up -d
    
    print_status "Waiting for services to start..."
    sleep 30
    
    # Check if services are healthy
    print_status "Checking service health..."
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        print_status "Redis is healthy"
    else
        print_error "Redis health check failed"
    fi
    
    # Check AI Content Service
    if curl -f http://localhost:5000/api/health &> /dev/null; then
        print_status "AI Content Service is healthy"
    else
        print_warning "AI Content Service health check failed"
        print_warning "This might be due to missing OpenAI API key or other configuration issues"
    fi
}

# Deploy with monitoring
deploy_with_monitoring() {
    print_header "Deploying with Monitoring Stack"
    
    print_status "Creating monitoring configuration..."
    
    # Create Prometheus config
    mkdir -p monitoring
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-content-service'
    static_configs:
      - targets: ['ai-content-service:5000']
    scrape_interval: 30s
    metrics_path: '/api/metrics'
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
      
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/nginx_status'
EOF
    
    print_status "Starting services with monitoring..."
    docker-compose --profile monitoring up -d
    
    print_status "Monitoring services will be available at:"
    print_status "- Prometheus: http://localhost:9090"
    print_status "- Grafana: http://localhost:3000 (admin/admin)"
}

# Deploy production setup
deploy_production() {
    print_header "Deploying Production Setup"
    
    print_status "Starting production services with Nginx..."
    docker-compose --profile production up -d
    
    print_status "Production setup complete"
    print_status "Service will be available at: http://localhost"
    print_warning "For HTTPS, configure SSL certificates in nginx/ssl/"
}

# Show service status
show_status() {
    print_header "Service Status"
    
    echo "Docker containers:"
    docker-compose ps
    
    echo ""
    echo "Service URLs:"
    echo "- API Service: http://localhost:5000/api"
    echo "- Health Check: http://localhost:5000/api/health"
    echo "- Metrics: http://localhost:5000/api/metrics"
    echo "- Redis: localhost:6379"
    
    echo ""
    echo "API Documentation: See API_DOCUMENTATION.md"
    echo "Demo Script: python demo.py"
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    docker-compose --profile monitoring --profile production down
    print_status "All services stopped"
}

# Clean up
cleanup() {
    print_header "Cleaning Up"
    
    read -p "This will remove all containers, volumes, and data. Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose --profile monitoring --profile production down -v --remove-orphans
        docker system prune -f
        print_status "Cleanup complete"
    else
        print_status "Cleanup cancelled"
    fi
}

# Show logs
show_logs() {
    service=${1:-ai-content-service}
    print_status "Showing logs for $service (press Ctrl+C to exit)"
    docker-compose logs -f "$service"
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_root
            check_prerequisites
            setup_environment
            deploy_service
            show_status
            ;;
        "monitoring")
            check_root
            check_prerequisites
            setup_environment
            deploy_with_monitoring
            show_status
            ;;
        "production")
            check_root
            check_prerequisites
            setup_environment
            deploy_production
            show_status
            ;;
        "status")
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            show_logs $2
            ;;
        "restart")
            stop_services
            sleep 5
            deploy_service
            show_status
            ;;
        "help"|"-h"|"--help")
            echo "AI Content Generation Service Deployment Script"
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  deploy      Deploy basic service (default)"
            echo "  monitoring  Deploy with monitoring (Prometheus, Grafana)"
            echo "  production  Deploy production setup with Nginx"
            echo "  status      Show service status"
            echo "  stop        Stop all services"
            echo "  restart     Restart services"
            echo "  logs [service]  Show logs for service"
            echo "  cleanup     Remove all containers and data"
            echo "  help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 deploy           # Basic deployment"
            echo "  $0 monitoring       # Deploy with monitoring"
            echo "  $0 production       # Production deployment"
            echo "  $0 logs redis       # Show Redis logs"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
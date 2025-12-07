#!/bin/bash

# AI Content Generation Service - Quick Start Script
# This script sets up and tests the complete production-ready system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Set up environment
setup_environment() {
    log "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            warning "Created .env file from .env.example"
            warning "Please update .env file with your OpenAI API key and other settings"
        else
            error ".env.example file not found"
            exit 1
        fi
    fi
    
    # Check if OpenAI API key is set
    if grep -q "your_openai_api_key_here" .env; then
        warning "Please set your OpenAI API key in the .env file"
        warning "Edit .env and replace 'your_openai_api_key_here' with your actual API key"
        read -p "Press Enter after you've updated the .env file..."
    fi
    
    # Create necessary directories
    mkdir -p data/raw data/processed data/faiss_index logs
    
    success "Environment setup completed"
}

# Build and start services
start_services() {
    log "Building and starting services..."
    
    # Build the Docker image
    log "Building AI Content Service Docker image..."
    docker-compose build ai-content-service
    
    # Start core services (Redis + AI Service)
    log "Starting core services..."
    docker-compose up -d redis ai-content-service
    
    # Wait for services to be healthy
    log "Waiting for services to become healthy..."
    
    # Wait for Redis
    echo -n "Waiting for Redis..."
    while ! docker-compose exec redis redis-cli ping > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    success "Redis is ready"
    
    # Wait for AI Content Service
    echo -n "Waiting for AI Content Service..."
    for i in {1..30}; do
        if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
            success "AI Content Service is ready"
            break
        fi
        echo -n "."
        sleep 2
        if [ $i -eq 30 ]; then
            error "AI Content Service failed to start"
            docker-compose logs ai-content-service
            exit 1
        fi
    done
}

# Test the system
test_system() {
    log "Testing the system..."
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f http://localhost:5000/api/health; then
        success "Health check passed"
    else
        error "Health check failed"
        return 1
    fi
    
    echo ""
    
    # Test content generation (if API key is configured)
    log "Testing content generation..."
    response=$(curl -s -X POST http://localhost:5000/api/generate \
        -H "Content-Type: application/json" \
        -d '{"query": "What is artificial intelligence?", "max_length": 200}')
    
    if echo "$response" | grep -q "content"; then
        success "Content generation test passed"
        echo "Sample response: $(echo "$response" | head -c 200)..."
    else
        warning "Content generation test failed (possibly due to missing API key)"
        echo "Response: $response"
    fi
    
    echo ""
    
    # Test metrics endpoint
    log "Testing metrics endpoint..."
    if curl -f http://localhost:5000/api/metrics > /dev/null 2>&1; then
        success "Metrics endpoint test passed"
    else
        warning "Metrics endpoint test failed"
    fi
}

# Load sample data
load_sample_data() {
    log "Loading sample data..."
    
    # Create sample documents
    sample_data='[
        {
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data without being explicitly programmed. It enables computers to find patterns in data and make predictions or decisions.",
            "url": "https://example.com/ml-intro",
            "metadata": {"category": "AI", "difficulty": "beginner"}
        },
        {
            "title": "Deep Learning Fundamentals",
            "content": "Deep learning uses neural networks with multiple layers to model and understand complex patterns in data. It has revolutionized fields like computer vision, natural language processing, and speech recognition.",
            "url": "https://example.com/dl-fundamentals",
            "metadata": {"category": "AI", "difficulty": "intermediate"}
        },
        {
            "title": "Natural Language Processing",
            "content": "Natural Language Processing (NLP) is a branch of artificial intelligence that deals with the interaction between computers and human language. It involves teaching computers to understand, interpret, and generate human language.",
            "url": "https://example.com/nlp-basics",
            "metadata": {"category": "AI", "difficulty": "intermediate"}
        }
    ]'
    
    response=$(curl -s -X POST http://localhost:5000/api/ingest \
        -H "Content-Type: application/json" \
        -d "{\"documents\": $sample_data}")
    
    if echo "$response" | grep -q "processed_count"; then
        success "Sample data loaded successfully"
        echo "Response: $response"
    else
        warning "Failed to load sample data"
        echo "Response: $response"
    fi
}

# Display system information
show_system_info() {
    log "System Information:"
    echo ""
    echo "🚀 AI Content Generation Service is running!"
    echo ""
    echo "📍 Service Endpoints:"
    echo "   • Health Check: http://localhost:5000/api/health"
    echo "   • Content Generation: http://localhost:5000/api/generate"
    echo "   • Semantic Search: http://localhost:5000/api/search"
    echo "   • Document Ingestion: http://localhost:5000/api/ingest"
    echo "   • Metrics: http://localhost:5000/api/metrics"
    echo ""
    echo "📊 Optional Monitoring:"
    echo "   • Start monitoring: docker-compose --profile monitoring up -d"
    echo "   • Prometheus: http://localhost:9090"
    echo "   • Grafana: http://localhost:3000 (admin/admin)"
    echo ""
    echo "🔧 Management Commands:"
    echo "   • View logs: docker-compose logs -f ai-content-service"
    echo "   • Stop services: docker-compose down"
    echo "   • Restart: docker-compose restart ai-content-service"
    echo ""
    echo "📖 API Documentation: See docs/API.md for detailed usage examples"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start     Start the AI Content Generation Service"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  test      Run system tests"
    echo "  logs      Show service logs"
    echo "  status    Show service status"
    echo "  clean     Clean up containers and volumes"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start          # Start the service"
    echo "  $0 test           # Test the running service"
    echo "  $0 logs           # View service logs"
}

# Main execution
case "${1:-start}" in
    start)
        log "Starting AI Content Generation Service..."
        check_prerequisites
        setup_environment
        start_services
        load_sample_data
        test_system
        show_system_info
        ;;
    
    stop)
        log "Stopping services..."
        docker-compose down
        success "Services stopped"
        ;;
    
    restart)
        log "Restarting services..."
        docker-compose restart
        success "Services restarted"
        ;;
    
    test)
        log "Running system tests..."
        test_system
        ;;
    
    logs)
        log "Showing service logs..."
        docker-compose logs -f ai-content-service
        ;;
    
    status)
        log "Service status:"
        docker-compose ps
        ;;
    
    clean)
        log "Cleaning up..."
        warning "This will remove all containers and data volumes!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --remove-orphans
            docker system prune -f
            success "Cleanup completed"
        else
            log "Cleanup cancelled"
        fi
        ;;
    
    help|--help|-h)
        show_usage
        ;;
    
    *)
        error "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac
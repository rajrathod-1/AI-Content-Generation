#!/bin/bash

# AI Content Generation Service - Python Direct Start
# Runs the service without Docker

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting AI Content Generation Service (Python Mode)${NC}"
echo "=================================================================="

# Check if we're in the right directory
if [[ ! -f "app.py" ]]; then
    echo -e "${RED}❌ Please run this script from the ai-content-generation-service directory${NC}"
    exit 1
fi

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your OpenAI API key${NC}"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check Redis
echo -e "${GREEN}🔍 Checking Redis...${NC}"
if ! command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis not found. Installing with Homebrew...${NC}"
    if command -v brew &> /dev/null; then
        brew install redis
    else
        echo -e "${RED}❌ Please install Redis manually or install Homebrew first${NC}"
        echo "   Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "   Then run: brew install redis"
        exit 1
    fi
fi

# Start Redis if not running
if ! redis-cli ping &> /dev/null; then
    echo -e "${GREEN}🚀 Starting Redis...${NC}"
    brew services start redis
    sleep 2
    
    # Check if Redis started
    if ! redis-cli ping &> /dev/null; then
        echo -e "${YELLOW}⚠️  Starting Redis manually...${NC}"
        redis-server --daemonize yes
        sleep 2
    fi
fi

if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Could not start Redis${NC}"
    exit 1
fi

# Create directories
echo -e "${GREEN}📁 Creating directories...${NC}"
mkdir -p data/raw data/processed logs

# Install Python dependencies
echo -e "${GREEN}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" .env 2>/dev/null; then
    echo -e "${RED}❌ Please set your OpenAI API key in .env file${NC}"
    echo "   Edit .env and replace 'your_openai_api_key_here' with your actual API key"
    exit 1
fi

echo -e "${GREEN}✅ Configuration looks good${NC}"

# Start the service
echo -e "${GREEN}🚀 Starting AI Content Generation Service...${NC}"
echo "=================================================================="
echo -e "${GREEN}📍 Service will be available at:${NC}"
echo "   • Health Check: http://localhost:5000/api/health"
echo "   • API Docs: See API_DOCUMENTATION.md"
echo "   • Demo: python demo.py (run in another terminal)"
echo "=================================================================="

# Set environment
export FLASK_ENV=development
export PYTHONPATH="$(pwd)"

# Start the Flask app
python app.py
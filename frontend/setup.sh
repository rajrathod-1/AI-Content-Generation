#!/bin/bash

# RAG Frontend Setup Script
echo "🚀 Setting up RAG Content Generator Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) found"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Frontend Environment Variables
VITE_API_BASE_URL=http://localhost:5000/api
VITE_APP_TITLE=RAG Content Generator
VITE_APP_DESCRIPTION=Advanced AI with Retrieval-Augmented Generation
EOL
    echo "✅ .env file created"
fi

echo ""
echo "🎉 Setup complete! You can now:"
echo ""
echo "   Start development server:"
echo "   npm run dev"
echo ""
echo "   Build for production:"
echo "   npm run build"
echo ""
echo "   Preview production build:"
echo "   npm run preview"
echo ""
echo "📝 Make sure your backend service is running on port 5000"
echo "🌐 Frontend will be available at http://localhost:3000"
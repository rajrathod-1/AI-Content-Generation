# RAG Content Generator Frontend

A professional React frontend for the RAG-powered AI content generation service. This application showcases the power of Retrieval-Augmented Generation technology with a beautiful, modern interface that impresses recruiters and demonstrates advanced AI capabilities.

## 🚀 Features

- **Interactive Chat Interface**: Real-time conversations with RAG-powered AI
- **Educational Content**: Comprehensive explanation of RAG technology vs ChatGPT
- **Performance Metrics**: Real-time monitoring dashboard
- **Source Citations**: Transparent source attribution for all generated content
- **Responsive Design**: Beautiful UI that works on all devices
- **Professional Styling**: Tailwind CSS with custom animations

## 🛠️ Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **React Router** for navigation
- **Axios** for API communication
- **React Hot Toast** for notifications

## 📋 Prerequisites

- Node.js 16+ and npm/yarn
- Backend RAG service running on port 5000

## 🔧 Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

## 🌐 Backend Integration

The frontend is configured to proxy API requests to the backend service:

- Development: `http://localhost:5000/api`
- All API calls are automatically proxied through Vite dev server

## 📱 Pages Overview

### Home Page (`/`)
- Hero section with compelling value proposition
- Feature comparison: RAG vs Standard ChatGPT
- Call-to-action sections
- Professional design to impress recruiters

### Chat Page (`/chat`)
- Interactive chat interface
- Real-time message streaming
- Source citations display
- Performance metrics for each response
- Professional conversation UI

### About Page (`/about`)
- Comprehensive RAG technology explanation
- 5-step process visualization
- Technical architecture details
- Comparison tables and benefits

### Metrics Page (`/metrics`)
- Real-time system performance monitoring
- Request/response analytics
- System health indicators
- Interactive charts and visualizations

## 🎨 Design Philosophy

This frontend is designed to:
- **Impress Recruiters**: Professional, modern design with smooth animations
- **Educate Users**: Clear explanations of complex RAG concepts
- **Demonstrate Technical Skills**: Advanced React patterns and modern tooling
- **Showcase AI Capabilities**: Interactive features that highlight RAG advantages

## 🔄 API Integration

The frontend integrates with the following backend endpoints:

- `POST /api/generate` - Generate content using RAG
- `POST /api/search` - Perform semantic search
- `POST /api/ingest` - Add documents to knowledge base
- `GET /api/metrics` - System performance metrics
- `GET /api/health` - Health check

## 🚀 Deployment

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Serve static files**:
   - Deploy `dist/` folder to your preferred hosting service
   - Configure proxy to backend API
   - Set up environment variables if needed

## 📊 Performance Features

- **Real-time Metrics**: Live performance monitoring
- **Response Time Tracking**: Monitor API response times
- **Source Attribution**: Display content sources with confidence scores
- **Error Handling**: Graceful error states with retry mechanisms

## 🎯 Recruitment Showcase Features

This project demonstrates:
- **Modern React Development**: Hooks, TypeScript, modern patterns
- **UI/UX Excellence**: Professional design with attention to detail
- **AI Integration**: Complex API integration with real-time features
- **Performance Optimization**: Efficient state management and rendering
- **Documentation**: Clear, comprehensive documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for demonstration purposes and showcases advanced RAG technology implementation.
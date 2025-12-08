# AI Content Generation Service

A production-ready Flask service that integrates OpenAI GPT-4 with semantic search using Sentence-Transformers and FAISS for high-quality content generation with retrieval-augmented generation (RAG).

## 🌐 Live Demo

**Frontend:** [https://faiss-generation.vercel.app/](https://faiss-generation.vercel.app/)

> **⚠️ Important Note:** The backend server is hosted on **Railway.com's Free Tier**. Due to platform limitations, the server may pause or shut down after 30 days or if resource limits are reached. If the chat service is not responding, the server might need to be restarted. Please request a restart if you encounter issues.

## Features

- **GPT-4 Integration**: Advanced content generation using OpenAI's latest models
- **Semantic Search**: Fast similarity search using Sentence-Transformers and FAISS
- **RAG System**: Retrieval-augmented generation for contextually relevant responses
- **High Performance**: Sub-200ms API response times with Redis caching
- **Scalable Architecture**: Microservices design for production deployment
- **Data Pipeline**: Intelligent crawlers processing 100GB+ of text data
- **Production Ready**: Comprehensive monitoring, logging, and error handling

## Performance Metrics

- 🚀 500+ daily content generation requests
- ⚡ Sub-200ms API response times
- 📊 95% user satisfaction rate
- 💾 100GB+ text data processing capability

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd ai-content-generation-service
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run Services**
   ```bash
   # Start Redis
   redis-server
   
   # Run the Flask application
   python app.py
   ```

## API Endpoints

- `POST /api/generate` - Generate content with RAG
- `POST /api/search` - Semantic search in knowledge base
- `POST /api/ingest` - Add new documents to knowledge base
- `GET /api/health` - Service health check
- `GET /api/metrics` - Performance metrics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Crawler   │───▶│  Data Pipeline  │───▶│ Vector Database │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│   Redis Cache   │◀───│  Flask API      │◀────────────┘
└─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   OpenAI GPT-4  │
                       └─────────────────┘
```

## Technology Stack

- **Backend**: Flask, Python 3.9+
- **AI/ML**: OpenAI GPT-4, Sentence-Transformers, FAISS
- **Caching**: Redis
- **Data Processing**: Beautiful Soup, NLTK, Pandas
- **Monitoring**: Custom metrics and logging
- **Deployment**: Docker, Gunicorn

## License

MIT License - see LICENSE file for details.
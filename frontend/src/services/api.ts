import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  timeout: 60000, // Increased to 60 seconds for Render free tier cold starts
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add any authentication headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for global error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export interface GenerateContentRequest {
  query: string;
  max_length?: number;
  temperature?: number;
}

export interface GenerateContentResponse {
  content: string;
  sources: Array<{
    title: string;
    url: string;
    snippet: string;
    score: number;
  }>;
  response_time_ms: number;
  timestamp: string;
}

export interface SearchRequest {
  query: string;
  limit?: number;
}

export interface SearchResponse {
  results: Array<{
    id: string;
    title: string;
    content: string;
    metadata: Record<string, any>;
    score: number;
  }>;
  count: number;
  response_time_ms: number;
  timestamp: string;
}

export interface IngestRequest {
  documents: Array<{
    title: string;
    content: string;
    url?: string;
    metadata?: Record<string, any>;
  }>;
}

export interface IngestResponse {
  processed_count: number;
  response_time_ms: number;
  timestamp: string;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version: string;
  error?: string;
}

export interface MetricsResponse {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_response_time: number;
  requests_by_endpoint: Record<string, number>;
  system_health: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

export class ApiService {
  // Health check
  static async healthCheck(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  }

  // Generate content using RAG
  static async generateContent(request: GenerateContentRequest): Promise<GenerateContentResponse> {
    const response = await api.post<GenerateContentResponse>('/generate', request);
    return response.data;
  }

  // Perform semantic search
  static async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await api.post<SearchResponse>('/search', request);
    return response.data;
  }

  // Ingest new documents
  static async ingestDocuments(request: IngestRequest): Promise<IngestResponse> {
    const response = await api.post<IngestResponse>('/ingest', request);
    return response.data;
  }

  // Get system metrics
  static async getMetrics(): Promise<MetricsResponse> {
    const response = await api.get<MetricsResponse>('/metrics');
    return response.data;
  }
}

export default ApiService;
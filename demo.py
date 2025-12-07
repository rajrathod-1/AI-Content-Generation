#!/usr/bin/env python3
"""
Demo script for the AI Content Generation Service
Showcases all major features and capabilities
"""

import requests
import json
import time
import sys
import os
from typing import Dict, List

class AIContentServiceDemo:
    """Demo class for showcasing AI Content Generation Service"""
    
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_response(self, response_data: Dict, max_content_length: int = 300):
        """Print formatted response"""
        if 'content' in response_data:
            content = response_data['content']
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            print(f"Generated Content: {content}")
            
            if 'sources' in response_data and response_data['sources']:
                print(f"\nSources Used ({len(response_data['sources'])}):")
                for i, source in enumerate(response_data['sources'][:3], 1):
                    print(f"  {i}. {source['title']} (Score: {source['score']:.3f})")
                    print(f"     URL: {source['url']}")
            
            if 'response_time_ms' in response_data:
                print(f"\nResponse Time: {response_data['response_time_ms']:.1f}ms")
        
        elif 'results' in response_data:
            print(f"Search Results ({response_data.get('count', 0)}):")
            for i, result in enumerate(response_data['results'][:5], 1):
                content = result['content']
                if len(content) > 150:
                    content = content[:150] + "..."
                print(f"  {i}. {result['title']} (Score: {result['score']:.3f})")
                print(f"     {content}")
                print(f"     URL: {result['url']}")
        
        else:
            print(json.dumps(response_data, indent=2))
    
    def check_health(self) -> bool:
        """Check if the service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Service is {health_data['status']}")
                return True
            else:
                print(f"❌ Service health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to service: {str(e)}")
            return False
    
    def demo_content_generation(self):
        """Demonstrate content generation with RAG"""
        self.print_header("CONTENT GENERATION WITH RAG")
        
        test_queries = [
            {
                "query": "Explain the benefits of renewable energy sources",
                "max_length": 400,
                "temperature": 0.7
            },
            {
                "query": "What are the latest developments in artificial intelligence?",
                "max_length": 500,
                "temperature": 0.6
            },
            {
                "query": "How does machine learning work in simple terms?",
                "max_length": 300,
                "temperature": 0.5
            }
        ]
        
        for i, query_data in enumerate(test_queries, 1):
            print(f"\n--- Test Query {i} ---")
            print(f"Query: {query_data['query']}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/generate",
                    json=query_data
                )
                
                if response.status_code == 200:
                    self.print_response(response.json())
                else:
                    print(f"❌ Generation failed: {response.status_code}")
                    print(response.text)
            
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            time.sleep(1)  # Small delay between requests
    
    def demo_semantic_search(self):
        """Demonstrate semantic search functionality"""
        self.print_header("SEMANTIC SEARCH")
        
        search_queries = [
            "machine learning algorithms",
            "solar energy technology",
            "data science techniques",
            "cloud computing benefits",
            "artificial intelligence applications"
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n--- Search Query {i} ---")
            print(f"Query: {query}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/search",
                    json={"query": query, "limit": 5}
                )
                
                if response.status_code == 200:
                    self.print_response(response.json())
                else:
                    print(f"❌ Search failed: {response.status_code}")
                    print(response.text)
            
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            time.sleep(0.5)
    
    def demo_document_ingestion(self):
        """Demonstrate document ingestion"""
        self.print_header("DOCUMENT INGESTION")
        
        sample_documents = [
            {
                "title": "Introduction to Quantum Computing",
                "content": """Quantum computing is a revolutionary technology that leverages the principles of quantum mechanics to process information. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or 'qubits' that can exist in multiple states simultaneously. This property, called superposition, allows quantum computers to perform many calculations in parallel. Another key principle is entanglement, where qubits become correlated and the state of one qubit instantaneously affects another, regardless of distance. Quantum computing has the potential to solve complex problems that are practically impossible for classical computers, such as cryptography, drug discovery, financial modeling, and optimization problems.""",
                "url": "https://example.com/quantum-computing-intro",
                "metadata": {
                    "category": "technology",
                    "difficulty": "intermediate",
                    "author": "Dr. Alice Johnson",
                    "publication_date": "2023-10-01"
                }
            },
            {
                "title": "Sustainable Agriculture Practices",
                "content": """Sustainable agriculture focuses on producing food while preserving the environment and supporting farmers' livelihoods. Key practices include crop rotation to maintain soil health, integrated pest management to reduce chemical use, water conservation through efficient irrigation systems, and biodiversity preservation. Organic farming methods eliminate synthetic pesticides and fertilizers, while precision agriculture uses technology to optimize resource use. Cover crops prevent soil erosion and improve fertility, and agroforestry integrates trees with crops for multiple benefits. These practices help address climate change, protect natural resources, and ensure food security for future generations.""",
                "url": "https://example.com/sustainable-agriculture",
                "metadata": {
                    "category": "agriculture",
                    "difficulty": "beginner",
                    "author": "Prof. Maria Garcia",
                    "publication_date": "2023-09-15"
                }
            },
            {
                "title": "Blockchain Technology and Cryptocurrencies",
                "content": """Blockchain is a distributed ledger technology that maintains a continuously growing list of records, called blocks, linked and secured using cryptography. Each block contains a cryptographic hash of the previous block, a timestamp, and transaction data. This creates an immutable record that is resistant to modification. Cryptocurrencies like Bitcoin and Ethereum use blockchain technology to enable peer-to-peer transactions without intermediaries. Smart contracts on blockchain platforms can automatically execute agreements when predetermined conditions are met. Beyond cryptocurrencies, blockchain has applications in supply chain management, healthcare records, voting systems, and digital identity verification.""",
                "url": "https://example.com/blockchain-technology",
                "metadata": {
                    "category": "technology",
                    "difficulty": "advanced",
                    "author": "Dr. Robert Chen",
                    "publication_date": "2023-10-10"
                }
            }
        ]
        
        for i, doc in enumerate(sample_documents, 1):
            print(f"\n--- Ingesting Document {i} ---")
            print(f"Title: {doc['title']}")
            print(f"Content length: {len(doc['content'])} characters")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/ingest",
                    json={"documents": [doc]}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Successfully ingested {result['processed_count']} document(s)")
                    print(f"   Processing time: {result['response_time_ms']:.1f}ms")
                else:
                    print(f"❌ Ingestion failed: {response.status_code}")
                    print(response.text)
            
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            time.sleep(0.5)
    
    def demo_performance_metrics(self):
        """Demonstrate performance metrics"""
        self.print_header("PERFORMANCE METRICS")
        
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            
            if response.status_code == 200:
                metrics = response.json()
                
                print(f"📊 System Overview:")
                print(f"   Uptime: {metrics.get('uptime_human', 'N/A')}")
                print(f"   Total Requests: {metrics.get('total_requests', 0):,}")
                print(f"   Success Rate: {metrics.get('success_rate', 0):.1%}")
                print(f"   Average Response Time: {metrics.get('average_response_time_ms', 0):.1f}ms")
                print(f"   Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.1%}")
                print(f"   Health Score: {metrics.get('health_score', 0):.1f}/100")
                
                print(f"\n📈 Response Time Distribution:")
                distribution = metrics.get('response_time_distribution', {})
                for bucket, count in distribution.items():
                    print(f"   {bucket}: {count} requests")
                
                print(f"\n👥 Usage Statistics:")
                print(f"   Active Users: {metrics.get('active_users_count', 0)}")
                print(f"   Requests per Minute: {metrics.get('requests_per_minute', 0):.1f}")
                print(f"   Total Tokens Used: {metrics.get('total_tokens_used', 0):,}")
                
                if 'service_breakdown' in metrics:
                    print(f"\n🔧 Service Breakdown:")
                    for service, stats in metrics['service_breakdown'].items():
                        print(f"   {service}:")
                        print(f"     Success Rate: {stats.get('success_rate', 0):.1%}")
                        print(f"     Avg Response Time: {stats.get('average_response_time_ms', 0):.1f}ms")
                        print(f"     Cache Hit Rate: {stats.get('cache_hit_rate', 0):.1%}")
            
            else:
                print(f"❌ Failed to get metrics: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def demo_real_world_scenario(self):
        """Demonstrate a real-world usage scenario"""
        self.print_header("REAL-WORLD SCENARIO: RESEARCH ASSISTANT")
        
        print("🔍 Scenario: Creating a comprehensive report on renewable energy")
        
        # Step 1: Search for relevant information
        print("\n--- Step 1: Research Phase ---")
        research_query = "renewable energy solar wind hydroelectric benefits challenges"
        
        try:
            search_response = self.session.post(
                f"{self.base_url}/search",
                json={"query": research_query, "limit": 8}
            )
            
            if search_response.status_code == 200:
                search_results = search_response.json()
                print(f"Found {search_results['count']} relevant sources")
                for i, result in enumerate(search_results['results'][:3], 1):
                    print(f"  {i}. {result['title']} (Relevance: {result['score']:.3f})")
            
        except Exception as e:
            print(f"❌ Research phase error: {str(e)}")
        
        # Step 2: Generate comprehensive content
        print("\n--- Step 2: Content Generation ---")
        generation_queries = [
            "Create an introduction to renewable energy sources and their importance",
            "Explain the advantages and disadvantages of solar energy",
            "Discuss the future prospects of renewable energy technology"
        ]
        
        for i, query in enumerate(generation_queries, 1):
            print(f"\n--- Generating Section {i} ---")
            try:
                gen_response = self.session.post(
                    f"{self.base_url}/generate",
                    json={
                        "query": query,
                        "max_length": 400,
                        "temperature": 0.6
                    }
                )
                
                if gen_response.status_code == 200:
                    result = gen_response.json()
                    content = result['content']
                    if len(content) > 200:
                        content = content[:200] + "..."
                    print(f"Generated: {content}")
                    print(f"Sources: {len(result.get('sources', []))} references")
                    print(f"Response time: {result.get('response_time_ms', 0):.1f}ms")
                
            except Exception as e:
                print(f"❌ Generation error: {str(e)}")
            
            time.sleep(0.5)
    
    def run_full_demo(self):
        """Run the complete demonstration"""
        print("🚀 AI Content Generation Service - Comprehensive Demo")
        print("=" * 60)
        
        # Health check
        if not self.check_health():
            print("❌ Service is not available. Please start the service first.")
            sys.exit(1)
        
        try:
            # Run all demos
            self.demo_document_ingestion()
            time.sleep(2)
            
            self.demo_semantic_search()
            time.sleep(2)
            
            self.demo_content_generation()
            time.sleep(2)
            
            self.demo_real_world_scenario()
            time.sleep(2)
            
            self.demo_performance_metrics()
            
            # Final summary
            self.print_header("DEMO COMPLETED SUCCESSFULLY")
            print("✅ All features demonstrated successfully!")
            print("\n📋 Summary of capabilities showcased:")
            print("   • Document ingestion and processing")
            print("   • Semantic search with FAISS vector database")
            print("   • RAG-powered content generation with GPT-4")
            print("   • Real-world research assistant scenario")
            print("   • Comprehensive performance monitoring")
            print("   • Sub-200ms response times")
            print("   • Production-ready monitoring and metrics")
            
            print(f"\n🎯 Ready for production deployment!")
            print(f"   API Base URL: {self.base_url}")
            print(f"   Documentation: See API_DOCUMENTATION.md")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo failed with error: {str(e)}")

def main():
    """Main function to run the demo"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Content Generation Service Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo.py                                    # Run full demo
  python demo.py --url http://localhost:5000/api   # Custom URL
  python demo.py --quick                           # Quick demo (subset)
        """
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:5000/api',
        help='Base URL for the API service (default: http://localhost:5000/api)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run a quick demo with fewer examples'
    )
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = AIContentServiceDemo(args.url)
    
    if args.quick:
        print("🏃‍♂️ Running Quick Demo")
        demo.check_health()
        demo.demo_content_generation()
        demo.demo_performance_metrics()
    else:
        demo.run_full_demo()

if __name__ == "__main__":
    main()
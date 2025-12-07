#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API integration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.openai_service import OpenAIService

def test_openai_connection():
    """Test OpenAI API connection"""
    print("🧪 Testing OpenAI API Connection...")
    
    try:
        # Create config
        config = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'OPENAI_MODEL': 'gpt-4-0125-preview',
            'OPENAI_MAX_TOKENS': 100,
            'OPENAI_TEMPERATURE': 0.7,
            'REQUEST_TIMEOUT': 30
        }
        
        # Initialize service
        service = OpenAIService(config)
        
        # Test simple generation
        print("📝 Testing simple content generation...")
        result = service.generate_content("Say hello in a friendly way.")
        
        print(f"✅ Success!")
        print(f"   Content: {result.content}")
        print(f"   Tokens: {result.tokens_used}")
        print(f"   Time: {result.response_time:.2f}s")
        print(f"   Model: {result.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_connection()
    sys.exit(0 if success else 1)
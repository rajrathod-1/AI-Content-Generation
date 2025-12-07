#!/usr/bin/env python3
"""
Debug script to check configuration
"""
import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv()

from src.config import Config

print("=== Configuration Debug ===")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT_SET')[:20]}...")
print(f"OPENAI_MODEL from env: {os.getenv('OPENAI_MODEL', 'NOT_SET')}")
print(f"OPENAI_MODEL from config: {Config.OPENAI_MODEL}")
print(f"OPENAI_MAX_TOKENS: {Config.OPENAI_MAX_TOKENS}")
print(f"OPENAI_TEMPERATURE: {Config.OPENAI_TEMPERATURE}")

# Test OpenAI service initialization
try:
    from src.services.openai_service import OpenAIService
    config_dict = {
        'OPENAI_API_KEY': Config.OPENAI_API_KEY,
        'OPENAI_MODEL': Config.OPENAI_MODEL,
        'OPENAI_MAX_TOKENS': Config.OPENAI_MAX_TOKENS,
        'OPENAI_TEMPERATURE': Config.OPENAI_TEMPERATURE,
        'REQUEST_TIMEOUT': 30
    }
    
    service = OpenAIService(config_dict)
    print(f"✅ OpenAI Service initialized successfully")
    print(f"Service model: {service.model}")
    print(f"Service API key: {service.api_key[:20]}...")
    
    # Test a simple generation
    result = service.generate_content("Hello, this is a test", max_tokens=10)
    print(f"✅ Test generation successful: {result.content}")
    
except Exception as e:
    print(f"❌ OpenAI Service failed: {e}")
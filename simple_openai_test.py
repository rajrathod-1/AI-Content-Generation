#!/usr/bin/env python3
"""
Simple OpenAI API test without dependencies
"""
import os
from openai import OpenAI

# Test OpenAI API directly
def test_openai_api():
    api_key = os.getenv('OPENAI_API_KEY', 'your-api-key-here')
    
    try:
        client = OpenAI(api_key=api_key, timeout=60.0, max_retries=3)
        
        print("Testing OpenAI API connection...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say hello in exactly 5 words"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        print(f"✅ SUCCESS!")
        print(f"Response: {content}")
        print(f"Tokens used: {tokens}")
        print(f"Model: {response.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    test_openai_api()
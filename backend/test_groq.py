#!/usr/bin/env python
"""Test script to verify API connection"""
import os
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to python path
sys.path.append(str(Path(__file__).resolve().parent))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resumeai.settings')

import django
django.setup()

from core.utils import _get_client, _get_model
from django.conf import settings

def test_api_connection():
    print("Testing API connection...")
    
    client = _get_client()
    if not client:
        print("ERROR: API key not found. Please set OPENROUTER_API_KEY or GROQ_API_KEY in your .env file.")
        return False
        
    is_openrouter = bool(getattr(settings, 'OPENROUTER_API_KEY', '').strip())
    provider = "OpenRouter" if is_openrouter else "Groq"
    print(f"Connecting to provider: {provider}")
    
    try:
        model_name = _get_model()
        print(f"Using model: {model_name}")
        
        # Test a simple chat completion
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Say 'Hello from {provider}!' in one sentence."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"SUCCESS: {provider} API response: {result}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to connect to {provider} API: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)

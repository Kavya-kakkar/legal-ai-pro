import requests
import os
from dotenv import load_dotenv
from typing import Optional
import time
from functools import wraps

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ✅ Validate API key at startup
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:8000",  # ✅ Fixed URL
    "X-Title": "Legal AI Assistant"
}

def retry_on_failure(max_retries: int = 3):
    """Decorator for retrying API calls on transient failures"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
            return None
        return wrapper
    return decorator

@retry_on_failure()
def generate_legal_draft(prompt: str) -> str:
    """
    Generate legal draft using OpenRouter API
    
    Args:
        prompt: Legal notice prompt with party details and issue
        
    Returns:
        Generated legal draft text
        
    Raises:
        ValueError: Invalid input
        Exception: API errors
    """
    # ✅ Input validation
    if not prompt or len(prompt.strip()) < 20:
        raise ValueError("Prompt too short or empty")
    
    payload = {
        "model": "openai/gpt-4o-mini",  # ✅ Good choice: fast + capable for legal drafting
        "messages": [
            {
                "role": "system", 
                "content": """You are an expert Indian legal drafting advocate with 20+ years experience.
                
Format: Formal Indian legal notice structure
- Advocate letterhead format
- Proper notice period (15/30 days as appropriate)
- Legally precise language
- Section references (IPC, CrPC, Contract Act where relevant)
- Standard clauses for payment demands, compliance, consequences
- Court jurisdiction clause
- Signed by advocate"""
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,  # ✅ Lowered for more consistent legal language
        "max_tokens": 2000,  # ✅ Increased for complete notices
        "top_p": 0.9
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=HEADERS,
            json=payload,
            timeout=90  # ✅ Increased timeout
        )
        
        # ✅ Detailed error handling
        if response.status_code == 401:
            raise Exception("Invalid API key - check OPENROUTER_API_KEY")
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded - too many requests")
        elif response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        data = response.json()
        
        # ✅ Validate response structure
        if "choices" not in data or not data["choices"]:
            raise Exception("Empty response from API")
        
        content = data["choices"][0]["message"]["content"].strip()
        
        if not content:
            raise Exception("Generated empty draft")
            
        return content
        
    except requests.exceptions.Timeout:
        raise Exception("API request timed out")
    except requests.exceptions.ConnectionError:
        raise Exception("Failed to connect to OpenRouter API")
    except KeyError as e:
        raise Exception(f"Unexpected API response format: {e}")
    except Exception as e:
        raise Exception(f"Failed to generate legal draft: {str(e)}")

# ✅ Test function (optional)
def test_connection() -> bool:
    """Test API connectivity"""
    try:
        simple_prompt = "Draft a one-sentence legal notice."
        generate_legal_draft(simple_prompt)
        print("✅ OpenRouter API connection successful")
        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()

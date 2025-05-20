#!/usr/bin/env python3
import os
import requests
import logging
from dotenv import load_dotenv

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api_debug')

# Load environment variables
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def test_rapidapi_key():
    """Tests if the RapidAPI key is valid"""
    if not RAPIDAPI_KEY:
        logger.error("RAPIDAPI_KEY is not set in environment or .env file")
        return False
    
    # Mask the API key for logging (show only first 4 and last 4 characters)
    key_length = len(RAPIDAPI_KEY)
    masked_key = RAPIDAPI_KEY[:4] + "*" * (key_length - 8) + RAPIDAPI_KEY[-4:] if key_length > 8 else "********"
    logger.info(f"Using RapidAPI key: {masked_key}")
    
    # Test with a simple RapidAPI endpoint that returns API key info
    url = "https://real-time-news-data.p.rapidapi.com/top-headlines"
    
    headers = {
        "x-rapidapi-host": "real-time-news-data.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    
    params = {"limit": "1", "country": "US", "lang": "en"}
    
    try:
        # Make a request with verbose logging
        logger.info(f"Testing API key with endpoint: {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        
        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            logger.info("API key is valid! Response preview:")
            try:
                resp_json = response.json()
                logger.info(f"Response contains {len(resp_json.get('data', []))} headlines")
                return True
            except Exception as e:
                logger.error(f"Error parsing response: {e}")
                return False
        elif response.status_code == 403:
            logger.error("API key is invalid or doesn't have access to this endpoint")
            logger.error(f"Error message: {response.text}")
            return False
        else:
            logger.error(f"Unexpected status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}...")
            return False
    except Exception as e:
        logger.error(f"Error testing API key: {e}")
        return False

def check_env_file():
    """Checks if .env file has correct format for API keys"""
    try:
        with open('.env', 'r') as f:
            content = f.read()
            logger.info("Found .env file")
            
            # Check if API keys are present with proper format
            if 'RAPIDAPI_KEY=' not in content:
                logger.warning("RAPIDAPI_KEY not found in .env file with correct format")
                logger.info("Expected format: RAPIDAPI_KEY=your_api_key_here (no spaces or quotes)")
            else:
                logger.info("RAPIDAPI_KEY entry found in .env file")
                
            if 'OPENAI_API_KEY=' not in content:
                logger.warning("OPENAI_API_KEY not found in .env file with correct format")
            else:
                logger.info("OPENAI_API_KEY entry found in .env file")
    except FileNotFoundError:
        logger.error(".env file not found")
        logger.info("Create a .env file with RAPIDAPI_KEY=your_key and OPENAI_API_KEY=your_key")

def suggest_fixes():
    """Suggests potential fixes for API issues"""
    logger.info("Potential fixes for API issues:")
    logger.info("1. Check if your RapidAPI key is active and valid")
    logger.info("2. Verify you've subscribed to the correct RapidAPI services:")
    logger.info("   - real-time-news-data")
    logger.info("   - news-article-data-extract-and-summarization1")
    logger.info("3. Make sure your .env file is formatted correctly:")
    logger.info("   RAPIDAPI_KEY=your_key_here")
    logger.info("   OPENAI_API_KEY=your_key_here")
    logger.info("4. Check if you have remaining API quota/credits on RapidAPI")
    logger.info("5. Try regenerating your API key in the RapidAPI dashboard")

if __name__ == "__main__":
    logger.info("Starting API debugging...")
    check_env_file()
    api_key_valid = test_rapidapi_key()
    
    if not api_key_valid:
        suggest_fixes()
    
    logger.info("API debugging completed")

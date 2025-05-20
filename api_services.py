#!/usr/bin/env python3
import os
import json
import base64
import logging
import requests
from openai import OpenAI
from pathlib import Path

# Use logger from centralized config
from log_config import setup_colored_logging
logger = logging.getLogger('api_services')

class APIServices:
    """
    Handles all API interactions (OpenAI, RapidAPI, etc.)
    """
    def __init__(self, openai_api_key, rapidapi_key):
        self.openai_api_key = openai_api_key
        self.rapidapi_key = rapidapi_key
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.session = requests.Session()
        
        # API URLs
        self.REALTIME_NEWS_URL = "https://real-time-news-data.p.rapidapi.com/topic-headlines"
        self.EXTRACT_URL = "https://news-article-data-extract-and-summarization1.p.rapidapi.com/extract"
        
        # Load prompt templates
        self.prompt_dir = Path("prompts")
        self.summary_prompt = self._load_prompt("summary_prompt.txt")
        self.image_subtitle_prompt = self._load_prompt("image_subtitle_prompt.txt")
    
    def _load_prompt(self, filename):
        """Load a prompt template from file"""
        try:
            file_path = self.prompt_dir / filename
            with open(file_path, "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load prompt from {filename}: {e}")
            return ""
    
    def fetch_headlines(self, country="US", lang="en", limit=15, topic="BUSINESS"):
        """Fetches topic headlines using RapidAPI"""
        logger.info(f"Fetching {topic} headlines for country={country}, lang={lang}")
        
        params = {"topic": topic, "limit": str(limit), "country": country, "lang": lang}
        headers = {
            "x-rapidapi-host": "real-time-news-data.p.rapidapi.com",
            "x-rapidapi-key": self.rapidapi_key
        }
        
        try:
            resp = self.session.get(self.REALTIME_NEWS_URL, params=params, headers=headers)
            resp.raise_for_status()
            result = resp.json().get("data", [])
            logger.info(f"Retrieved {len(result)} headlines")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch headlines: {e}")
            return []
    
    def extract_article(self, url):
        """Extracts article content using RapidAPI"""
        logger.info(f"Extracting article from URL: {url}")
        
        headers = {
            "x-rapidapi-host": "news-article-data-extract-and-summarization1.p.rapidapi.com",
            "x-rapidapi-key": self.rapidapi_key,
            "Content-Type": "application/json"
        }
        payload = {"url": url}
        
        try:
            resp = self.session.post(self.EXTRACT_URL, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            logger.info("Article extraction completed successfully")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to extract article: {e}")
            return None
    
    def generate_summary(self, article):
        """Generates a summary of the article using OpenAI"""
        logger.info("Generating summary with OpenAI")
        
        # Use the loaded prompt template from file
        prompt = self.summary_prompt
        
        # Add article data to the prompt
        article_data = f"""
---------------
{article.get('url','')}
{article.get('title','')}
{article.get('author','')}
{article.get('text','')}
{article.get('description','')}
{article.get('siteName','')}
{article.get('date','')}
{','.join(article.get('keywords',[]))}
{article.get('summary','')}
"""
        
        # Combine the prompt template with article data
        full_prompt = f"{prompt}\n\n{article_data}"
        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": full_prompt}]
            )
            content = resp.choices[0].message.content
            # Parse the JSON response
            try:
                # Clean response if needed (remove markdown code blocks etc.)
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "")
                elif content.startswith("`"):
                    content = content.strip("`")
                
                result = json.loads(content)
                logger.info(f"Summary generation complete with {len(result.get('slides', []))} slides")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Raw response: {content[:500]}...")
                return None
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            if 'content' in locals():
                logger.debug(f"Raw OpenAI response: {content[:500]}...")
            return None
    
    def generate_tts(self, text):
        """Generates text-to-speech using OpenAI API"""
        if not text or len(text.strip()) == 0:
            error_msg = "Empty text provided for TTS generation"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info(f"Generating TTS for text: '{text[:50]}...'")
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        # Use a voice that supports Italian
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": "alloy",  # 'alloy' or 'nova', 'shimmer', 'echo', 'onyx', 'fable'
            "response_format": "mp3",
            "speed": 1.2
        }
        
        try:
            resp = self.session.post(
                "https://api.openai.com/v1/audio/speech", 
                json=payload, 
                headers=headers
            )
            resp.raise_for_status()
            logger.info(f"TTS generation complete, received {len(resp.content)} bytes")
            return resp.content  # raw MP3 bytes
        except requests.exceptions.RequestException as e:
            # Try to get the error details
            error_msg = f"Failed to generate TTS: {e}"
            try:
                error_details = resp.json()
                error_msg += f" - Details: {error_details}"
                logger.error(error_msg)
            except Exception:
                logger.error(error_msg)
                logger.error("Could not parse error response")
            # Re-raise a custom exception with details
            raise RuntimeError(error_msg)
    
    def generate_image(self, img_prompt, title):
        """Generates an image using OpenAI's DALL-E API"""
        if not img_prompt or len(img_prompt.strip()) == 0:
            error_msg = "Empty image prompt provided"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info(f"Generating image for prompt: '{img_prompt[:300]}...'")
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        # Use the loaded image subtitle prompt template
        full_prompt = f"{img_prompt}. {self.image_subtitle_prompt.format(title=title)}"
        
        # Make sure we use the DALL-E 3 model for better results
        payload = {
            "model": "dall-e-3",
            "prompt": full_prompt,
            "n": 1,
            "size": "1024x1792",  # DALL-E 3 supports these dimensions
            "response_format": "b64_json",
            "quality": "standard"
        }
        
        try:
            resp = self.session.post(
                "https://api.openai.com/v1/images/generations", 
                json=payload, 
                headers=headers
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Image generation complete")
            return result.get('data', [{}])[0].get('b64_json')
        except requests.exceptions.RequestException as e:
            # Try to get the error details
            error_msg = f"Failed to generate image: {e}"
            try:
                error_details = resp.json()
                error_msg += f" - Details: {error_details}"
                logger.error(error_msg)
                # Also log the prompt that caused the error
                logger.error(f"Problematic prompt: {full_prompt[:]}...")
            except Exception:
                logger.error(error_msg)
                logger.error("Could not parse error response")
            # Re-raise a custom exception with details
            raise RuntimeError(error_msg)

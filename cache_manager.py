#!/usr/bin/env python3
import os
import json
import logging
import hashlib
import base64
from pathlib import Path

# Use logger from centralized config
from log_config import setup_colored_logging
logger = logging.getLogger('cache_manager')

class CacheManager:
    """
    Manages caching of API responses to avoid redundant API calls
    """
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create subdirectories for different types of content
        self.tts_dir = os.path.join(cache_dir, "tts")
        self.image_dir = os.path.join(cache_dir, "images")
        self.article_dir = os.path.join(cache_dir, "articles")
        self.summary_dir = os.path.join(cache_dir, "summaries")
        self.headlines_dir = os.path.join(cache_dir, "headlines")
        
        for directory in [self.tts_dir, self.image_dir, self.article_dir, self.summary_dir, self.headlines_dir]:
            os.makedirs(directory, exist_ok=True)
            
        logger.info(f"Cache initialized at {os.path.abspath(cache_dir)}")
        
    def _get_hash(self, content):
        """Create a hash from content for use as a cache key"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.md5(content).hexdigest()
        
    def get_tts(self, text):
        """Check if TTS for text exists in cache"""
        content_hash = self._get_hash(text)
        cache_path = os.path.join(self.tts_dir, f"{content_hash}.mp3")
        
        if os.path.exists(cache_path):
            logger.info(f"TTS cache hit for '{text[:30]}...'")
            with open(cache_path, "rb") as f:
                return f.read()
        return None
        
    def save_tts(self, text, audio_content):
        """Save TTS audio to cache"""
        content_hash = self._get_hash(text)
        cache_path = os.path.join(self.tts_dir, f"{content_hash}.mp3")
        
        with open(cache_path, "wb") as f:
            f.write(audio_content)
        logger.info(f"Saved TTS to cache for '{text[:30]}...'")
        
    def get_image(self, prompt):
        """Check if image for prompt exists in cache"""
        content_hash = self._get_hash(prompt)
        cache_path = os.path.join(self.image_dir, f"{content_hash}.b64")
        
        if os.path.exists(cache_path):
            logger.info(f"Image cache hit for prompt '{prompt[:30]}...'")
            with open(cache_path, "r") as f:
                return f.read()
        return None
        
    def save_image(self, prompt, image_b64):
        """Save image base64 to cache"""
        content_hash = self._get_hash(prompt)
        cache_path = os.path.join(self.image_dir, f"{content_hash}.b64")
        
        with open(cache_path, "w") as f:
            f.write(image_b64)
        logger.info(f"Saved image to cache for prompt '{prompt[:30]}...'")
        
    def delete_image(self, prompt):
        """Delete image from cache if generation fails"""
        content_hash = self._get_hash(prompt)
        cache_path = os.path.join(self.image_dir, f"{content_hash}.b64")
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                logger.info(f"Deleted failed image from cache for prompt '{prompt[:30]}...'")
                return True
            except Exception as e:
                logger.error(f"Failed to delete image cache for prompt '{prompt[:30]}...': {e}")
        return False
        
    def get_article(self, url):
        """Check if article extraction exists in cache"""
        content_hash = self._get_hash(url)
        cache_path = os.path.join(self.article_dir, f"{content_hash}.json")
        
        if os.path.exists(cache_path):
            logger.info(f"Article cache hit for URL '{url}'")
            with open(cache_path, "r") as f:
                return json.load(f)
        return None
        
    def save_article(self, url, article_data):
        """Save article data to cache"""
        content_hash = self._get_hash(url)
        cache_path = os.path.join(self.article_dir, f"{content_hash}.json")
        
        with open(cache_path, "w") as f:
            json.dump(article_data, f)
        logger.info(f"Saved article to cache for URL '{url}'")
        
    def get_summary(self, article_data):
        """Check if summary for article exists in cache"""
        # Use the URL as the key for caching since it uniquely identifies the article
        url = article_data.get('url', '')
        if not url:
            return None
            
        content_hash = self._get_hash(url)
        cache_path = os.path.join(self.summary_dir, f"{content_hash}.json")
        
        if os.path.exists(cache_path):
            logger.info(f"Summary cache hit for article '{url}'")
            with open(cache_path, "r") as f:
                return json.load(f)
        return None
        
    def save_summary(self, article_data, summary_data):
        """Save summary data to cache"""
        url = article_data.get('url', '')
        if not url:
            logger.warning("Cannot cache summary: URL not found in article data")
            return
            
        content_hash = self._get_hash(url)
        cache_path = os.path.join(self.summary_dir, f"{content_hash}.json")
        
        with open(cache_path, "w") as f:
            json.dump(summary_data, f)
        logger.info(f"Saved summary to cache for article '{url}'")
        
    def delete_summary(self, article_data):
        """Delete summary from cache if any slide generation fails"""
        url = article_data.get('url', '')
        if not url:
            logger.warning("Cannot delete summary: URL not found in article data")
            return False
            
        content_hash = self._get_hash(url)
        cache_path = os.path.join(self.summary_dir, f"{content_hash}.json")
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                logger.info(f"Deleted summary from cache for article '{url}'")
                return True
            except Exception as e:
                logger.error(f"Failed to delete summary cache for article '{url}': {e}")
        return False
        
    def get_headlines(self, country, lang, limit, topic="BUSINESS"):
        """Check if headlines exist in cache"""
        # Create a unique key for the headlines request based on parameters
        key = f"{topic}-{country}-{lang}-{limit}"
        content_hash = self._get_hash(key)
        cache_path = os.path.join(self.headlines_dir, f"{content_hash}.json")
        
        if os.path.exists(cache_path):
            logger.info(f"Headlines cache hit for topic '{topic}', country '{country}', language '{lang}', limit {limit}")
            with open(cache_path, "r") as f:
                return json.load(f)
        return None
        
    def save_headlines(self, country, lang, limit, headlines_data, topic="BUSINESS"):
        """Save headlines data to cache"""
        key = f"{topic}-{country}-{lang}-{limit}"
        content_hash = self._get_hash(key)
        cache_path = os.path.join(self.headlines_dir, f"{content_hash}.json")
        
        with open(cache_path, "w") as f:
            json.dump(headlines_data, f)
        logger.info(f"Saved headlines to cache for topic '{topic}', country '{country}', language '{lang}', limit {limit}")

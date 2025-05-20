#!/usr/bin/env python3
import os
import re
import logging
from pathlib import Path
import json
import time
import random

# Import our modules
from video_generator import VideoGenerator
from cache_manager import CacheManager
from log_config import setup_colored_logging

# Configure logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger('test')

# Initialize services
cache_manager = CacheManager(cache_dir="./cache")
video_generator = VideoGenerator()

# Sample mock headlines
MOCK_HEADLINES = [
    {"title": "Italia vince la Coppa UEFA 2025", "link": "https://example.com/sport/1"},
    {"title": "Nuova tecnologia per batterie ecologiche", "link": "https://example.com/tech/1"},
    {"title": "Festival di Sanremo 2025 annuncia i partecipanti", "link": "https://example.com/culture/1"},
    {"title": "Borse europee in crescita dopo accordo commerciale", "link": "https://example.com/economy/1"},
    {"title": "Spettacolare aurora boreale visibile in Italia", "link": "https://example.com/science/1"},
    {"title": "Comunicato stampa del Consiglio dei Ministri n. 128", "link": "https://example.com/politics/1"},
    {"title": "Bartolomeo incontra Leone XIV a Roma", "link": "https://example.com/religion/1"},
    {"title": "Mattarella a Palazzo Ducale inaugura mostra", "link": "https://example.com/culture/2"}
]

def main():
    logger.info("Starting test workflow to find and process first unprocessed headline")
    
    # Ensure outputs directory exists
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    # Track if we found any new article to process
    processed_article = False
    
    # Check each headline
    for i, article in enumerate(MOCK_HEADLINES):
        headline_text = article.get('title', 'No title')
        logger.info(f"Checking article {i+1}/{len(MOCK_HEADLINES)}: {headline_text}")
        
        # Clean headline (letters only, truncated to 20 chars)
        clean_headline = re.sub(r'[^a-zA-Z]', '', headline_text)[:20]
        
        # Check for existing videos with this headline
        existing_videos = list(outputs_dir.glob(f"*_{clean_headline}.mp4"))
        if existing_videos:
            existing_video = existing_videos[0]
            logger.info(f"Video already exists for this headline: {existing_video}")
            continue  # Check next headline
        
        # Found a headline without existing video, process it
        logger.info(f"Selected article for processing: {headline_text}")
        
        # Create dummy video file to simulate processing
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_filename = f"{timestamp}_{clean_headline}.mp4"
        output_path = outputs_dir / output_filename
        
        # Create empty dummy file (would be a real video in production)
        with open(output_path, "wb") as f:
            f.write(b"Dummy video content")
        
        logger.info(f"Created dummy video: {output_path}")
        processed_article = True
        break  # Stop after first unprocessed article
    
    # If we checked all headlines and found none to process
    if not processed_article:
        logger.info("All articles already have videos generated - nothing new to process")
        return None
    
    logger.info("Successfully processed the first article without an existing video")
    return True

if __name__ == "__main__":
    logger.info("Testing article processing sequence")
    try:
        result = main()
        if result:
            logger.info("Test completed successfully - processed one article")
        elif result is None:
            logger.info("Test completed - all articles already processed")
        else:
            logger.warning("Test completed with errors")
    except Exception as e:
        logger.critical(f"Test failed: {e}")

#!/usr/bin/env python3
import os
import re
import logging
from pathlib import Path

# Use logger from centralized config
from log_config import setup_colored_logging

# Configure logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger('test_skip')

# Create a dummy file to simulate an existing video
def create_dummy_video(headline):
    # Clean headline (letters only, truncated to 20 chars)
    clean_headline = re.sub(r'[^a-zA-Z]', '', headline)[:20]
    
    # Create timestamp (using a fixed one for testing)
    timestamp = "20250520_010000"
    
    # Create filename
    filename = f"{timestamp}_{clean_headline}.mp4"
    
    # Ensure outputs directory exists
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    # Full path
    output_path = outputs_dir / filename
    
    # Create empty file
    with open(output_path, "wb") as f:
        f.write(b"Dummy video content")
    
    return output_path

def check_if_video_exists(headline):
    # Clean headline (letters only, truncated to 20 chars)
    clean_headline = re.sub(r'[^a-zA-Z]', '', headline)[:20]
    
    # Ensure outputs directory exists
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    # Check for existing videos with this headline
    existing_videos = list(outputs_dir.glob(f"*_{clean_headline}.mp4"))
    
    if existing_videos:
        logger.info(f"Video already exists for headline '{headline}': {existing_videos[0]}")
        return True
    else:
        logger.info(f"No video found for headline '{headline}', would generate new one")
        return False

def main():
    # Test headlines
    test_headlines = [
        "Guerra Israele Medio Oriente",  # We'll create a dummy video for this one
        "Economia italiana in crescita",  # This one won't have a pre-existing video
    ]
    
    # Create a dummy video for the first headline
    dummy_path = create_dummy_video(test_headlines[0])
    logger.info(f"Created dummy video at {dummy_path}")
    
    # Check both headlines
    for headline in test_headlines:
        logger.info(f"\nTesting headline: '{headline}'")
        exists = check_if_video_exists(headline)
        
        if exists:
            logger.info(f"✓ Would SKIP video generation for '{headline}'")
        else:
            logger.info(f"✓ Would PROCEED with video generation for '{headline}'")

if __name__ == "__main__":
    main()

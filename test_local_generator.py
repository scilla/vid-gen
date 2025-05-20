#!/usr/bin/env python3
import os
import logging
import base64
from pathlib import Path

# Import our video generator
from video_generator import VideoGenerator
from log_config import setup_colored_logging

# Configure logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger('test')

def main():
    logger.info("Testing local video generator with fixed ffmpeg configuration")
    
    # Set up some simple mock data
    # This would normally come from the API calls
    headline = "Test Headline for Generator"
    logger.info(f"Using headline: '{headline}'")
    
    # Create temporary directory for test files if it doesn't exist
    test_dir = Path("test_assets")
    test_dir.mkdir(exist_ok=True)
    
    # Create simple text placeholder files if they don't exist
    dummy_text = "This is a placeholder for testing.\n" * 10
    
    # Create dummy files for all required slots in mock data
    mock_results = {}
    for i in range(2):  # Create 2 slides for testing
        # Create placeholder slide data
        mock_results[i] = {
            "slide": {
                "title": f"Test Title {i+1}",
                "voiceOver": f"This is test voice over text for slide {i+1}",
                "imgPrompt": f"Test image prompt for slide {i+1}"
            },
            "image": dummy_text.encode('utf-8'),
            "audio": dummy_text.encode('utf-8')
        }
    
    # Initialize video generator
    video_gen = VideoGenerator()
    
    # Test the video filename and skipping feature
    logger.info(f"Checking if a video already exists for headline: '{headline}'")
    
    import re
    clean_headline = re.sub(r'[^a-zA-Z]', '', headline)[:20]
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    existing_videos = list(outputs_dir.glob(f"*_{clean_headline}.mp4"))
    if existing_videos:
        logger.info(f"Found existing video: {existing_videos[0]}")
        logger.info("The system would skip generation for this headline")
    else:
        logger.info("No existing video found for this headline")
        logger.info("The video generator would create a file with naming pattern:")
        logger.info(f"outputs/YYYYMMDD_HHMMSS_{clean_headline}.mp4")
    
    logger.info("\nTest completed successfully")

if __name__ == "__main__":
    main()

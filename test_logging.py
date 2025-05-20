#!/usr/bin/env python3
import logging
from log_config import setup_colored_logging

# Set up logging
setup_colored_logging(level=logging.DEBUG)
logger = logging.getLogger('test_logging')

def main():
    # Test various log types to see the color scheme
    logger.info("Starting log color test")
    
    # Headline/News logs
    logger.info("Fetched 15 headlines from news source")
    logger.info("Extracting article content from URL")
    
    # Summary/JSON logs
    logger.info("Generating summary for article")
    logger.info("Processing JSON response")
    
    # Media generation logs
    logger.info("Generating TTS for text segment")
    logger.info("Processing audio for slide 2")
    logger.info("Generating image for prompt")
    logger.info("Processing image for slide 3")
    logger.info("Generating video from slides and audio")
    logger.info("Assembling final video file")
    
    # Cache logs
    logger.info("Saving article to cache")
    logger.info("Found cached audio file")
    
    # Progress logs
    logger.info("Starting main workflow")
    logger.info("Successfully completed audio generation")
    logger.info("Waiting for API response")
    
    # Error handling
    logger.warning("API rate limit approaching")
    logger.error("Failed to generate image")
    logger.critical("Fatal error in video assembly")
    
    # API logs
    logger.info("API request sent to OpenAI")
    logger.info("URL processed: https://example.com/news")
    
    logger.info("Log color test completed")

if __name__ == "__main__":
    main()

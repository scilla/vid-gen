#!/usr/bin/env python3
import os
import logging
from pathlib import Path

# Import our modules
from video_generator import VideoGenerator
from log_config import setup_colored_logging

# Configure colored logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger('test')

# Create mock data for a video
def main():
    logger.info("Starting test video generation with filename formatting")
    
    # Initialize the video generator
    video_generator = VideoGenerator()
    
    # Create mock data (similar to what the real script produces)
    headline = "Test Headline With Special Ch@r$ and Numbers 123"
    
    # Create a basic slide structure with dummy data
    # This would normally come from API calls, but we're mocking it for testing
    test_img_path = Path(__file__).parent / "test_assets"
    test_img_path.mkdir(exist_ok=True)
    
    # Create a text file as a placeholder if no images exist yet
    test_img = test_img_path / "test_image.txt"
    if not test_img.exists():
        with open(test_img, "w") as f:
            f.write("Test image placeholder")
    
    test_audio = test_img_path / "test_audio.txt"
    if not test_audio.exists():
        with open(test_audio, "w") as f:
            f.write("Test audio placeholder")
    
    # Mock data that would normally come from image/audio generation
    mock_results = {
        0: {
            "slide": {"title": "Test Slide", "voiceOver": "Test voice over"},
            "image": b"Sample image data",
            "audio": b"Sample audio data"
        }
    }
    
    # Call the video generator with the headline to test filename generation
    logger.info(f"Testing with headline: '{headline}'")
    output_path = video_generator.generate_video(
        mock_results, 
        headline=headline,
        preview_mode=True
    )
    
    logger.info(f"Video would be generated at: {output_path}")
    logger.info("Test completed - check that the filename format is correct")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import base64
import logging
import json
import tempfile
import re
import datetime
from pathlib import Path

# Import the local generator module
from generator import assemble_video, PREVIEW_RESOLUTION, FULL_RESOLUTION

# Use logger from centralized config
from log_config import setup_colored_logging
logger = logging.getLogger('video_generator')

# Ensure outputs directory exists
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

class VideoGenerator:
    def __init__(self, video_gen_url=None):
        # video_gen_url parameter is kept for backward compatibility but not used
        # as we're now using the local generator module
        pass
    
    def generate_video(self, all_results, output_filename=None, preview_mode=False, headline=None):
        logger.info("Generating final video")
        
        # Check if any valid results exist
        valid_results = {i: result for i, result in all_results.items() 
                      if result["image"] is not None and result["audio"] is not None}
        
        if not valid_results:
            logger.error("No valid results to generate video. All API calls failed.")
            return False
            
        logger.info(f"Proceeding with {len(valid_results)} valid slides out of {len(all_results)} total")
        
        # Create output filename with timestamp and headline if provided
        if output_filename is None:
            # Get current timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Process headline if available
            headline_part = ""
            if headline:
                # Keep only a-z and A-Z characters from headline
                clean_headline = re.sub(r'[^a-zA-Z]', '', headline)
                # Truncate to 20 characters
                headline_part = clean_headline[:20]
            
            # Construct filename
            output_filename = f"{timestamp}_{headline_part}.mp4" if headline_part else f"{timestamp}_video.mp4"
        
        # Ensure output is in the outputs directory
        output_path = OUTPUT_DIR / output_filename
        logger.info(f"Video will be saved as {output_path}")
        
        # Create temporary directory for assets
        temp_dir = tempfile.mkdtemp()
        try:
            # Prepare slide definitions
            slide_defs = []
            
            # Save images and audio to disk
            for i in sorted(valid_results.keys()):
                # Save image
                image_path = os.path.join(temp_dir, f"image{i+1}.jpg")
                with open(image_path, "wb") as f:
                    # Base64 decode if needed
                    if isinstance(valid_results[i]["image"], str):
                        f.write(base64.b64decode(valid_results[i]["image"]))
                    else:
                        f.write(valid_results[i]["image"])
                
                # Save audio
                audio_path = os.path.join(temp_dir, f"audio{i+1}.mp3")
                with open(audio_path, "wb") as f:
                    f.write(valid_results[i]["audio"])
                
                # Add to slide definitions
                slide_defs.append({
                    "image": image_path,
                    "audio": audio_path
                })
            
            logger.info(f"Prepared {len(slide_defs)} slides for video generation")
            
            # Temporarily modify generator settings
            import generator
            original_output = generator.OUTPUT_FILENAME
            original_resolution = generator.RESOLUTION
            
            try:
                # Set new generator settings
                generator.OUTPUT_FILENAME = str(output_path)
                generator.RESOLUTION = PREVIEW_RESOLUTION if preview_mode else FULL_RESOLUTION
                
                # Call the generator directly
                logger.info("Assembling video with local generator")
                assemble_video(slide_defs)
                logger.info(f"Video saved as {output_path}")
                return str(output_path)  # Return the full path to the video file
                
            finally:
                # Restore original settings
                generator.OUTPUT_FILENAME = original_output
                generator.RESOLUTION = original_resolution
                
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
            return False
            
        finally:
            # Clean up temporary files
            import shutil
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")

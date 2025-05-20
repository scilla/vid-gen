#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from pydantic import BaseModel
import uvicorn
import os
from pyngrok import ngrok
import shutil
from pathlib import Path
import uuid
import base64
from io import BytesIO
import logging

# Import generator functions and logging config
from generator import assemble_video, FULL_RESOLUTION, PREVIEW_RESOLUTION, FPS, TRANSITION_DURATION
from log_config import setup_colored_logging

app = FastAPI(title="Video Generator API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure colored logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger('main')

# Create directories for files
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class Base64Media(BaseModel):
    filename: str
    data: str  # base64 encoded data

class GenerateVideoRequest(BaseModel):
    images: List[Base64Media]
    audios: List[Base64Media]
    preview_mode: bool = True

@app.post("/generate")
async def generate_video(
    images: List[UploadFile] = File(...),
    audios: List[UploadFile] = File(...),
    preview_mode: bool = Form(True)
):
    """
    Generate a video from the provided images and audio files and return the video file directly.
    - images: List of image files
    - audios: List of audio files (must match number of images)
    - preview_mode: Whether to use preview resolution (faster) or full resolution
    """
    return await process_video_generation(images, audios, preview_mode)

@app.post("/generate-base64")
async def generate_video_base64(request: GenerateVideoRequest):
    """
    Generate a video from base64 encoded images and audio data and return the video file directly.
    - images: List of base64 encoded image data with filenames
    - audios: List of base64 encoded audio data with filenames
    - preview_mode: Whether to use preview resolution (faster) or full resolution
    """
    try:
        # Create temporary file-like objects from base64 data
        temp_images = []
        temp_audios = []
        
        for img in request.images:
            # Create UploadFile-like object with BytesIO
            binary_data = base64.b64decode(img.data)
            temp_img = UploadFile(file=img.filename)
            temp_img.file = BytesIO(binary_data)
            temp_images.append(temp_img)
            
        for audio in request.audios:
            # Create UploadFile-like object with BytesIO
            binary_data = base64.b64decode(audio.data)
            temp_audio = UploadFile(file=audio.filename)
            temp_audio.file = BytesIO(binary_data)
            temp_audios.append(temp_audio)
        
        # Use the same processing function as the regular endpoint
        return await process_video_generation(temp_images, temp_audios, request.preview_mode)
        
    except Exception as e:
        logger.error(f"Error processing base64 data: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

async def process_video_generation(images, audios, preview_mode):
    """
    Generate a video from the provided images and audio files and return the video file directly.
    - images: List of image files
    - audios: List of audio files (must match number of images)
    - preview_mode: Whether to use preview resolution (faster) or full resolution
    """
    try:
        # Validate input
        if len(images) != len(audios):
            raise HTTPException(
                status_code=400, 
                detail=f"Number of images ({len(images)}) must match number of audios ({len(audios)})"
            )
        
        # Generate a unique ID for this job
        job_id = str(uuid.uuid4())
        
        # Create output filename and path
        filename = f"{job_id}.mp4"
        output_path = OUTPUT_DIR / filename
        
        # Save uploaded files
        slide_defs = []
        for i, (image, audio) in enumerate(zip(images, audios)):
            # Save image
            image_subdir = UPLOAD_DIR / "images"
            image_subdir.mkdir(exist_ok=True)
            image_filename = f"{job_id}_{i}_{image.filename}"
            image_path = image_subdir / image_filename
            
            # Reset file pointer if it's been read before
            image.file.seek(0)
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            # Save audio
            audio_subdir = UPLOAD_DIR / "audio"
            audio_subdir.mkdir(exist_ok=True)
            audio_filename = f"{job_id}_{i}_{audio.filename}"
            audio_path = audio_subdir / audio_filename
            
            # Reset file pointer if it's been read before
            audio.file.seek(0)
            with open(audio_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)
            
            # Add to slide definitions
            slide_defs.append({
                "image": str(image_path),
                "audio": str(audio_path)
            })
        
        # Set resolution based on preview mode
        resolution = PREVIEW_RESOLUTION if preview_mode else FULL_RESOLUTION
        
        # Keep track of temp files to clean up later
        temp_files = []
        for slide_def in slide_defs:
            temp_files.append(slide_def["image"])
            temp_files.append(slide_def["audio"])
        
        # Modify generator settings for this job
        import generator
        original_output = generator.OUTPUT_FILENAME
        original_resolution = generator.RESOLUTION
        
        try:
            # Update generator settings
            generator.OUTPUT_FILENAME = str(output_path)
            generator.RESOLUTION = resolution
            
            # Generate the video synchronously
            logger.info(f"Starting video generation for job {job_id}")
            assemble_video(slide_defs)
            logger.info(f"Video generation completed for job {job_id}")
            
        finally:
            # Restore original settings
            generator.OUTPUT_FILENAME = original_output
            generator.RESOLUTION = original_resolution
            
        # Clean up temporary files after successful generation
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")
        
        # Return the video file directly
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type="video/mp4"
        )
        
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        
        # Clean up temporary files in case of error, but only if job_id is defined
        try:
            if 'job_id' in locals() and 'slide_defs' in locals(): 
                # If we've already created the slide_defs, remove those specific files
                for slide_def in slide_defs:
                    if os.path.exists(slide_def["image"]):
                        os.remove(slide_def["image"])
                    if os.path.exists(slide_def["audio"]):
                        os.remove(slide_def["audio"])
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")
            
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

if __name__ == "__main__":
    # Open a ngrok tunnel to the HTTP server
    port = 8000
    public_url = ngrok.connect(port).public_url
    print(f"ngrok tunnel opened at {public_url} -> http://localhost:{port}")
    print("To access your API directly: " + public_url + "/generate-base64")
    
    # Start the FastAPI application
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

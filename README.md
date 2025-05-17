# Video Generator

A tool that creates videos with sliding image transitions and audio narration. Includes both a command-line generator and a FastAPI web server for remote video generation.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure FFmpeg is installed on your system.

## Usage

### Command Line

Run the generator directly:

```bash
python generator.py
```

This uses the slides defined in the script to generate a video.

### API Server

Start the API server:

```bash
python main.py
```

The server runs on port 8000 by default and provides a single endpoint:

```
POST /generate
```

#### Example API request with curl:

```bash
curl -X POST "http://localhost:8000/generate" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "audios=@audio1.m4a" \
  -F "audios=@audio2.m4a" \
  -F "preview_mode=true" \
  --output video.mp4
```

## How It Works

1. Images and audio files are processed into slides
2. Each image is sized to fit the video resolution
3. Transitions slide images in from the right
4. Audio narration plays with each slide
5. The final video is rendered using FFmpeg

## Configuration

- `PREVIEW_MODE`: Set to `true` for faster, lower-resolution output (360x640)
- `FULL_RESOLUTION`: High-quality output (1080x1920)
- `TRANSITION_DURATION`: Slide transition time in seconds

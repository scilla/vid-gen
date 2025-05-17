#!/usr/bin/env python3.13
import sys
import os

import shutil
from moviepy import (
	ImageClip,
	AudioFileClip,
	CompositeVideoClip,
	ColorClip,
	vfx,
	CompositeAudioClip,
)

if shutil.which("ffmpeg") is None:
	sys.stderr.write("Error: FFmpeg not found. Please install FFmpeg.\n")
	sys.exit(1)

# Configuration (hard-coded)
PREVIEW = True  # Set to True for low-res previews, False for final output

slides = [
	{"image": "IMG_3098.jpg", "audio": "slide1.m4a"},
	{"image": "IMG_3099.jpg", "audio": "slide2.m4a"},
	# Add more slides here…
]
OUTPUT_FILENAME = "output.mp4"

# Resolution settings
FULL_RESOLUTION = (1080, 1920)  # width, height
PREVIEW_RESOLUTION = (360, 640)  # lower resolution for preview
RESOLUTION = PREVIEW_RESOLUTION if PREVIEW else FULL_RESOLUTION

FPS = 30
TRANSITION_DURATION = 0.5  # seconds

def load_slides():
	"""
	Return the list of slides. Exits if none found.
	"""
	if not slides:
		sys.stderr.write("Error: No slides defined in script.\n")
		sys.exit(1)
	return slides

def load_image(image_path, resolution):
	"""
	Load image and resize to fit the height of the resolution.
	"""
	if not os.path.isfile(image_path):
		sys.stderr.write(f"Error: Image file not found: {image_path}\n")
		sys.exit(1)

	try:
		# Load image and resize to fit the height while maintaining aspect ratio
		img = ImageClip(image_path)
		resized_img = img.with_effects([vfx.Resize(height=resolution[1])])
		return resized_img
	except Exception as e:
		sys.stderr.write(f"Error processing image {image_path}: {e}\n")
		sys.exit(1)

def load_audio(audio_path):
	"""
	Load audio file.
	"""
	if not os.path.isfile(audio_path):
		sys.stderr.write(f"Error: Audio file not found: {audio_path}\n")
		sys.exit(1)

	return AudioFileClip(audio_path)

def slide_right(clip, duration):
	"""
	Create a transform effect that slides from right to center.
	"""
	# Calculate center position
	center_x = int(RESOLUTION[0] / 2 - clip.size[0] / 2)
	
	def get_frame_position(t):
		if t < duration: 
			# During transition: slide from right to center
			# Start offscreen (RESOLUTION[0]) and move to center
			progress = t / duration  # 0 to 1
			start_x = RESOLUTION[0] 
			x_pos = int(start_x - progress * (start_x - center_x))
			return (x_pos, 'center')
		else:
			# After transition: stay at center position
			return (center_x, 'center')
	
	return clip.with_position(get_frame_position)

def assemble_video(slide_defs):
	"""
	Builds the timeline with sliding transitions and writes output MP4.
	"""
	if not slide_defs:
		sys.stderr.write("Error: No slides to process.\n")
		sys.exit(1)
	
	# Create a list to hold all clips
	all_clips = []
	total_time = 0
	
	# Calculate audio durations
	audio_clips = []
	audio_durations = []
	for slide_def in slide_defs:
		audio = load_audio(slide_def["audio"])
		audio_clips.append(audio)
		audio_durations.append(audio.duration)
	
	# Calculate start times for each slide
	start_times = [0]  # First slide starts at 0
	
	# Calculate start times for slides after the first one
	for i in range(len(slide_defs) - 1):
		start_time = start_times[i] + audio_durations[i] - TRANSITION_DURATION
		start_times.append(start_time)
		total_time = start_time + audio_durations[i+1]
	
	# For the last slide, add its duration to get total duration
	if len(slide_defs) == 1:
		total_time = audio_durations[0]
	
	# Create the black background that spans the entire video
	background = ColorClip(size=RESOLUTION, color=(0, 0, 0)).with_duration(total_time)
	all_clips.append(background)
	
	# Process each slide
	for i, slide_def in enumerate(slide_defs):
		# Load the image
		img = load_image(slide_def["image"], RESOLUTION)
		
		# Set duration - until the end of its audio
		duration = total_time - start_times[i] if i == len(slide_defs) - 1 else audio_durations[i]
		img = img.with_duration(duration)
		
		# Apply transition effect for all slides except the first one
		if i == 0:
			# First slide is centered from the start
			img = img.with_position("center")
		else:
			# Add sliding transition
			img = slide_right(img, TRANSITION_DURATION)
		
		# Set the start time
		img = img.with_start(start_times[i])
		all_clips.append(img)
	
	# Create audio tracks
	combined_audio_clips = []
	for i, audio in enumerate(audio_clips):
		combined_audio_clips.append(audio.with_start(start_times[i]))
	
	# Create the final composite with all visual elements
	final_video = CompositeVideoClip(all_clips, size=RESOLUTION)
	
	# Add all audio tracks
	final_audio = CompositeAudioClip(combined_audio_clips)
	final_video = final_video.with_audio(final_audio)
	
	# Determine audio sample rate
	srates = {audio.fps for audio in audio_clips}
	if len(srates) > 1:
		sys.stderr.write(f"Warning: varying audio sample rates {srates}, using {max(srates)} Hz\n")
	audio_fps = max(srates) if srates else 44100
	
	# Write final video
	final_video.write_videofile(
		OUTPUT_FILENAME,
		fps=FPS,
		codec="libx264",
		audio_codec="aac",
		audio_fps=audio_fps,
		temp_audiofile="temp-audio.m4a",
		remove_temp=True,
		ffmpeg_params=["-movflags", "+faststart"]
	)

def main():
	slide_defs = load_slides()
	try:
		print(f"Generating video {'in PREVIEW mode' if PREVIEW else 'in FULL QUALITY'} at {RESOLUTION[0]}x{RESOLUTION[1]}")
		assemble_video(slide_defs)
	except Exception as e:
		sys.stderr.write(f"Error: {e}\n")
		sys.exit(1)

if __name__ == "__main__":
	main()

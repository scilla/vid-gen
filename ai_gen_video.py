#!/usr/bin/env python3
import os
import re
import time
import glob
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Import our modules
from api_services import APIServices
from cache_manager import CacheManager
from video_generator import VideoGenerator
from log_config import setup_colored_logging

# Configure colored logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger('ai_gen_video')

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not RAPIDAPI_KEY or not OPENAI_API_KEY:
	logger.critical("You must set RAPIDAPI_KEY and OPENAI_API_KEY in your environment")
	exit(1)

# Initialize services
api_services = APIServices(OPENAI_API_KEY, RAPIDAPI_KEY)
cache_manager = CacheManager(cache_dir="./cache")
video_generator = VideoGenerator()  # No URL needed, using local generator

# ──────────────────────────────────────────────────────────────────────────────
#  Helper functions that utilize caching
# ──────────────────────────────────────────────────────────────────────────────


def get_or_fetch_headlines(country="IT", lang="it", limit=15, topic="WORLD", fresh=False): # WORLD, NATIONAL, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH
	# For testing purposes, we're now caching headlines
	# Check cache first (unless fresh=True)
	if not fresh:
		cached_headlines = cache_manager.get_headlines(country, lang, limit, topic)
		if cached_headlines:
			logger.info(f"Using cached headlines for topic={topic}, country={country}, lang={lang}")
			return cached_headlines
	
	# If fresh=True or not in cache, fetch from API
	if fresh:
		logger.info(f"Forcing fresh headlines fetch for topic={topic}, country={country}, lang={lang}")
	
	headlines = api_services.fetch_headlines(country, lang, limit, topic)
	if headlines:
		cache_manager.save_headlines(country, lang, limit, headlines, topic)
	return headlines

def get_or_extract_article(url):
	"""Get article from cache or extract it via API"""
	# Check cache first
	cached_article = cache_manager.get_article(url)
	if cached_article:
		return cached_article
	
	# If not in cache, fetch from API
	article = api_services.extract_article(url)
	if article:
		cache_manager.save_article(url, article)
	return article

def get_or_generate_summary(article):
	"""Get summary from cache or generate via OpenAI"""
	# Check cache first
	cached_summary = cache_manager.get_summary(article) 
	if cached_summary:
		return cached_summary
	
	# If not in cache, generate with OpenAI
	summary = api_services.generate_summary(article)
	if summary:
		cache_manager.save_summary(article, summary)
	return summary

def get_or_generate_tts(text, idx):
	"""Get TTS audio from cache or generate via API"""
	# Check cache first
	cached_audio = cache_manager.get_tts(text)
	if cached_audio:
		logger.info(f"Using cached TTS audio for slide {idx}")
		return cached_audio
	
	# If not in cache, generate with API
	audio = api_services.generate_tts(text)
	if audio:
		cache_manager.save_tts(text, audio)
	return audio

def get_or_generate_image(img_prompt, title, idx):
	"""Get image from cache or generate via API"""
	# Create full prompt with title
	full_prompt = (
		f"{img_prompt}. Add white subtitles with black border: \"{title}\". "
		"The subtitles should be well inside the picture frame and should use consistent font and size. "
		"Put in the upper of image."
	)
	
	# Check cache first
	cached_image = cache_manager.get_image(full_prompt)
	if cached_image:
		logger.info(f"Using cached image for slide {idx}")
		return cached_image
	
	# If not in cache, generate with API
	try:
		image = api_services.generate_image(img_prompt, title)
		if image:
			cache_manager.save_image(full_prompt, image)
		return image
	except Exception as e:
		# If image generation fails, delete any partial cache entries
		cache_manager.delete_image(full_prompt)
		logger.error(f"Failed to generate image for slide {idx}: {e}")
		return None

# ──────────────────────────────────────────────────────────────────────────────
#  MAIN WORKFLOW
# ──────────────────────────────────────────────────────────────────────────────
def main():
	logger.info("Starting main workflow")
	try:
		# Fetch all headlines
		headlines = get_or_fetch_headlines(country="IT", lang="it", limit=15, topic="WORLD", fresh=False)
		if not headlines:
			logger.error("No articles available.")
			return False
		
		logger.info(f"Retrieved {len(headlines)} headlines")
		
		# Ensure outputs directory exists
		outputs_dir = Path("outputs")
		outputs_dir.mkdir(exist_ok=True)
		
		# Track if we found any new article to process
		processed_article = False
		
		# Check each headline
		for i, article in enumerate(headlines):
			headline_text = article.get('title', 'No title')
			logger.info(f"Checking article {i+1}/{len(headlines)}: {headline_text}")
			
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
			processed_article = True
			# The rest of the code proceeds with this article

			# extract & summarize
			extracted = get_or_extract_article(article["link"])
			if not extracted:
				logger.error("Failed to extract article content")
				continue  # Try next article
			
			summary_json = get_or_generate_summary(extracted)
			if not summary_json or "slides" not in summary_json:
				logger.error("Failed to generate summary JSON")
				continue  # Try next article
			
			slides = summary_json["slides"]
			logger.info(f"Processed summary with {len(slides)} slides")

			# prepare containers
			slide_data = [
				{"title": s["title"], "voiceOver": s["voiceOver"], "imgPrompt": s["imgPrompt"]}
				for s in slides
			]
			results = {i: {"slide": slide_data[i], "audio": None, "image": None}
			           for i in range(len(slide_data))}

			# parallel TTS + image generation with max 5 concurrent
			logger.info("Starting parallel TTS and image generation")
			with ThreadPoolExecutor(max_workers=5) as executor:
				futs = {}
				for i, s in enumerate(slide_data):
					# schedule TTS
					tf = executor.submit(get_or_generate_tts, s["voiceOver"], i)
					futs[tf] = ("audio", i)
					time.sleep(0.5)  # Reduced sleep time since we use caching

					# schedule Image
					inf = executor.submit(get_or_generate_image, s["imgPrompt"], s["title"], i)
					futs[inf] = ("image", i)
					time.sleep(0.5)  # Reduced sleep time since we use caching

				# collect results
				logger.info("Waiting for all generation tasks to complete")
				error_occurred = False
				image_generation_failed = False  # Track if any image generation failed
				for fut in as_completed(futs):
					kind, idx = futs[fut]
					try:
						res = fut.result()
						if res is None:
							logger.error(f"No content received for {kind} slide {idx}")
							error_occurred = True
							# Mark image generation as failed if this was an image
							if kind == "image":
								image_generation_failed = True
							continue
							
						results[idx][kind] = res
						logger.info(f"Successfully processed {kind} for slide {idx}")
					except Exception as e:
						logger.error(f"Error processing {kind} for slide {idx}: {e}", exc_info=True)
						error_occurred = True
						# Mark image generation as failed if this was an image
						if kind == "image":
							image_generation_failed = True

				# If any image generation failed, invalidate the summary cache
				if image_generation_failed:
					logger.warning("At least one image generation failed, invalidating summary cache")
					cache_manager.delete_summary(extracted)
				
				# Stop execution if any errors occurred
				if error_occurred:
					logger.error("Errors occurred during content generation, stopping execution")
					continue  # Try next article

				# Check if we have all assets for all slides
				incomplete_slides = [i for i, result in results.items() 
								if result["image"] is None or result["audio"] is None]
					
				if incomplete_slides:
					logger.error(f"Missing assets for slides: {incomplete_slides}")
					continue  # Try next article
				
				# final assembly
				logger.info("All assets processed, proceeding to final video assembly")
				# Pass the headline for the output filename
				headline_text = article.get('title', '')
				video_path = video_generator.generate_video(results, headline=headline_text, preview_mode=False)
				
				if video_path:
					logger.info(f"Video assembly completed successfully: {video_path}")
					break  # Successfully processed an article, so stop the loop
				else:
					logger.error("Video assembly failed")
					continue  # Try next article
		
		# If we checked all headlines and found none to process
		if not processed_article:
			logger.info("All articles already have videos generated")
			return None
		
		# If we reached here, we successfully processed one article
		return True
	except Exception as e:
		logger.error(f"Error in main workflow: {e}", exc_info=True)
		return False

if __name__ == "__main__":
	logger.info("Starting ai_gen_video script")
	try:
		success = main()
		if success:
			logger.info("Script execution completed successfully")
		elif success is None:
			logger.info("No new articles to process - all have been generated")
		else:
			logger.warning("Script execution completed with errors")
	except Exception as e:
		logger.critical(f"Script execution failed: {e}", exc_info=True)
		exit(1)

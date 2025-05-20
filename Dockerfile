FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for moviepy and other packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install python-dotenv separately
RUN pip install --no-cache-dir python-dotenv

# Copy application code
COPY . .

# Create directories for cache and temporary files
RUN mkdir -p /app/temp /app/cache /app/static

# Create an entrypoint script that checks for required environment variables
RUN echo '#!/bin/bash\n\
if [ -z "$OPENAI_API_KEY" ]; then\n\
  echo "Error: OPENAI_API_KEY environment variable is not set"\n\
  exit 1\n\
fi\n\
if [ -z "$RAPIDAPI_KEY" ]; then\n\
  echo "Error: RAPIDAPI_KEY environment variable is not set"\n\
  exit 1\n\
fi\n\
exec "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Expose the port the app will run on
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

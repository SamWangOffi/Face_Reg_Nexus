# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only necessary files first (to leverage cache)
COPY requirements.txt ./

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Expose Flask ports
EXPOSE 5000
EXPOSE 6000

# Default command (can be customized)
CMD ["python", "people_counting_api/people_track_rtsp.py"]

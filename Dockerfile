# ==============================================================================
# StockAI SaaS / AI Stock Action Agent — Production Dockerfile
# ==============================================================================

# Use official lightweight Python base image
FROM python:3.11-slim-buster

# Prevent Python from writing .pyc files and enable unbuffered output logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    TRANSFORMERS_CACHE=/app/cache/huggingface

# Set up working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling certain libraries (optional but safe)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies including Gunicorn for production WSGI server
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Pre-cache the FinBERT model weights at build time
# This eliminates cold starts and network latency during first-request inferences
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
    AutoTokenizer.from_pretrained('yiyanghkust/finbert-tone'); \
    AutoModelForSequenceClassification.from_pretrained('yiyanghkust/finbert-tone')"

# Copy the rest of the application files to the container
COPY . .

# Expose the default port (Render/Cloud Run dynamically map this to $PORT)
EXPOSE 5000

# Start the application using a production Gunicorn WSGI server
# Runs 2 worker threads (adjust depending on core capacity)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--threads", "2", "--timeout", "120"]

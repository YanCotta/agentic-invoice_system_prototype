FROM python:3.12-slim

# Install system dependencies including Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# Expose ports for reference (not strictly necessary with docker-compose)
EXPOSE 8000 8501

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
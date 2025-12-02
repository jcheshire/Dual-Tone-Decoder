#!/bin/bash

# Dual-Tone Decoder startup script

echo "Starting Dual-Tone Decoder..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

echo "Starting server on http://0.0.0.0:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

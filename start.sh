#!/bin/bash
set -e  # Exit on error

# Dual-Tone Decoder startup script

echo "============================================"
echo "  Dual-Tone Decoder - Startup"
echo "============================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
    echo "Installing dependencies (this may take a few minutes)..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "✓ Virtual environment found"
    source venv/bin/activate
fi

echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ Configuration file created (.env)"
    echo "  You can edit .env to customize settings"
else
    echo "✓ Configuration file exists (.env)"
fi

echo ""

# Create uploads directory if it doesn't exist
mkdir -p uploads
echo "✓ Upload directory ready"

echo ""
echo "============================================"
echo "  Starting FastAPI Backend Server"
echo "============================================"
echo ""
echo "Backend API: http://localhost:8000/api"
echo "Web Interface: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"
echo ""

# Start the FastAPI backend server with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

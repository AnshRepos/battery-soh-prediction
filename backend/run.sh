#!/bin/bash

# Battery Dashboard Backend - Local Run Script

set -e

echo "Starting Battery Dashboard Backend..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Start the Flask development server
echo ""
echo "Starting Flask development server..."
echo "API will be available at http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py

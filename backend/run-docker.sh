#!/bin/bash

# Battery Dashboard Backend - Docker Run Script

set -e

echo "Battery Dashboard Backend - Docker Deployment"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker to proceed."
    exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -t battery-dashboard-backend:latest .

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Run the container
echo ""
echo "Starting Docker container..."
echo "API will be available at http://localhost:5000"
echo ""

docker run \
    --name battery-dashboard-backend \
    -p 5000:5000 \
    --env-file .env \
    -v \C:\Users\Ansh Narang\OneDrive\Desktop\battery-dashboard\backend:/app \
    battery-dashboard-backend:latest

echo ""
echo "To stop the container, press Ctrl+C or run:"
echo "docker stop battery-dashboard-backend"
echo ""
echo "To remove the container, run:"
echo "docker rm battery-dashboard-backend"

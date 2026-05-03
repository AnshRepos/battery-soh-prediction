# Backend Setup Guide

This guide explains how to set up and run the Battery Dashboard backend locally and with Docker.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Docker and Docker Compose (for containerized setup)
- Node.js (for frontend development)

## Local Development Setup

### 1. Navigate to Backend Directory

\\\ash
cd backend
\\\

### 2. Create Virtual Environment

\\\ash
python -m venv venv
\\\

### 3. Activate Virtual Environment

**On Windows:**
\\\ash
venv\Scripts\activate
\\\

**On macOS/Linux:**
\\\ash
source venv/bin/activate
\\\

### 4. Install Dependencies

\\\ash
pip install -r requirements.txt
\\\

### 5. Environment Configuration

Create a \.env\ file in the backend directory:

\\\nv
FLASK_ENV=development
FLASK_DEBUG=True
API_PORT=5000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DATABASE_URL=sqlite:///battery_dashboard.db
LOG_LEVEL=DEBUG
\\\

### 6. Initialize Database

\\\ash
python -m flask db upgrade
\\\

Or if using custom scripts:

\\\ash
python scripts/init_db.py
\\\

### 7. Run Development Server

\\\ash
python -m flask run --port=5000
\\\

The API will be available at \http://localhost:5000\

## Docker Setup

### 1. Build Docker Image

\\\ash
docker build -t battery-dashboard-backend .
\\\

### 2. Run Docker Container

\\\ash
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e CORS_ORIGINS=http://localhost:5173,http://localhost:3000 \
  battery-dashboard-backend
\\\

### 3. Using Docker Compose

Create a \docker-compose.yml\ in the project root:

\\\yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - API_PORT=5000
      - CORS_ORIGINS=http://localhost:5173
      - DATABASE_URL=sqlite:///battery_dashboard.db
    volumes:
      - ./backend/instance:/app/instance
    networks:
      - battery-network

  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:5000
    depends_on:
      - backend
    networks:
      - battery-network

networks:
  battery-network:
    driver: bridge
\\\

Run with Docker Compose:

\\\ash
docker-compose up -d
\\\

## API Endpoints

The backend provides the following endpoints:

### Health Check
- \GET /api/health\ - Check if backend is running

### Models
- \GET /api/models\ - Get all models
- \GET /api/models/:id\ - Get specific model
- \POST /api/models\ - Create new model
- \PUT /api/models/:id\ - Update model
- \DELETE /api/models/:id\ - Delete model

### Metrics
- \GET /api/metrics\ - Get metrics for a model
- \GET /api/metrics/aggregated\ - Get aggregated metrics
- \GET /api/metrics/historical\ - Get historical data

### Predictions
- \GET /api/predictions\ - Get predictions
- \POST /api/predictions\ - Create prediction
- \GET /api/predictions/:id\ - Get specific prediction
- \PUT /api/predictions/:id\ - Update prediction status
- \GET /api/predictions/date-range\ - Get predictions by date range

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure:
- The backend's \CORS_ORIGINS\ environment variable includes your frontend URL
- The frontend's \VITE_API_BASE_URL\ is correctly configured
- The backend is running on the expected port

### Port Already in Use

If port 5000 is already in use:

\\\ash
# Find process using port 5000
lsof -i :5000

# Change port in .env or command
python -m flask run --port=5001
\\\

### Database Issues

To reset the database:

\\\ash
# Remove existing database
rm instance/battery_dashboard.db

# Reinitialize
python -m flask db upgrade
\\\

## Environment Variables

Key environment variables for configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | development | Flask environment (development/production) |
| FLASK_DEBUG | True | Enable debug mode |
| API_PORT | 5000 | Port for API server |
| CORS_ORIGINS | http://localhost:5173 | Allowed CORS origins |
| DATABASE_URL | sqlite:///battery_dashboard.db | Database connection URL |
| LOG_LEVEL | DEBUG | Logging level |

## Performance Optimization

For production:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Enable caching headers on responses
3. Use a real database (PostgreSQL, MySQL)
4. Set up proper logging and monitoring
5. Enable HTTPS/SSL

## Support

For issues or questions, check the project's issue tracker or documentation.

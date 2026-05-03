# Battery Dashboard Backend API

## Overview

The Battery Dashboard Backend is a Flask-based REST API for predicting and monitoring battery health metrics. It provides endpoints for health predictions, performance comparisons, and metrics retrieval using machine learning models.

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip or conda
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository
2. Navigate to the backend directory
3. Install dependencies:

\\\ash
pip install -r requirements.txt
\\\

### Running Locally

Run the development server:

\\\ash
python app.py
\\\

Or use the provided script:

\\\ash
bash run.sh
\\\

The server will start on \http://localhost:5000\ by default.

## API Endpoints

### Health Check

**GET /api/health**

Returns the health status of the API.

**Example:**
\\\ash
curl -X GET http://localhost:5000/api/health
\\\

**Response:**
\\\json
{
  "status": "healthy"
}
\\\

### Predict Battery Health

**POST /api/predict**

Predicts battery health based on input parameters.

**Request Body:**
\\\json
{
  "temperature": 25.5,
  "voltage": 3.7,
  "current": 0.5,
  "cycle_count": 100,
  "impedance": 0.05
}
\\\

**Example:**
\\\ash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 25.5,
    "voltage": 3.7,
    "current": 0.5,
    "cycle_count": 100,
    "impedance": 0.05
  }'
\\\

**Response:**
\\\json
{
  "prediction": {
    "health_status": "Good",
    "soh_percentage": 85.5,
    "remaining_cycles": 450,
    "confidence": 0.92
  }
}
\\\

### Get Metrics

**GET /api/metrics**

Retrieves comprehensive system and performance metrics.

**Example:**
\\\ash
curl -X GET http://localhost:5000/api/metrics
\\\

**Response:**
\\\json
{
  "model_accuracy": 0.94,
  "predictions_count": 1250,
  "average_prediction_time": 0.045,
  "system_uptime": 3600
}
\\\

## Environment Configuration

Configure the application using the \.env\ file. Copy the \.env.example\ file and update values:

\\\ash
cp .env.example .env
\\\

Key configuration variables:
- \FLASK_ENV\: Development or production mode
- \FLASK_DEBUG\: Enable debug mode
- \API_HOST\: Server host (default: 0.0.0.0)
- \API_PORT\: Server port (default: 5000)

## Docker Deployment

### Build and Run with Docker

\\\ash
bash run-docker.sh
\\\

Or manually:

\\\ash
docker build -t battery-dashboard-backend .
docker run -p 5000:5000 battery-dashboard-backend
\\\

### Using Docker Compose

\\\ash
docker-compose up --build
\\\

## Testing

Run the test suite:

\\\ash
python tests.py
\\\

Or using pytest:

\\\ash
pytest tests.py -v
\\\

## Project Structure

\\\
backend/
├── app.py              # Flask application entry point
├── config.py           # Configuration management
├── wsgi.py             # WSGI entry point
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── run.sh              # Local run script
├── run-docker.sh       # Docker run script
├── tests.py            # Test suite
├── README.md           # This file
├── models/             # ML models and model utilities
├── services/           # Business logic services
│   ├── prediction_service.py
│   └── metrics_service.py
└── utils/              # Utility functions and helpers
`

## Services

### Prediction Service

Located in \services/prediction_service.py\. Handles battery health predictions using trained ML models.

### Metrics Service

Located in \services/metrics_service.py\. Provides system and model performance metrics.

## Error Handling

The API returns standard HTTP status codes:
- \200 OK\: Successful request
- \400 Bad Request\: Invalid input or processing error
- \500 Internal Server Error\: Unexpected server error

Error responses include a message:
\\\json
{
  "error": "Description of the error"
}
\\\

## Performance

- Average prediction latency: ~45ms
- Supports concurrent predictions
- Optimized for production deployment

## Security

- CORS enabled for secure cross-origin requests
- Environment variables for sensitive configuration
- Input validation on all endpoints
- CSRF protection available

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify the PORT in \.env\ or run:
\\\ash
python app.py --port 5001
\\\

### TensorFlow Issues
Ensure TensorFlow is properly installed for your OS:
\\\ash
pip install --upgrade tensorflow
\\\

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Ensure all tests pass
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues, questions, or suggestions, please create an issue in the repository.

# Frontend-Backend API Integration Guide

This guide explains how to use the Battery Dashboard frontend to integrate with backend API endpoints.

## Configuration

### Environment Variables

Create or update \.env\ file in the project root:

\\\nv
VITE_API_BASE_URL=http://localhost:5000
\\\

For production:

\\\nv
VITE_API_BASE_URL=https://api.yourdomain.com
\\\

## API Client Setup

The API integration is located in \src/services/\:

- **apiClient.js** - Core HTTP client with error handling
- **backend.js** - Service functions for specific endpoints

### Using the API Client

The API client is automatically configured through environment variables. All requests are made to the base URL specified in \VITE_API_BASE_URL\.

## Service Usage Examples

### 1. Models Service

#### Get All Models

\\\javascript
import { modelsService } from '@/services/backend.js';
import { ref } from 'vue';

const isLoading = ref(false);

const fetchModels = async () => {
  const result = await modelsService.getAllModels(isLoading);
  
  if (result.success) {
    console.log('Models:', result.data);
  } else {
    console.error('Error:', result.message);
  }
};
\\\

#### Get Specific Model

\\\javascript
const modelId = '123';
const result = await modelsService.getModelById(modelId, isLoading);
\\\

#### Create Model

\\\javascript
const modelData = {
  name: 'Model A',
  type: 'lithium-ion',
  capacity: 5000,
  voltage: 12
};

const result = await modelsService.createModel(modelData, isLoading);
if (result.success) {
  console.log('Model created:', result.data);
}
\\\

#### Update Model

\\\javascript
const modelId = '123';
const updatedData = {
  name: 'Updated Model A',
  capacity: 5500
};

const result = await modelsService.updateModel(modelId, updatedData, isLoading);
\\\

#### Delete Model

\\\javascript
const modelId = '123';
const result = await modelsService.deleteModel(modelId, isLoading);
\\\

### 2. Metrics Service

#### Get Metrics for Model

\\\javascript
import { metricsService } from '@/services/backend.js';

const modelId = '123';
const result = await metricsService.getMetrics(modelId, isLoading);

if (result.success) {
  const metrics = result.data; // { accuracy: 0.95, precision: 0.92, ... }
}
\\\

#### Get Aggregated Metrics

\\\javascript
const result = await metricsService.getAggregatedMetrics(isLoading);

if (result.success) {
  const aggregatedMetrics = result.data; // Metrics across all models
}
\\\

#### Get Historical Metrics

\\\javascript
const modelId = '123';
const startDate = '2024-01-01';
const endDate = '2024-12-31';

const result = await metricsService.getHistoricalMetrics(
  modelId,
  startDate,
  endDate,
  isLoading
);
\\\

### 3. Predictions Service

#### Get Predictions

\\\javascript
import { predictionsService } from '@/services/backend.js';

const modelId = '123';
const result = await predictionsService.getPredictions(modelId, isLoading);

if (result.success) {
  const predictions = result.data; // Array of predictions
}
\\\

#### Create Prediction

\\\javascript
const predictionData = {
  model_id: '123',
  input_data: {
    temperature: 25,
    voltage: 12,
    current: 5
  },
  timestamp: new Date().toISOString()
};

const result = await predictionsService.createPrediction(predictionData, isLoading);
\\\

#### Get Prediction by ID

\\\javascript
const predictionId = 'pred-456';
const result = await predictionsService.getPredictionById(predictionId, isLoading);
\\\

#### Update Prediction Status

\\\javascript
const predictionId = 'pred-456';
const status = 'completed';

const result = await predictionsService.updatePredictionStatus(
  predictionId,
  status,
  isLoading
);
\\\

#### Get Predictions by Date Range

\\\javascript
const startDate = '2024-01-01';
const endDate = '2024-12-31';

const result = await predictionsService.getPredictionsForDateRange(
  startDate,
  endDate,
  isLoading
);
\\\

### 4. Health Check Service

\\\javascript
import { healthService } from '@/services/backend.js';

const result = await healthService.checkHealth();

if (result.success) {
  console.log('Backend is healthy');
} else {
  console.log('Backend is not available');
}
\\\

## Response Format

All API responses follow a consistent format:

\\\javascript
{
  success: boolean,        // true if request succeeded
  status: number,          // HTTP status code
  message: string,         // Status message
  data: any                // Response data or null
}
\\\

### Success Response

\\\javascript
{
  success: true,
  status: 200,
  message: 'Success',
  data: { /* actual data */ }
}
\\\

### Error Response

\\\javascript
{
  success: false,
  status: 404,
  message: 'Request failed with status 404',
  data: null
}
\\\

## Error Handling

The API client provides consistent error handling:

\\\javascript
const result = await modelsService.getAllModels(isLoading);

if (!result.success) {
  switch (result.status) {
    case 0:
      console.error('Network error or backend is offline');
      break;
    case 404:
      console.error('Resource not found');
      break;
    case 500:
      console.error('Server error');
      break;
    default:
      console.error(result.message);
  }
}
\\\

## Loading States

Use Vue ref for loading states in components:

\\\javascript
import { ref } from 'vue';
import { modelsService } from '@/services/backend.js';

export default {
  setup() {
    const isLoading = ref(false);
    const models = ref([]);
    const error = ref(null);

    const fetchModels = async () => {
      const result = await modelsService.getAllModels(isLoading);
      
      if (result.success) {
        models.value = result.data;
        error.value = null;
      } else {
        error.value = result.message;
      }
    };

    return {
      isLoading,
      models,
      error,
      fetchModels
    };
  }
};
\\\

### Template Usage

\\\ue
<template>
  <div>
    <button @click=\"fetchModels\" :disabled=\"isLoading\">
      {{ isLoading ? 'Loading...' : 'Fetch Models' }}
    </button>
    
    <div v-if=\"error\" class=\"error\">{{ error }}</div>
    
    <ul v-if=\"models.length\">
      <li v-for=\"model in models\" :key=\"model.id\">
        {{ model.name }}
      </li>
    </ul>
  </div>
</template>
\\\

## CORS Configuration

If you encounter CORS errors:

1. Ensure backend is running with correct CORS configuration
2. Backend should include frontend URL in CORS_ORIGINS
3. Update frontend API URL to match backend expectations

Example backend CORS setup:

\\\nv
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://yourdomain.com
\\\

## Best Practices

1. **Always check success status** before accessing response data
2. **Use loading states** to prevent duplicate requests
3. **Handle errors gracefully** with user-friendly messages
4. **Implement retry logic** for failed network requests
5. **Use TypeScript** for better type safety (optional but recommended)
6. **Cache responses** when appropriate to reduce API calls
7. **Log errors** for debugging and monitoring

## Debugging

### Enable API Logging

The API client logs errors to the console. Check browser DevTools for:

- Network tab to inspect requests/responses
- Console for error messages
- API client logs with endpoint and error details

### Test API Endpoints

Use tools like Postman or cURL to test endpoints directly:

\\\ash
# Health check
curl http://localhost:5000/api/health

# Get all models
curl http://localhost:5000/api/models

# Get specific model
curl http://localhost:5000/api/models/123
\\\

## Performance Tips

1. Implement pagination for large datasets
2. Use caching for frequently accessed data
3. Batch multiple API calls when possible
4. Compress request/response payloads
5. Use HTTP/2 for better performance

## Deployment

For production deployment:

1. Set \VITE_API_BASE_URL\ to production backend URL
2. Ensure HTTPS is used for API communication
3. Configure proper CORS headers
4. Implement request rate limiting
5. Set up proper error monitoring and logging

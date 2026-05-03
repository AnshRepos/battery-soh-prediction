/**
 * Backend API Service
 * 
 * This module provides service functions for interacting with backend endpoints.
 * It wraps the API client to provide a clean interface for models, metrics, and predictions.
 */

import apiClient from './apiClient.js';

/**
 * Models API Service
 */
export const modelsService = {
  /**
   * Get all available battery models
   */
  async getAllModels(loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.get('/api/models');
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Get a specific model by ID
   */
  async getModelById(modelId, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.get(\/api/models/\\);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Create a new model
   */
  async createModel(modelData, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.post('/api/models', modelData);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Update an existing model
   */
  async updateModel(modelId, modelData, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.put(\/api/models/\\, modelData);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Delete a model
   */
  async deleteModel(modelId, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.delete(\/api/models/\\);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },
};

/**
 * Metrics API Service
 */
export const metricsService = {
  /**
   * Get metrics for a specific model
   */
  async getMetrics(modelId, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.get(\/api/metrics?model_id=\\);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Get aggregated metrics across all models
   */
  async getAggregatedMetrics(loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.get('/api/metrics/aggregated');
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Get historical metrics data
   */
  async getHistoricalMetrics(modelId, startDate, endDate, loading) {
    if (loading) loading.value = true;
    try {
      const params = new URLSearchParams({
        model_id: modelId,
        start_date: startDate,
        end_date: endDate,
      });
      const response = await apiClient.get(\/api/metrics/historical?\\);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },
};

/**
 * Predictions API Service
 */
export const predictionsService = {
  /**
   * Get predictions for a specific model
   */
  async getPredictions(modelId, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.get(\/api/predictions?model_id=\\);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Create a new prediction
   */
  async createPrediction(predictionData, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.post('/api/predictions', predictionData);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Get specific prediction by ID
   */
  async getPredictionById(predictionId, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.get(\/api/predictions/\\);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Update prediction status
   */
  async updatePredictionStatus(predictionId, status, loading) {
    if (loading) loading.value = true;
    try {
      const response = await apiClient.put(\/api/predictions/\\, {
        status,
      });
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },

  /**
   * Get predictions for date range
   */
  async getPredictionsForDateRange(startDate, endDate, loading) {
    if (loading) loading.value = true;
    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });
      const response = await apiClient.get(\/api/predictions/date-range?\\);
      return response;
    } finally {
      if (loading) loading.value = false;
    }
  },
};

/**
 * Health Check Service
 */
export const healthService = {
  /**
   * Check if backend is healthy
   */
  async checkHealth() {
    try {
      const response = await apiClient.get('/api/health');
      return response;
    } catch (error) {
      return {
        success: false,
        message: 'Backend is not available',
      };
    }
  },
};

export default {
  modelsService,
  metricsService,
  predictionsService,
  healthService,
};

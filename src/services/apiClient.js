/**
 * API Client for Battery Dashboard Backend
 * 
 * This module provides a configured HTTP client for making requests to the backend API.
 * It includes base URL configuration, error handling, and request/response interceptors.
 */

class APIClient {
  constructor() {
    // Get base URL from environment variable or fallback to default
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
    this.timeout = 30000; // 30 seconds
  }

  /**
   * Build headers with Content-Type and any additional headers
   */
  buildHeaders(customHeaders = {}) {
    return {
      'Content-Type': 'application/json',
      ...customHeaders,
    };
  }

  /**
   * Handle API errors with consistent error structure
   */
  handleError(error, endpoint) {
    console.error(\API Error [\]:\, error);

    if (error instanceof Response) {
      return {
        success: false,
        status: error.status,
        message: \Request failed with status \\,
        data: null,
      };
    }

    if (error instanceof TypeError) {
      return {
        success: false,
        status: 0,
        message: 'Network error or CORS issue. Check if backend is running.',
        data: null,
      };
    }

    return {
      success: false,
      status: 500,
      message: error.message || 'An unexpected error occurred',
      data: null,
    };
  }

  /**
   * Fetch with timeout wrapper
   */
  fetchWithTimeout(url, options = {}) {
    return Promise.race([
      fetch(url, options),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), this.timeout)
      ),
    ]);
  }

  /**
   * GET request
   */
  async get(endpoint, options = {}) {
    try {
      const url = \\\\;
      const response = await this.fetchWithTimeout(url, {
        method: 'GET',
        headers: this.buildHeaders(options.headers),
        ...options,
      });

      if (!response.ok) {
        throw response;
      }

      const data = await response.json();
      return {
        success: true,
        status: response.status,
        message: 'Success',
        data,
      };
    } catch (error) {
      return this.handleError(error, \GET \\);
    }
  }

  /**
   * POST request
   */
  async post(endpoint, body, options = {}) {
    try {
      const url = \\\\;
      const response = await this.fetchWithTimeout(url, {
        method: 'POST',
        headers: this.buildHeaders(options.headers),
        body: JSON.stringify(body),
        ...options,
      });

      if (!response.ok) {
        throw response;
      }

      const data = await response.json();
      return {
        success: true,
        status: response.status,
        message: 'Success',
        data,
      };
    } catch (error) {
      return this.handleError(error, \POST \\);
    }
  }

  /**
   * PUT request
   */
  async put(endpoint, body, options = {}) {
    try {
      const url = \\\\;
      const response = await this.fetchWithTimeout(url, {
        method: 'PUT',
        headers: this.buildHeaders(options.headers),
        body: JSON.stringify(body),
        ...options,
      });

      if (!response.ok) {
        throw response;
      }

      const data = await response.json();
      return {
        success: true,
        status: response.status,
        message: 'Success',
        data,
      };
    } catch (error) {
      return this.handleError(error, \PUT \\);
    }
  }

  /**
   * DELETE request
   */
  async delete(endpoint, options = {}) {
    try {
      const url = \\\\;
      const response = await this.fetchWithTimeout(url, {
        method: 'DELETE',
        headers: this.buildHeaders(options.headers),
        ...options,
      });

      if (!response.ok) {
        throw response;
      }

      const data = await response.json();
      return {
        success: true,
        status: response.status,
        message: 'Success',
        data,
      };
    } catch (error) {
      return this.handleError(error, \DELETE \\);
    }
  }

  /**
   * Get the base URL (useful for debugging)
   */
  getBaseURL() {
    return this.baseURL;
  }
}

// Create and export singleton instance
const apiClient = new APIClient();
export default apiClient;

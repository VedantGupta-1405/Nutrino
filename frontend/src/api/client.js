import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Attach JWT Bearer token if present in localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('nutrino_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to format errors and handle session expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('nutrino_token');
      localStorage.removeItem('nutrino_user');
      window.dispatchEvent(new Event('nutrino_auth_expired'));
    }
    return Promise.reject(error);
  }
);

/**
 * Extracts a human-readable error message from an API error response.
 */
export function extractErrorMessage(error, defaultMessage = 'An unexpected error occurred') {
  if (!error) return defaultMessage;
  if (error.response?.data) {
    const data = error.response.data;
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      // Pydantic validation errors
      return data.detail.map((err) => `${err.loc?.slice(-1)[0] || 'field'}: ${err.msg}`).join(', ');
    }
    if (data.message) return data.message;
  }
  return error.message || defaultMessage;
}

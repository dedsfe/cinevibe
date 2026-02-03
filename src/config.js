// Base API URL - uses env var for production
// Para backend local: http://localhost:8080/api
// Para ngrok: https://SEU_NGROK.ngrok.io/api
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';

// Helper to check if backend is local
export const isLocalBackend = () => {
  return API_BASE_URL.includes('localhost') || API_BASE_URL.includes('127.0.0.1');
};

// Helper to get health check URL
export const getHealthUrl = () => {
  return API_BASE_URL.replace('/api', '') + '/api/health';
};

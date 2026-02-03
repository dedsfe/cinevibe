// API Configuration
// In development, uses localhost
// In production, uses environment variable or fallback

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';

// Other config
export const APP_NAME = 'Filfil';
export const APP_VERSION = '1.0.0';

/**
 * User-friendly error messages
 * Maps technical errors to readable messages
 */

export const ERROR_MESSAGES = {
  // Network errors
  NETWORK_ERROR: "Unable to connect. Please check your internet connection.",
  TIMEOUT: "Request timed out. Please try again.",
  SERVER_ERROR: "Server error. Please try again later.",
  
  // Geolocation errors
  LOCATION_DENIED: "Location permission denied. Please enable location access in your browser settings.",
  LOCATION_UNAVAILABLE: "Location information is unavailable. Please try again.",
  LOCATION_TIMEOUT: "Location request timed out. Please try again.",
  LOCATION_NOT_SUPPORTED: "Geolocation is not supported by your browser.",
  
  // API errors
  API_ERROR: "Something went wrong. Please try again.",
  INVALID_REQUEST: "Invalid request. Please check your input.",
  NOT_FOUND: "Resource not found.",
  UNAUTHORIZED: "You are not authorized to access this resource.",
  
  // Chat errors
  SEND_MESSAGE_FAILED: "Failed to send message. Please try again.",
  LOAD_SESSIONS_FAILED: "Failed to load chat history.",
  CREATE_SESSION_FAILED: "Failed to create new chat.",
  DELETE_SESSION_FAILED: "Failed to delete chat.",
  
  // Suggestions errors
  NO_SUGGESTIONS: "No places found matching your request. Try adjusting your search.",
  SUGGESTIONS_FAILED: "Failed to get recommendations. Please try again.",
  
  // Generic
  UNKNOWN_ERROR: "An unexpected error occurred. Please try again.",
} as const;

export type ErrorMessageKey = keyof typeof ERROR_MESSAGES;

/**
 * Get user-friendly error message from error object
 */
export const getErrorMessage = (error: any): string => {
  // Network errors
  if (error.message?.includes('Failed to fetch') || error.code === 'ERR_NETWORK') {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }
  
  if (error.message?.includes('timeout') || error.code === 'ECONNABORTED') {
    return ERROR_MESSAGES.TIMEOUT;
  }
  
  // HTTP status codes
  if (error.response?.status) {
    switch (error.response.status) {
      case 400:
        return ERROR_MESSAGES.INVALID_REQUEST;
      case 401:
      case 403:
        return ERROR_MESSAGES.UNAUTHORIZED;
      case 404:
        return ERROR_MESSAGES.NOT_FOUND;
      case 500:
      case 502:
      case 503:
        return ERROR_MESSAGES.SERVER_ERROR;
      default:
        return error.response.data?.detail || ERROR_MESSAGES.API_ERROR;
    }
  }
  
  // Geolocation errors
  if (error.code === 1) {
    return ERROR_MESSAGES.LOCATION_DENIED;
  }
  if (error.code === 2) {
    return ERROR_MESSAGES.LOCATION_UNAVAILABLE;
  }
  if (error.code === 3) {
    return ERROR_MESSAGES.LOCATION_TIMEOUT;
  }
  
  // Custom error messages
  if (error.message) {
    return error.message;
  }
  
  return ERROR_MESSAGES.UNKNOWN_ERROR;
};

/**
 * Check if error is retryable
 */
export const isRetryableError = (error: any): boolean => {
  // Network errors are retryable
  if (error.message?.includes('Failed to fetch') || error.code === 'ERR_NETWORK') {
    return true;
  }
  
  // Timeout errors are retryable
  if (error.message?.includes('timeout') || error.code === 'ECONNABORTED') {
    return true;
  }
  
  // Server errors (5xx) are retryable
  if (error.response?.status >= 500) {
    return true;
  }
  
  // 429 Too Many Requests is retryable
  if (error.response?.status === 429) {
    return true;
  }
  
  return false;
};

/**
 * Get retry delay based on attempt number (exponential backoff)
 */
export const getRetryDelay = (attemptNumber: number): number => {
  // Exponential backoff: 1s, 2s, 4s, 8s, 16s
  return Math.min(1000 * Math.pow(2, attemptNumber - 1), 16000);
};

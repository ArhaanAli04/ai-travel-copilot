/**
 * Hook for API calls with automatic retry logic
 * Implements exponential backoff
 */

import { useState, useCallback } from 'react';
import { getRetryDelay, isRetryableError } from '../utils/error-messages';

interface RetryOptions {
  maxRetries?: number;
  onRetry?: (attemptNumber: number) => void;
}

export const useApiWithRetry = () => {
  const [retrying, setRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const executeWithRetry = useCallback(
    async <T>(
      apiCall: () => Promise<T>,
      options: RetryOptions = {}
    ): Promise<T> => {
      const { maxRetries = 3, onRetry } = options;
      let lastError: any;

      for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
        try {
          setRetryCount(attempt - 1);
          
          // If not first attempt, we're retrying
          if (attempt > 1) {
            setRetrying(true);
            if (onRetry) {
              onRetry(attempt - 1);
            }
          }

          const result = await apiCall();
          
          // Success - reset state
          setRetrying(false);
          setRetryCount(0);
          
          return result;
        } catch (error) {
          lastError = error;
          console.error(`Attempt ${attempt} failed:`, error);

          // Check if we should retry
          const shouldRetry = attempt <= maxRetries && isRetryableError(error);

          if (!shouldRetry) {
            setRetrying(false);
            setRetryCount(0);
            throw error;
          }

          // Wait before retrying (exponential backoff)
          const delay = getRetryDelay(attempt);
          console.log(`⏳ Retrying in ${delay}ms... (attempt ${attempt}/${maxRetries})`);
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }

      // All retries exhausted
      setRetrying(false);
      setRetryCount(0);
      throw lastError;
    },
    []
  );

  return { executeWithRetry, retrying, retryCount };
};

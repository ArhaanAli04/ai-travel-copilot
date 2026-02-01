/**
 * Date and time utilities
 */

import { format, formatDistanceToNow } from 'date-fns';

/**
 * Get current time of day
 */
export const getTimeOfDay = (): string => {
  const hour = new Date().getHours();

  if (hour < 6) return 'late night';
  if (hour < 12) return 'morning';
  if (hour < 17) return 'afternoon';
  if (hour < 21) return 'evening';
  return 'night';
};

/**
 * Get greeting based on time of day
 */
export const getGreeting = (): string => {
  const timeOfDay = getTimeOfDay();

  switch (timeOfDay) {
    case 'morning':
      return 'Good morning';
    case 'afternoon':
      return 'Good afternoon';
    case 'evening':
      return 'Good evening';
    case 'night':
    case 'late night':
      return 'Good evening';
    default:
      return 'Hello';
  }
};

/**
 * Format time for display (e.g., "2:30 PM")
 */
export const formatTime = (date: Date): string => {
  return format(date, 'h:mm a');
};

/**
 * Format date for display (e.g., "Jan 31, 2026")
 */
export const formatDate = (date: Date): string => {
  return format(date, 'MMM d, yyyy');
};

/**
 * Format relative time (e.g., "2 minutes ago")
 */
export const formatRelativeTime = (date: Date): string => {
  return formatDistanceToNow(date, { addSuffix: true });
};

/**
 * Get current day of week
 */
export const getDayOfWeek = (): string => {
  return format(new Date(), 'EEEE');
};

/**
 * Check if a place is currently open
 */
export const isOpenNow = (hours?: string): boolean | null => {
  if (!hours) return null;

  // Parse hours string (format: "Mon-Fri 9:00-18:00")
  // This is simplified - you may need more robust parsing
  const now = new Date();
  const currentHour = now.getHours();
  const currentDay = format(now, 'EEE');

  // Simple check - can be enhanced
  if (hours.includes('24/7') || hours.includes('24 hours')) {
    return true;
  }

  // TODO: Add more sophisticated hours parsing
  return null;
};

/**
 * Get time constraint string based on current time
 */
export const getTimeConstraint = (): string => {
  const hour = new Date().getHours();

  if (hour >= 12 && hour < 14) return 'lunch time';
  if (hour >= 18 && hour < 21) return 'dinner time';
  if (hour >= 7 && hour < 11) return 'breakfast time';
  
  return '1-2 hours';
};

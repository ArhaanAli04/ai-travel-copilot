/**
 * Mock data for UI development and testing
 */

import { type Message, type POI,type ChatSession } from '../types/local-discovery';

export const MOCK_POIS: POI[] = [
  {
    poi_id: '1',
    name: 'Chaayos',
    category: 'cafe',
    distance_km: 0.5,
    distance_text: '500 m',
    location: {
      type: 'Point',
      coordinates: [72.8295, 19.0596],
    },
    address: 'Bandra West, Mumbai',
    phone: '+91 22 1234 5678',
    website: 'https://chaayos.com',
    hours: '8:00 AM - 11:00 PM',
    tags: {
      cuisine: 'cafe',
      amenity: 'cafe',
      outdoor_seating: 'yes',
      wifi: 'yes',
    },
    reason: 'Popular local cafe with great ambiance and tea selection',
    highlights: ['Free WiFi', 'Outdoor seating', 'Variety of teas'],
    best_for: 'Working remotely or casual meetups',
    relevance_score: 0.95,
    average_rating: 4.5,
    feedback_count: 127,
    positive_feedback_count: 98,
    negative_feedback_count: 12,
  },
  {
    poi_id: '2',
    name: 'The Bombay Canteen',
    category: 'restaurant',
    distance_km: 1.2,
    distance_text: '1.2 km',
    location: {
      type: 'Point',
      coordinates: [72.8311, 19.0645],
    },
    address: 'Lower Parel, Mumbai',
    phone: '+91 22 9876 5432',
    hours: '12:00 PM - 12:00 AM',
    tags: {
      cuisine: 'indian',
      amenity: 'restaurant',
      bar: 'yes',
    },
    reason: 'Trendy restaurant serving modern Indian cuisine',
    highlights: ['Innovative menu', 'Craft cocktails', 'Stylish ambiance'],
    best_for: 'Special occasions or date nights',
    relevance_score: 0.88,
    average_rating: 4.7,
    feedback_count: 234,
    positive_feedback_count: 201,
    negative_feedback_count: 15,
  },
  {
    poi_id: '3',
    name: 'Prithvi Cafe',
    category: 'cafe',
    distance_km: 0.8,
    distance_text: '800 m',
    location: {
      type: 'Point',
      coordinates: [72.8268, 19.0554],
    },
    address: 'Juhu, Mumbai',
    hours: '9:00 AM - 10:00 PM',
    tags: {
      cuisine: 'cafe',
      amenity: 'cafe',
      outdoor_seating: 'yes',
    },
    reason: 'Iconic cafe next to Prithvi Theatre with bohemian vibe',
    highlights: ['Theatre crowd', 'Book-friendly', 'Chai & snacks'],
    best_for: 'Reading or post-theatre discussions',
    relevance_score: 0.82,
    average_rating: 4.3,
    feedback_count: 89,
    positive_feedback_count: 65,
    negative_feedback_count: 8,
  },
];

export const MOCK_MESSAGES: Message[] = [
  {
    id: '1',
    role: 'assistant',
    content: `${getGreeting()}! 👋 I'm your local discovery assistant. I can help you find amazing places around Mumbai based on your preferences.

Try asking me things like:
• "Find me a cozy cafe for working"
• "Best restaurants for dinner tonight"
• "Where can I get authentic street food?"

What are you looking for today?`,
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
  },
];

export const MOCK_CHAT_SESSIONS: ChatSession[] = [
  {
    id: '1',
    title: 'Coffee shops in Bandra',
    messages: MOCK_MESSAGES,
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
    updated_at: new Date(Date.now() - 5 * 60 * 1000),
    city: 'mumbai',
    location: { lat: 19.0596, lon: 72.8295 },
  },
  {
    id: '2',
    title: 'Dinner recommendations',
    messages: [],
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000),
    updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000),
    city: 'mumbai',
    location: { lat: 19.0596, lon: 72.8295 },
  },
];

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

/**
 * Generate mock AI response for testing
 */
export const generateMockResponse = (query: string): Message => {
  const hasFood = /food|eat|restaurant|dinner|lunch/i.test(query);
  const hasCoffee = /coffee|cafe|work/i.test(query);

  let content = `Based on your search for "${query}", here are some great options nearby:`;
  let pois: POI[] = [];

  if (hasCoffee) {
    content = `I found some excellent cafes for you! Here are my top picks:`;
    pois = MOCK_POIS.filter((poi) => poi.category === 'cafe');
  } else if (hasFood) {
    content = `Here are some fantastic restaurants I recommend:`;
    pois = MOCK_POIS;
  } else {
    pois = MOCK_POIS.slice(0, 2);
  }

  return {
    id: Date.now().toString(),
    role: 'assistant',
    content,
    pois,
    timestamp: new Date(),
  };
};

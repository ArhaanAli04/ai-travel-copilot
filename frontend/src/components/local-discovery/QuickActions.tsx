/**
 * Quick Actions Component
 * Pre-defined quick action buttons for common queries
 */

import React from 'react';
import { Coffee, UtensilsCrossed, ShoppingBag, MapPin, Star, Clock } from 'lucide-react';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  query: string;
}

interface QuickActionsProps {
  onSelectAction: (query: string) => void;
  disabled?: boolean;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'coffee',
    label: 'Coffee Shop',
    icon: <Coffee className="w-4 h-4" />,
    query: 'Find me a cozy coffee shop for working',
  },
  {
    id: 'dinner',
    label: 'Dinner',
    icon: <UtensilsCrossed className="w-4 h-4" />,
    query: 'Best restaurants for dinner tonight',
  },
  {
    id: 'shopping',
    label: 'Shopping',
    icon: <ShoppingBag className="w-4 h-4" />,
    query: 'Where can I go shopping nearby',
  },
  {
    id: 'explore',
    label: 'Explore',
    icon: <MapPin className="w-4 h-4" />,
    query: 'Show me interesting places to explore',
  },
  {
    id: 'top_rated',
    label: 'Top Rated',
    icon: <Star className="w-4 h-4" />,
    query: 'Top rated places near me',
  },
  {
    id: 'quick_bite',
    label: 'Quick Bite',
    icon: <Clock className="w-4 h-4" />,
    query: 'Find me a quick bite nearby',
  },
];

export const QuickActions: React.FC<QuickActionsProps> = ({
  onSelectAction,
  disabled = false,
}) => {
  return (
    <div className="px-6 py-4 bg-white border-b border-gray-200">
      <h3 className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wide">
        Quick Actions
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.id}
            onClick={() => onSelectAction(action.query)}
            disabled={disabled}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100 border border-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {action.icon}
            <span>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

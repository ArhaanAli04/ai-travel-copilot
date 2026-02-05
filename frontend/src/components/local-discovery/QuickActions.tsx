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
    query: 'Find me a cozy cafe for working',
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
    <div className="px-6 py-4 border-b border-[rgba(148,163,184,0.2)]">
      <h3 className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF] mb-3">
        Quick Actions
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.id}
            onClick={() => onSelectAction(action.query)}
            disabled={disabled}
            className="flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-white bg-[#1F2937]/50 rounded-lg hover:bg-[#1F2937]/70 border border-[rgba(148,163,184,0.2)] transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:border-[#38BDF8]/30 group"
          >
            <span className="text-[#9CA3AF] group-hover:text-[#38BDF8] transition-colors">
              {action.icon}
            </span>
            <span className="text-[#E5E7EB] group-hover:text-white transition-colors">
              {action.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

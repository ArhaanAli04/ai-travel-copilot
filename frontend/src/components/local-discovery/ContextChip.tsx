/**
 * Context Chip Component
 * Displays contextual information (location, time, preferences)
 */

import React from 'react';
import { type ContextChip as ContextChipType } from '../../types/local-discovery';
import { 
  MapPin, 
  Clock, 
  Cloud, 
  Leaf, 
  DollarSign, 
  Users,
  X 
} from 'lucide-react';

interface ContextChipProps {
  chip: ContextChipType;
  onRemove?: (chipId: string) => void;
}

const getIcon = (type: string) => {
  switch (type) {
    case 'location':
      return MapPin;
    case 'time':
      return Clock;
    case 'weather':
      return Cloud;
    case 'dietary':
      return Leaf;
    case 'budget':
      return DollarSign;
    case 'preference':
      return Users;
    default:
      return MapPin;
  }
};

export const ContextChip: React.FC<ContextChipProps> = ({ chip, onRemove }) => {
  const Icon = getIcon(chip.type);

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
        chip.removable
          ? 'bg-blue-50 text-blue-700 border border-blue-200'
          : 'bg-gray-100 text-gray-700 border border-gray-200'
      }`}
    >
      <Icon className="w-4 h-4" />
      <span className="font-medium">{chip.label}:</span>
      <span>{chip.value}</span>

      {chip.removable && onRemove && (
        <button
          onClick={() => onRemove(chip.id)}
          className="ml-1 hover:bg-blue-100 rounded-full p-0.5 transition-colors"
          aria-label="Remove"
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};

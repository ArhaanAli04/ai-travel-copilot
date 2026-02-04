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
  X,
  Edit2 
} from 'lucide-react';

interface ContextChipProps {
  chip: ContextChipType;
  onRemove?: (chipId: string) => void;
  onEdit?: (chipId: string) => void;
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

export const ContextChip: React.FC<ContextChipProps> = ({ chip, onRemove, onEdit }) => {
  const Icon = getIcon(chip.type);
  
  // ✅ Check if this chip can be edited (location or time)
  const canEdit = (chip.type === 'location' || chip.type === 'time') && onEdit;

  // ✅ Different color scheme for editable chips
  const getChipStyles = () => {
    if (chip.removable) {
      return 'bg-blue-50 text-blue-700 border border-blue-200';
    }
    if (canEdit) {
      return 'bg-purple-50 text-purple-700 border border-purple-200'; // ✅ Purple for editable
    }
    return 'bg-gray-100 text-gray-700 border border-gray-200';
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${getChipStyles()}`}>
      {/* ✅ CHANGED: Use emoji icon if available, otherwise use Lucide icon */}
      {chip.icon ? (
        <span className="text-base">{chip.icon}</span>
      ) : (
        <Icon className="w-4 h-4" />
      )}
      
      <span className="font-medium">{chip.label}:</span>
      <span>{chip.value}</span>

      {/* ✅ Edit button for location and time chips */}
      {canEdit && (
        <button
          onClick={() => onEdit(chip.id)}
          className="ml-1 hover:bg-purple-100 rounded-full p-0.5 transition-colors"
          aria-label={`Edit ${chip.label}`}
        >
          <Edit2 className="w-3 h-3" />
        </button>
      )}

      {/* ✅ Remove button for removable chips (preferences) */}
      {chip.removable && onRemove && (
        <button
          onClick={() => onRemove(chip.id)}
          className="ml-1 hover:bg-blue-100 rounded-full p-0.5 transition-colors"
          aria-label={`Remove ${chip.label}`}
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};

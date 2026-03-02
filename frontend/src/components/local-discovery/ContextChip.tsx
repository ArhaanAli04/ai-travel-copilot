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
  
  // Check if this chip can be edited (location or time)
  const canEdit = (chip.type === 'location' || chip.type === 'time') && onEdit;

  // Different color scheme based on chip type
  const getChipStyles = () => {
    if (chip.type === 'location') {
      return 'bg-[#8B5CF6]/10 text-[#8B5CF6] border border-[#8B5CF6]/30';
    }
    if (chip.type === 'time') {
      return 'bg-[#8B5CF6]/10 text-[#8B5CF6] border border-[#8B5CF6]/30';
    }
    if (chip.removable) {
      return 'bg-[#38BDF8]/10 text-[#38BDF8] border border-[#38BDF8]/30';
    }
    return 'bg-white/5 text-[#9CA3AF] border border-[rgba(148,163,184,0.2)]';
  };

  const getHoverStyles = () => {
    if (chip.type === 'location') {
      return 'hover:bg-[#8B5CF6]/20';
    }
    if (chip.type === 'time') {
      return 'hover:bg-[#8B5CF6]/20';
    }
    if (chip.removable) {
      return 'hover:bg-[#38BDF8]/20';
    }
    return 'hover:bg-white/10';
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${getChipStyles()} transition-all`}>
      {/* Use emoji icon if available, otherwise use Lucide icon */}
      {chip.icon ? (
        <span className="text-base">{chip.icon}</span>
      ) : (
        <Icon className="w-4 h-4" />
      )}
      
      <span className="font-medium">{chip.label}:</span>
      <span className="font-normal">{chip.value}</span>

      {/* Edit button for location and time chips */}
      {canEdit && (
        <button
          onClick={() => onEdit(chip.id)}
          className={`ml-1 ${getHoverStyles()} cursor-pointer rounded-full p-0.5 transition-colors`}
          aria-label={`Edit ${chip.label}`}
        >
          <Edit2 className="w-3 h-3" />
        </button>
      )}

      {/* Remove button for removable chips (preferences) */}
      {chip.removable && onRemove && (
        <button
          onClick={() => onRemove(chip.id)}
          className={`ml-1 ${getHoverStyles()} rounded-full p-0.5 transition-colors`}
          aria-label={`Remove ${chip.label}`}
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};

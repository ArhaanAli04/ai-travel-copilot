/**
 * Context Display Component
 * Shows current context (location, time, preferences) as chips
 */

import React from 'react';
import { type ContextChip as ContextChipType } from '../../types/local-discovery';
import { ContextChip } from './ContextChip';
import { Info } from 'lucide-react';

interface ContextDisplayProps {
  chips: ContextChipType[];
  onRemoveChip?: (chipId: string) => void;
  showInfo?: boolean;
}

export const ContextDisplay: React.FC<ContextDisplayProps> = ({
  chips,
  onRemoveChip,
  showInfo = false,
}) => {
  if (chips.length === 0 && !showInfo) {
    return null;
  }

  const locationChips = chips.filter((chip) => chip.type === 'location' || chip.type === 'time');
  const preferenceChips = chips.filter((chip) => chip.type === 'preference');

  return (
    <div className="space-y-3">
      {/* Info Banner */}
      {showInfo && (
        <div className="flex items-start gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
          <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-blue-900">
            Your context helps me provide personalized recommendations. You can add preferences from the settings menu.
          </p>
        </div>
      )}

      {/* Location & Time Context */}
      {locationChips.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">
            Context
          </h4>
          <div className="flex flex-wrap gap-2">
            {locationChips.map((chip) => (
              <ContextChip key={chip.id} chip={chip} onRemove={onRemoveChip} />
            ))}
          </div>
        </div>
      )}

      {/* Preference Chips */}
      {preferenceChips.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">
            Your Preferences
          </h4>
          <div className="flex flex-wrap gap-2">
            {preferenceChips.map((chip) => (
              <ContextChip key={chip.id} chip={chip} onRemove={onRemoveChip} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

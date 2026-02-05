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
  onEditChip?: (chipId: string) => void;
  showInfo?: boolean;
}

export const ContextDisplay: React.FC<ContextDisplayProps> = ({
  chips,
  onRemoveChip,
  onEditChip,
  showInfo = false,
}) => {
  if (chips.length === 0) {
    return null;
  }

  const contextChips = chips.filter(chip => 
    chip.type === 'location' || chip.type === 'time'
  );
  const preferenceChips = chips.filter(chip => 
    chip.type !== 'location' && chip.type !== 'time'
  );

  return (
    <div className="space-y-4">
      {/* CONTEXT Section - Location & Time */}
      {contextChips.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF] mb-2">
            Context
          </h3>
          <div className="flex flex-wrap gap-2">
            {contextChips.map((chip) => (
              <ContextChip
                key={chip.id}
                chip={chip}
                onRemove={onRemoveChip}
                onEdit={onEditChip}
              />
            ))}
          </div>
        </div>
      )}

      {/* YOUR PREFERENCES Section - Everything else */}
      {preferenceChips.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
              Your Preferences
            </h3>
            {showInfo && (
              <div className="group relative">
                <Info className="w-4 h-4 text-[#6B7280] cursor-help hover:text-[#9CA3AF] transition-colors" />
                <div className="absolute left-0 top-6 w-64 bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white text-xs rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
                  These preferences help personalize your recommendations. You can add more by clicking the settings icon.
                </div>
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {preferenceChips.map((chip) => (
              <ContextChip
                key={chip.id}
                chip={chip}
                onRemove={onRemoveChip}
                onEdit={onEditChip}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

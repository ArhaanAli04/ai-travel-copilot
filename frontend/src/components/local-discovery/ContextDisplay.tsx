/**
 * Context Display Component
 * Shows current context (location, time, preferences) as chips - COLLAPSIBLE
 */

import React, { useState } from 'react';
import { type ContextChip as ContextChipType } from '../../types/local-discovery';
import { ContextChip } from './ContextChip';
import { Info, ChevronDown, ChevronUp, Settings } from 'lucide-react';

interface ContextDisplayProps {
  chips: ContextChipType[];
  onRemoveChip?: (chipId: string) => void;
  onEditChip?: (chipId: string) => void;
  onOpenPreferences?: () => void;
  showInfo?: boolean;
}

export const ContextDisplay: React.FC<ContextDisplayProps> = ({
  chips,
  onRemoveChip,
  onEditChip,
  onOpenPreferences,
  showInfo = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

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
    <div className="border-b border-[rgba(148,163,184,0.2)]">
      {/* Header - Changes based on expanded state */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        {/* Left side - only show when collapsed */}
        {!isExpanded ? (
          <div className="flex items-center gap-3">
            <div className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
              Context & Preferences
            </div>
            <div className="flex items-center gap-2">
              {contextChips.slice(0, 2).map((chip) => (
                <ContextChip
                  key={chip.id}
                  chip={chip}
                  onRemove={onRemoveChip}
                  onEdit={onEditChip}
                />
              ))}
              {preferenceChips.length > 0 && (
                <span className="text-xs text-[#6B7280] px-2 py-1 bg-white/5 rounded-full">
                  +{preferenceChips.length} preferences
                </span>
              )}
            </div>
          </div>
        ) : (
          <div /> // Empty div to maintain layout
        )}

        {/* Toggle Button - always visible */}
        <div className="flex items-center gap-2 text-[#9CA3AF]">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-6 pb-4 space-y-4 animate-fade-in">
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
              <div className="flex items-center justify-between mb-2">
                {/* Left side: Title + Info */}
                <div className="flex items-center gap-2">
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

                {/* Right side: Settings Icon */}
                {onOpenPreferences && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenPreferences();
                    }}
                    className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
                    aria-label="Open preferences"
                  >
                    <Settings className="w-4 h-4 text-[#9CA3AF] hover:text-white transition-colors" />
                  </button>
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
      )}
    </div>
  );
};

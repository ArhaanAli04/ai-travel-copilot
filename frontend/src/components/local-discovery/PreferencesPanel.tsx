/**
 * Preferences Panel Component
 * Side panel for managing user preferences and context
 */

import React, { useState } from 'react';
import { type UserPreferences } from '../../types/local-discovery';
import { X, Plus, Trash2, Users, DollarSign, Clock } from 'lucide-react';

interface PreferencesPanelProps {
  preferences: UserPreferences;
  onUpdatePreferences: (key: keyof UserPreferences, value: any) => void;
  onClose: () => void;
}

const CUISINES = [
  'Italian', 'Indian', 'Chinese', 'Mexican', 'Japanese', 'Thai', 
  'American', 'French', 'Mediterranean', 'Asian', 'Middle Eastern',
  'Korean', 'Vietnamese', 'Greek', 'Spanish'
];

const CATEGORIES = [
  'restaurant', 'cafe', 'bar', 'pub', 'bakery', 'fast_food',
  'food_court', 'ice_cream', 'biergarten'
];

export const PreferencesPanel: React.FC<PreferencesPanelProps> = ({
  preferences,
  onUpdatePreferences,
  onClose,
}) => {
  const [newDietary, setNewDietary] = useState('');

  // Handle adding dietary restriction
  const handleAddDietary = () => {
    if (newDietary.trim()) {
      const current = preferences.dietary || [];
      onUpdatePreferences('dietary', [...current, newDietary.trim()]);
      setNewDietary('');
    }
  };

  // Handle removing dietary restriction
  const handleRemoveDietary = (item: string) => {
    const current = preferences.dietary || [];
    onUpdatePreferences('dietary', current.filter((d) => d !== item));
  };

  // Toggle cuisine preference
  const toggleCuisine = (cuisine: string) => {
    const current = preferences.cuisines || [];
    if (current.includes(cuisine)) {
      onUpdatePreferences('cuisines', current.filter((c) => c !== cuisine));
    } else {
      onUpdatePreferences('cuisines', [...current, cuisine]);
    }
  };

  // Toggle category
  const toggleCategory = (category: string) => {
    const current = preferences.categories || [];
    if (current.includes(category)) {
      onUpdatePreferences('categories', current.filter((c) => c !== category));
    } else {
      onUpdatePreferences('categories', [...current, category]);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0a0e14]/95 backdrop-blur-xl">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[rgba(148,163,184,0.2)] flex items-center justify-between flex-shrink-0">
        <div>
          <h2 className="text-xl font-bold text-white">Preferences</h2>
          <p className="text-sm text-[#9CA3AF] mt-1">Customize your discovery experience</p>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-white/5 rounded-lg transition-colors cursor-pointer"
          aria-label="Close"
        >
          <X className="w-5 h-5 text-[#9CA3AF]" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-6 space-y-6">
        {/* Dietary Restrictions */}
        <div className="space-y-3">
          <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Dietary Restrictions
          </label>
          
          {/* List */}
          {preferences.dietary && preferences.dietary.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {preferences.dietary.map((item) => (
                <span
                  key={item}
                  className="inline-flex items-center gap-2 px-3 py-2 bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/30 rounded-lg text-sm"
                >
                  {item}
                  <button
                    onClick={() => handleRemoveDietary(item)}
                    className="hover:bg-[#EF4444]/20 rounded-full p-0.5 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Add New */}
          <div className="flex gap-2">
            <input
              type="text"
              value={newDietary}
              onChange={(e) => setNewDietary(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddDietary())}
              placeholder="e.g., Vegetarian, Vegan, Gluten-free"
              className="flex-1 bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] rounded-lg h-10 px-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all text-sm"
            />
            <button
              onClick={handleAddDietary}
              disabled={!newDietary.trim()}
              className="px-4 h-10 bg-[#38BDF8] text-white rounded-lg hover:bg-[#3B82F6] disabled:bg-[#6B7280] disabled:cursor-not-allowed transition-colors"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Cuisine Preferences */}
        <div className="space-y-3">
          <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Cuisine Preferences
          </label>
          <p className="text-xs text-[#6B7280]">
            Select cuisines you prefer
          </p>
          
          <div className="flex flex-wrap gap-2">
            {CUISINES.map((cuisine) => (
              <button
                key={cuisine}
                type="button"
                onClick={() => toggleCuisine(cuisine)}
                className={`px-4 py-2 text-sm rounded-full transition-all hover:scale-105 cursor-pointer ${
                  preferences.cuisines?.includes(cuisine)
                    ? 'bg-[#38BDF8] text-white border border-[#38BDF8]'
                    : 'border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:bg-white/5'
                }`}
              >
                {cuisine}
              </button>
            ))}
          </div>
        </div>

        {/* Place Categories */}
        <div className="space-y-3">
          <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Place Categories
          </label>
          <p className="text-xs text-[#6B7280]">
            Type of places you're looking for
          </p>
          
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => toggleCategory(category)}
                className={`px-4 py-2 text-sm rounded-full transition-all hover:scale-105 capitalize cursor-pointer ${
                  preferences.categories?.includes(category)
                    ? 'bg-[#F97316] text-white border border-[#F97316]'
                    : 'border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:bg-white/5'
                }`}
              >
                {category.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Budget */}
        <div className="space-y-2">
          <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Budget
          </label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280]" />
            <select
              value={preferences.budget || ''}
              onChange={(e) => onUpdatePreferences('budget', e.target.value || undefined)}
              className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white rounded-lg h-12 pl-11 pr-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all appearance-none cursor-pointer"
            >
              <option value="">Any Budget</option>
              <option value="budget">Budget ($)</option>
              <option value="moderate">Moderate ($$)</option>
              <option value="expensive">Expensive ($$$)</option>
              <option value="luxury">Luxury ($$$$)</option>
            </select>
          </div>
        </div>

        {/* Time Constraint */}
        <div className="space-y-2">
          <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Time Constraint
          </label>
          <div className="relative">
            <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280]" />
            <select
              value={preferences.time_constraint || ''}
              onChange={(e) => onUpdatePreferences('time_constraint', e.target.value || undefined)}
              className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white rounded-lg h-12 pl-11 pr-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all appearance-none cursor-pointer"
            >
              <option value="">No Constraint</option>
              <option value="quick">Quick (15-30 min)</option>
              <option value="moderate">Moderate (30-60 min)</option>
              <option value="leisurely">Leisurely (1-2 hours)</option>
              <option value="extended">Extended (2+ hours)</option>
            </select>
          </div>
        </div>

        {/* Group Size */}
        <div className="space-y-2">
          <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Group Size
          </label>
          <div className="relative">
            <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280]" />
            <input
              type="number"
              min="1"
              max="20"
              value={preferences.group_size || ''}
              onChange={(e) => {
                const value = parseInt(e.target.value);
                onUpdatePreferences('group_size', value || undefined);
              }}
              placeholder="Number of people"
              className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] rounded-lg h-12 pl-11 pr-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all"
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-[rgba(148,163,184,0.2)] flex-shrink-0">
        <button
          onClick={onClose}
          className="w-full h-12 text-base font-semibold rounded-xl bg-gradient-to-r from-[#F97316] to-[#38BDF8] hover:from-[#EA580C] hover:to-[#3B82F6] transition-all text-white shadow-lg"
        >
          Save Preferences
        </button>
      </div>
    </div>
  );
};

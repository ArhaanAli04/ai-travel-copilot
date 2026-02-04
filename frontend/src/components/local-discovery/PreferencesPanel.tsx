/**
 * Preferences Panel Component
 * Side panel for managing user preferences and context
 */

import React, { useState } from 'react';
import {type UserPreferences } from '../../types/local-discovery';
import { X, Plus, Trash2 } from 'lucide-react';

interface PreferencesPanelProps {
  preferences: UserPreferences;
  onUpdatePreferences: (key: keyof UserPreferences, value: any) => void;
  onClose: () => void;
}

export const PreferencesPanel: React.FC<PreferencesPanelProps> = ({
  preferences,
  onUpdatePreferences,
  onClose,
}) => {
  const [newDietary, setNewDietary] = useState('');
  const [newCuisine, setNewCuisine] = useState('');
  const [newCategory, setNewCategory] = useState('');

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

  // Handle adding cuisine preference
  const handleAddCuisine = () => {
    if (newCuisine.trim()) {
      const current = preferences.cuisines || [];
      // Trim and capitalize first letter
      const formatted = newCuisine.trim().toLowerCase();
      const capitalized = formatted.charAt(0).toUpperCase() + formatted.slice(1);
      onUpdatePreferences('cuisines', [...current, capitalized]);
      setNewCuisine('');
    }
  };

  // Handle removing cuisine preference
  const handleRemoveCuisine = (item: string) => {
    const current = preferences.cuisines || [];
    onUpdatePreferences('cuisines', current.filter((c) => c !== item));
  };

  // Handle adding category
  const handleAddCategory = () => {
    if (newCategory.trim()) {
      const current = preferences.categories || [];
      // Convert to lowercase for consistency
      const formatted = newCategory.trim().toLowerCase();
      onUpdatePreferences('categories', [...current, formatted]);
      setNewCategory('');
    }
  };

  // Handle removing category
  const handleRemoveCategory = (item: string) => {
    const current = preferences.categories || [];
    onUpdatePreferences('categories', current.filter((c) => c !== item));
  };

  return (
    <div className="h-full flex flex-col bg-white">
      
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Preferences</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {/* Dietary Restrictions */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Dietary Restrictions
            </h3>
            
            {/* List */}
            {preferences.dietary && preferences.dietary.length > 0 && (
              <div className="space-y-2 mb-3">
                {preferences.dietary.map((item) => (
                  <div
                    key={item}
                    className="flex items-center justify-between px-3 py-2 bg-red-50 border border-red-200 rounded-lg"
                  >
                    <span className="text-sm text-red-900">{item}</span>
                    <button
                      onClick={() => handleRemoveDietary(item)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add New */}
            <div className="flex gap-2">
              <input
                type="text"
                value={newDietary}
                onChange={(e) => setNewDietary(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddDietary()}
                placeholder="e.g., Vegetarian, Vegan, Gluten-free"
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleAddDietary}
                disabled={!newDietary.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Cuisine Preferences */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Cuisine Preferences
            </h3>
            <p className="text-xs text-gray-500 mb-2">
              Select cuisines you prefer (e.g., Italian, Indian, Chinese)
            </p>
            
            {/* List of Selected Cuisines */}
            {preferences.cuisines && preferences.cuisines.length > 0 && (
              <div className="space-y-2 mb-3">
                {preferences.cuisines.map((item) => (
                  <div
                    key={item}
                    className="flex items-center justify-between px-3 py-2 bg-green-50 border border-green-200 rounded-lg"
                  >
                    <span className="text-sm text-green-900">{item}</span>
                    <button
                      onClick={() => handleRemoveCuisine(item)}
                      className="text-green-600 hover:text-green-800"
                      aria-label={`Remove ${item}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Dropdown Selector */}
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) {
                  const current = preferences.cuisines || [];
                  if (!current.includes(e.target.value)) {
                    onUpdatePreferences('cuisines', [...current, e.target.value]);
                  }
                }
              }}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">Select a cuisine...</option>
              <option value="Italian">Italian</option>
              <option value="Indian">Indian</option>
              <option value="Chinese">Chinese</option>
              <option value="Mexican">Mexican</option>
              <option value="Japanese">Japanese</option>
              <option value="Thai">Thai</option>
              <option value="American">American</option>
              <option value="French">French</option>
              <option value="Mediterranean">Mediterranean</option>
              <option value="Asian">Asian</option>
              <option value="Middle Eastern">Middle Eastern</option>
              <option value="Korean">Korean</option>
              <option value="Vietnamese">Vietnamese</option>
              <option value="Greek">Greek</option>
              <option value="Spanish">Spanish</option>
            </select>
          </div>

          {/* Place Categories */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Place Categories
            </h3>
            <p className="text-xs text-gray-500 mb-2">
              Type of place you're looking for
            </p>
            
            {/* List */}
            {preferences.categories && preferences.categories.length > 0 && (
              <div className="space-y-2 mb-3">
                {preferences.categories.map((item) => (
                  <div
                    key={item}
                    className="flex items-center justify-between px-3 py-2 bg-purple-50 border border-purple-200 rounded-lg"
                  >
                    <span className="text-sm text-purple-900 capitalize">{item}</span>
                    <button
                      onClick={() => handleRemoveCategory(item)}
                      className="text-purple-600 hover:text-purple-800"
                      aria-label={`Remove ${item}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Dropdown Selector */}
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) {
                  const current = preferences.categories || [];
                  if (!current.includes(e.target.value)) {
                    onUpdatePreferences('categories', [...current, e.target.value]);
                  }
                }
              }}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">Select a category...</option>
              <option value="restaurant">Restaurant</option>
              <option value="cafe">Cafe</option>
              <option value="bar">Bar</option>
              <option value="pub">Pub</option>
              <option value="bakery">Bakery</option>
              <option value="fast_food">Fast Food</option>
              <option value="food_court">Food Court</option>
              <option value="ice_cream">Ice Cream</option>
              <option value="biergarten">Beer Garden</option>
            </select>
          </div>

          {/* Budget */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Budget</h3>
            <select
              value={preferences.budget || ''}
              onChange={(e) => onUpdatePreferences('budget', e.target.value || undefined)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Any Budget</option>
              <option value="budget">Budget ($)</option>
              <option value="moderate">Moderate ($$)</option>
              <option value="expensive">Expensive ($$$)</option>
              <option value="luxury">Luxury ($$$$)</option>
            </select>
          </div>

          {/* Time Constraint */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Time Constraint
            </h3>
            <select
              value={preferences.time_constraint || ''}
              onChange={(e) => onUpdatePreferences('time_constraint', e.target.value || undefined)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">No Constraint</option>
              <option value="quick">Quick (15-30 min)</option>
              <option value="moderate">Moderate (30-60 min)</option>
              <option value="leisurely">Leisurely (1-2 hours)</option>
              <option value="extended">Extended (2+ hours)</option>
            </select>
          </div>

          {/* Group Size */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Group Size
            </h3>
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
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Done
          </button>
        </div>
      </div>
    
  );
};

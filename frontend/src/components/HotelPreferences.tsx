import { type TripCreate } from '../services/api';

interface HotelPreferencesProps {
  formData: TripCreate;
  setFormData: React.Dispatch<React.SetStateAction<TripCreate>>;
}

const HotelPreferences = ({ formData, setFormData }: HotelPreferencesProps) => {
  if (!formData.include_hotels) return null;

  return (
    <div className="p-6 bg-[#1F2937]/30 border border-[rgba(148,163,184,0.2)] rounded-2xl space-y-4">
      <h3 className="text-white font-semibold mb-2">🏨 Hotel Preferences</h3>

      <div className="grid gap-4">
        {/* Sort By */}
        <div>
          <label className="block mb-2 text-sm font-semibold text-[#E5E7EB]">
            Sort Results By
          </label>
          <select
            value={formData.hotel_preferences?.sort_by || 'relevance'}
            onChange={(e) =>
              setFormData(prev => ({
                ...prev,
                hotel_preferences: {
                  ...prev.hotel_preferences,
                  sort_by: e.target.value,
                },
              }))
            }
            className="w-full h-10 rounded-lg bg-[#111827] border border-[rgba(148,163,184,0.3)] text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#F59E0B]"
          >
            <option value="relevance">Relevance</option>
            <option value="lowest_price">Lowest Price</option>
            <option value="highest_rating">Highest Rating</option>
            <option value="most_reviewed">Most Reviewed</option>
          </select>
        </div>

        {/* Max Price */}
        <div>
          <label className="block mb-2 text-sm font-semibold text-[#E5E7EB]">
            Max Price Per Night (USD, Optional)
          </label>
          <input
            type="number"
            min="0"
            value={formData.hotel_preferences?.max_price || ''}
            onChange={(e) =>
              setFormData(prev => ({
                ...prev,
                hotel_preferences: {
                  ...prev.hotel_preferences,
                  max_price: e.target.value ? parseFloat(e.target.value) : undefined,
                },
              }))
            }
            placeholder="e.g., 200"
            className="w-full h-10 rounded-lg bg-[#111827] border border-[rgba(148,163,184,0.3)] text-white placeholder:text-[#6B7280] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#F59E0B]"
          />
        </div>

        {/* Min Rating */}
        <div>
          <label className="block mb-2 text-sm font-semibold text-[#E5E7EB]">
            Minimum Rating (Optional)
          </label>
          <select
            value={formData.hotel_preferences?.min_rating || ''}
            onChange={(e) =>
              setFormData(prev => ({
                ...prev,
                hotel_preferences: {
                  ...prev.hotel_preferences,
                  min_rating: e.target.value ? parseFloat(e.target.value) : undefined,
                },
              }))
            }
            className="w-full h-10 rounded-lg bg-[#111827] border border-[rgba(148,163,184,0.3)] text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#F59E0B]"
          >
            <option value="">Any rating</option>
            <option value="3">3+ stars</option>
            <option value="3.5">3.5+ stars</option>
            <option value="4">4+ stars</option>
            <option value="4.5">4.5+ stars</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default HotelPreferences;

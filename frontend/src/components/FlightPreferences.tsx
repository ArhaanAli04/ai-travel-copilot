import { type TripCreate } from '../services/api';

interface FlightPreferencesProps {
  formData: TripCreate;
  setFormData: React.Dispatch<React.SetStateAction<TripCreate>>;
}

const FlightPreferences = ({ formData, setFormData }: FlightPreferencesProps) => {
  if (!formData.include_flights) return null;

  return (
    <div className="p-6 bg-[#1F2937]/30 border border-[rgba(148,163,184,0.2)] rounded-2xl space-y-4">
      <h3 className="text-white font-semibold mb-2">✈️ Flight Preferences</h3>

      <div className="grid gap-4">
        {/* Trip Type */}
        <div>
          <label className="block mb-2 text-sm font-semibold text-[#E5E7EB]">
            Trip Type
          </label>
          <select
            value={formData.flight_preferences?.trip_type || 'one_way'}
            onChange={(e) =>
              setFormData(prev => ({
                ...prev,
                flight_preferences: {
                  ...prev.flight_preferences,
                  trip_type: e.target.value,
                },
              }))
            }
            className="w-full h-10 rounded-lg bg-[#111827] border border-[rgba(148,163,184,0.3)] text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#38BDF8]"
          >
            <option value="one_way">One-way</option>
            <option value="round_trip">Round Trip</option>
          </select>
        </div>

        {/* Cabin Class */}
        <div>
          <label className="block mb-2 text-sm font-semibold text-[#E5E7EB]">
            Cabin Class
          </label>
          <select
            value={formData.flight_preferences?.cabin_class || 'economy'}
            onChange={(e) =>
              setFormData(prev => ({
                ...prev,
                flight_preferences: {
                  ...prev.flight_preferences,
                  cabin_class: e.target.value,
                },
              }))
            }
            className="w-full h-10 rounded-lg bg-[#111827] border border-[rgba(148,163,184,0.3)] text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#38BDF8]"
          >
            <option value="economy">Economy</option>
            <option value="premium_economy">Premium Economy</option>
            <option value="business">Business</option>
            <option value="first">First Class</option>
          </select>
        </div>

        {/* Max Stops */}
        <div>
          <label className="block mb-2 text-sm font-semibold text-[#E5E7EB]">
            Maximum Stops
          </label>
          <select
            value={formData.flight_preferences?.max_stops ?? 'any'}
            onChange={(e) =>
              setFormData(prev => ({
                ...prev,
                flight_preferences: {
                  ...prev.flight_preferences,
                  max_stops: e.target.value === 'any' ? undefined : parseInt(e.target.value),
                },
              }))
            }
            className="w-full h-10 rounded-lg bg-[#111827] border border-[rgba(148,163,184,0.3)] text-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#38BDF8]"
          >
            <option value="any">Any number of stops</option>
            <option value="0">Nonstop only</option>
            <option value="1">1 stop max</option>
            <option value="2">2 stops max</option>
          </select>
        </div>

        {/* Preferred Airlines */}
        <div>
          <label className="block mb-2 text-sm font-semibold text-[#E5E7EB]">
            Preferred Airlines (Optional)
          </label>
          <input
            type="text"
            value={formData.flight_preferences?.preferred_airlines || ''}
            onChange={(e) =>
              setFormData(prev => ({
                ...prev,
                flight_preferences: {
                  ...prev.flight_preferences,
                  preferred_airlines: e.target.value,
                },
              }))
            }
            placeholder="e.g., Air India, IndiGo"
            className="w-full h-10 rounded-lg bg-[#111827] border border-[rgba(148,163,184,0.3)] text-white placeholder:text-[#6B7280] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#38BDF8]"
          />
        </div>
      </div>
    </div>
  );
};

export default FlightPreferences;

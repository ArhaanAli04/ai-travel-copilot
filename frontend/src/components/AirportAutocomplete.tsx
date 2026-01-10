import { useState, useEffect, useRef } from 'react';
import { airportApi, type AirportSuggestion } from '../services/api';

interface AirportAutocompleteProps {
  value: string;
  onChange: (value: string, code: string) => void;
  placeholder?: string;
  required?: boolean;
  className?: string;
}

const AirportAutocomplete = ({ value, onChange, placeholder, required,className }: AirportAutocompleteProps) => {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<AirportSuggestion[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedCode, setSelectedCode] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 2) {
        setLoading(true);
        try {
          const results = await airportApi.searchAirports(query);
          setSuggestions(results);
          setShowDropdown(true);
        } catch (error) {
          console.error('Failed to search airports:', error);
        } finally {
          setLoading(false);
        }
      } else {
        setSuggestions([]);
        setShowDropdown(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [query]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (airport: AirportSuggestion) => {
    setQuery(airport.display);
    setSelectedCode(airport.code);
    onChange(airport.display, airport.code);
    setShowDropdown(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setQuery(newValue);
    setSelectedCode('');
    onChange(newValue, '');
  };

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      <input
        type="text"
        value={query}
        onChange={handleInputChange}
        placeholder={placeholder}
        required={required}
        className={`w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] rounded-lg h-12 px-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all ${className || ''}`}
        
      />
      
      {loading && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] text-sm">
          🔍
        </div>
      )}

      {selectedCode && !loading && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[#22C55E] text-xs font-semibold">
          ✓ {selectedCode}
        </div>
      )}

      {showDropdown && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 max-h-72 overflow-y-auto bg-[#020617] border border-[rgba(148,163,184,0.3)] rounded-xl shadow-xl z-50">
          {suggestions.map((airport) => (
            <button
              type="button"
              key={airport.code}
              onClick={() => handleSelect(airport)}
              className="w-full text-left px-4 py-2.5 hover:bg-white/5 transition-colors border-b border-white/5 last:border-b-0"
            >
              <div className="font-semibold text-white">
                {airport.name} ({airport.code})
              </div>
              <div className="text-xs text-[#9CA3AF]">
                {airport.city}, {airport.country}
              </div>
            </button>
          ))}
        </div>
      )}


      {showDropdown && suggestions.length === 0 && !loading && query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-[#020617] border border-[rgba(148,163,184,0.3)] rounded-xl px-4 py-3 text-center text-sm text-[#9CA3AF] z-50">
          No airports found
        </div>
      )}
    </div>
  );
};

export default AirportAutocomplete;

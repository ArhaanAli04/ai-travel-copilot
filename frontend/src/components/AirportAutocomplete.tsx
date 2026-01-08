import { useState, useEffect, useRef } from 'react';
import { airportApi, type AirportSuggestion } from '../services/api';

interface AirportAutocompleteProps {
  value: string;
  onChange: (value: string, code: string) => void;
  placeholder?: string;
  required?: boolean;
}

const AirportAutocomplete = ({ value, onChange, placeholder, required }: AirportAutocompleteProps) => {
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
        style={{
          width: '100%',
          padding: '0.75rem',
          fontSize: '1rem',
          border: '1px solid #ddd',
          borderRadius: '8px',
          background: selectedCode ? '#e8f5e9' : 'white'
        }}
      />
      
      {loading && (
        <div style={{
          position: 'absolute',
          right: '1rem',
          top: '50%',
          transform: 'translateY(-50%)',
          color: '#666'
        }}>
          🔍
        </div>
      )}

      {selectedCode && (
        <div style={{
          position: 'absolute',
          right: '1rem',
          top: '50%',
          transform: 'translateY(-50%)',
          color: '#4CAF50',
          fontWeight: 'bold'
        }}>
          ✓ {selectedCode}
        </div>
      )}

      {showDropdown && suggestions.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          maxHeight: '300px',
          overflowY: 'auto',
          background: 'white',
          border: '1px solid #ddd',
          borderRadius: '8px',
          marginTop: '0.25rem',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000
        }}>
          {suggestions.map((airport) => (
            <div
              key={airport.code}
              onClick={() => handleSelect(airport)}
              style={{
                padding: '0.75rem 1rem',
                cursor: 'pointer',
                borderBottom: '1px solid #f0f0f0',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f5'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                {airport.name} ({airport.code})
              </div>
              <div style={{ fontSize: '0.85rem', color: '#666' }}>
                {airport.city}, {airport.country}
              </div>
            </div>
          ))}
        </div>
      )}

      {showDropdown && suggestions.length === 0 && !loading && query.length >= 2 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #ddd',
          borderRadius: '8px',
          marginTop: '0.25rem',
          padding: '1rem',
          textAlign: 'center',
          color: '#666'
        }}>
          No airports found
        </div>
      )}
    </div>
  );
};

export default AirportAutocomplete;

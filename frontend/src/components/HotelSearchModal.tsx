import React, { useState } from 'react';
import { X, Hotel, Calendar, Users, Star, DollarSign } from 'lucide-react';
import { type Trip, type HotelSearchParams, hotelApi } from '../services/api';

interface HotelSearchModalProps {
  trip: Trip;
  isOpen: boolean;
  onClose: () => void;
  onSearchComplete: (hotels: any[]) => void;
}

const HotelSearchModal: React.FC<HotelSearchModalProps> = ({
  trip,
  isOpen,
  onClose,
  onSearchComplete,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [city, setCity] = useState(trip.destinations[0] || '');
  const [checkIn, setCheckIn] = useState(trip.start_date.split('T')[0]);
  const [checkOut, setCheckOut] = useState(trip.end_date.split('T')[0]);
  const [adults, setAdults] = useState(trip.traveler_count || 2);
  const [sortBy, setSortBy] = useState<string>(
    trip.hotel_preferences?.sort_by || 'highest_rating'
  );
  const [maxPrice, setMaxPrice] = useState<string>(
    trip.hotel_preferences?.max_price?.toString() || ''
  );
  const [minRating, setMinRating] = useState<string>(
    trip.hotel_preferences?.min_rating?.toString() || ''
  );

  const handleSearch = async () => {
    if (!city || !checkIn || !checkOut) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params: HotelSearchParams = {
        city,
        check_in_date: checkIn,
        check_out_date: checkOut,
        adults,
        sort_by: sortBy as any,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
        min_rating: minRating ? parseFloat(minRating) : undefined,
      };

      const hotels = await hotelApi.searchHotels(trip.id, params);
      onSearchComplete(hotels);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to search hotels');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass-card rounded-3xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto border border-[#F59E0B]/30 animate-fade-in">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-[rgba(148,163,184,0.2)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/30">
              <Hotel className="w-6 h-6 text-[#F59E0B]" />
            </div>
            <h2 className="text-2xl font-bold text-white">Search Hotels</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {error && (
            <div className="glass-card rounded-2xl p-4 border-[#EF4444]/30 bg-[#EF4444]/10">
              <p className="text-[#FCA5A5] text-sm">{error}</p>
            </div>
          )}

          {/* City */}
          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
              Destination City
            </label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g., Paris"
              className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-[#F59E0B] transition-all"
            />
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Check-in
              </label>
              <input
                type="date"
                value={checkIn}
                onChange={(e) => setCheckIn(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#F59E0B] transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Check-out
              </label>
              <input
                type="date"
                value={checkOut}
                onChange={(e) => setCheckOut(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#F59E0B] transition-all"
              />
            </div>
          </div>

          {/* Adults & Sort */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                <Users className="w-4 h-4 inline mr-1" />
                Adults
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={adults}
                onChange={(e) => setAdults(parseInt(e.target.value))}
                className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#F59E0B] transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#F59E0B] transition-all"
              >
                <option value="relevance" className="bg-[#1F2937]">Relevance</option>
                <option value="lowest_price" className="bg-[#1F2937]">Lowest Price</option>
                <option value="highest_rating" className="bg-[#1F2937]">Highest Rating</option>
                <option value="most_reviewed" className="bg-[#1F2937]">Most Reviewed</option>
              </select>
            </div>
          </div>

          {/* Filters */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Max Price/Night (USD)
              </label>
              <input
                type="number"
                min="0"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="No limit"
                className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-[#F59E0B] transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                <Star className="w-4 h-4 inline mr-1" />
                Min Rating
              </label>
              <select
                value={minRating}
                onChange={(e) => setMinRating(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#F59E0B] transition-all"
              >
                <option value="" className="bg-[#1F2937]">Any rating</option>
                <option value="3" className="bg-[#1F2937]">3+</option>
                <option value="3.5" className="bg-[#1F2937]">3.5+</option>
                <option value="4" className="bg-[#1F2937]">4+</option>
                <option value="4.5" className="bg-[#1F2937]">4.5+</option>
              </select>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-[rgba(148,163,184,0.2)]">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-6 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleSearch}
            disabled={loading || !city || !checkIn || !checkOut}
            className="px-6 py-3 bg-gradient-to-r from-[#F59E0B] to-[#D97706] text-white rounded-xl font-bold hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 transition-all flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Hotel className="w-5 h-5" />
                Search Hotels
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default HotelSearchModal;

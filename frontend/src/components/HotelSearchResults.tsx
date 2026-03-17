import { Hotel, Star, MapPin, X,Images } from 'lucide-react';
import { type Hotel as HotelType } from '../services/api';
import { useState } from 'react';
import HotelPhotoModal from './HotelPhotoModal';
import { formatCurrency } from '../utils/currency';
interface HotelSearchResultsProps {
  hotels: HotelType[];
  onSelectHotel: (hotel: HotelType) => void;
  loading: boolean;
  onClose: () => void;
}

const AMENITY_ICONS: Record<string, string> = {
  'free wi-fi': '📶',
  'breakfast ($)': '🍳',
  'free breakfast': '🍳',
  'pool': '🏊',
  'indoor pool': '🏊',
  'spa': '💆',
  'fitness center': '🏋️',
  'parking ($)': '🅿️',
  'free parking': '🅿️',
  'restaurant': '🍽️',
  'bar': '🍷',
  'pet-friendly': '🐾',
  'airport shuttle': '🚌',
  'room service': '🛎️',
  'air conditioning': '❄️',
  'kid-friendly': '👶',
};

const getAmenityIcon = (amenity: string) => {
  const lower = amenity.toLowerCase();
  for (const [key, icon] of Object.entries(AMENITY_ICONS)) {
    if (lower.includes(key)) return icon;
  }
  return '✓';
};

const HotelSearchResults = ({
  hotels,
  onSelectHotel,
  loading,
  onClose,
}: HotelSearchResultsProps) => {
  const [photoModal, setPhotoModal] = useState<{ hotelName: string; images: string[] } | null>(null);

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-1">
        <Star className="w-4 h-4 text-[#F59E0B] fill-[#F59E0B]" />
        <span className="text-white font-semibold">{rating.toFixed(1)}</span>
      </div>
    );
  };

  const renderHotelCard = (hotel: HotelType, index: number) => (
  <div
    key={`hotel-${index}`}
    className="glass-card rounded-3xl p-6 border-[rgba(148,163,184,0.2)] hover:bg-[#1F2937]/70 transition-all animate-fade-in"
    style={{ animationDelay: `${index * 0.05}s` }}
  >
    {/* Header: Name + Rating */}
    <div className="flex justify-between items-start mb-3">
      <div className="flex-1 pr-4">
        <h4 className="text-xl font-bold text-white mb-1">{hotel.name}</h4>
        <div className="flex items-center gap-2 text-[#9CA3AF] text-sm">
          <MapPin className="w-4 h-4" />
          <span>{hotel.city}</span>
          {hotel.property_type && (
            <>
              <span>·</span>
              <span className="capitalize">{hotel.property_type}</span>
            </>
          )}
        </div>
      </div>
      <div className="text-right shrink-0">
        {hotel.rating && renderStars(hotel.rating)}
        {hotel.reviews_count && (
          <p className="text-xs text-[#9CA3AF] mt-1">
            {hotel.reviews_count.toLocaleString()} reviews
          </p>
        )}
      </div>
    </div>

    {/* Check-in / Nights / Check-out */}
    <div className="grid grid-cols-3 gap-3 mb-4">
      <div className="p-3 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.1)] text-center">
        <p className="text-xs text-[#9CA3AF] mb-1">Check-in</p>
        <p className="text-white font-semibold text-sm">{hotel.check_in_date}</p>
      </div>
      <div className="p-3 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.1)] text-center">
        <p className="text-xs text-[#9CA3AF] mb-1">Nights</p>
        <p className="text-white font-semibold text-sm">{hotel.nights}</p>
      </div>
      <div className="p-3 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.1)] text-center">
        <p className="text-xs text-[#9CA3AF] mb-1">Check-out</p>
        <p className="text-white font-semibold text-sm">{hotel.check_out_date}</p>
      </div>
    </div>

    {/* Amenities */}
    {hotel.amenities && hotel.amenities.length > 0 && (
      <div className="flex flex-wrap gap-2 mb-4">
        {hotel.amenities.slice(0, 6).map((amenity) => (
          <span
            key={amenity}
            className="px-2 py-1 rounded-lg bg-[#1F2937]/50 text-[#9CA3AF] text-xs border border-[rgba(148,163,184,0.15)] flex items-center gap-1"
          >
            <span>{getAmenityIcon(amenity)}</span>
            <span className="capitalize">{amenity}</span>
          </span>
        ))}
        {hotel.amenities.length > 6 && (
          <span className="px-2 py-1 rounded-lg bg-[#1F2937]/50 text-[#6B7280] text-xs border border-[rgba(148,163,184,0.15)]">
            +{hotel.amenities.length - 6} more
          </span>
        )}
      </div>
    )}

    {/* Price + Photos + Select button */}
    <div className="flex items-center justify-between pt-3 border-t border-[rgba(148,163,184,0.2)]">
    <div>
        <p className="text-xs text-[#9CA3AF]">Total Cost</p>
        <p className="text-2xl font-bold text-[#22C55E]">
        {formatCurrency(hotel.total_price, hotel.price_currency)}{' '}
        <span className="text-sm font-normal text-[#9CA3AF]">
            ({formatCurrency(hotel.price_per_night, hotel.price_currency)}/night)
        </span>
        </p>
    </div>
    <div className="flex items-center gap-2">
        {hotel.images && hotel.images.length > 0 && (
        <button
            onClick={() => setPhotoModal({ hotelName: hotel.name, images: hotel.images! })}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] transition-all text-sm font-medium cursor-pointer"
        >
            <Images className="w-4 h-4" />
            Photos ({hotel.images.length})
        </button>
        )}
        <button
        onClick={() => onSelectHotel(hotel)}
        disabled={loading}
        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all ${
            loading
            ? 'bg-[#1F2937] text-white/50 border border-[#6B7280]/30 cursor-not-allowed'
            : 'bg-transparent text-[#F59E0B] border border-[#F59E0B] hover:bg-[#F59E0B] hover:text-black hover:shadow-lg hover:shadow-[#F59E0B]/30 active:scale-95 cursor-pointer'
        }`}
        >
        {loading ? (
            <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Saving...
            </>
        ) : (
            <>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Select This Hotel
            </>
        )}
        </button>
    </div>
</div>
  </div>
);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="glass-card rounded-3xl p-6 border-[rgba(148,163,184,0.2)] mb-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Hotel className="w-6 h-6 text-[#F59E0B]" />
            <h4 className="text-xl font-bold text-white">
              Found {hotels.length} hotel{hotels.length !== 1 ? 's' : ''}
            </h4>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#6B7280] hover:bg-[#4B5563] text-white font-semibold transition-all flex items-center gap-2 cursor-pointer"
          >
            Close <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Hotel Cards */}
      <div className="space-y-4">
        {hotels.map((hotel, index) => renderHotelCard(hotel, index))}
      </div>

      {/* No Results */}
      {hotels.length === 0 && (
        <div className="glass-card rounded-3xl p-12 border-[rgba(148,163,184,0.2)] text-center">
          <Hotel className="w-16 h-16 text-[#6B7280] mx-auto mb-4" />
          <p className="text-xl text-white font-semibold mb-2">No hotels found</p>
          <p className="text-[#9CA3AF]">Try adjusting your filters or dates</p>
        </div>
      )}
      {photoModal && (
        <HotelPhotoModal
            hotelName={photoModal.hotelName}
            images={photoModal.images}
            onClose={() => setPhotoModal(null)}
        />
        )}
    </div>
  );
};

export default HotelSearchResults;

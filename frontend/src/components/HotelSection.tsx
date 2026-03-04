import { useState, useEffect } from 'react';
import { Hotel, Search, CheckCircle, AlertCircle, X, Star, MapPin, ExternalLink, Images } from 'lucide-react';
import { type Trip, type Hotel as HotelType, hotelApi } from '../services/api';
import HotelSearchResults from './HotelSearchResults';
import HotelSearchModal from './HotelSearchModal';
import ConfirmModal from './ConfirmModal';
import HotelPhotoModal from './HotelPhotoModal';

interface HotelSectionProps {
  trip: Trip;
}

const HotelSection = ({ trip }: HotelSectionProps) => {
  const [showHotelSearch, setShowHotelSearch] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [hotels, setHotels] = useState<HotelType[]>([]);
  const [selectedHotels, setSelectedHotels] = useState<HotelType[]>([]);
  const [loadingHotels, setLoadingHotels] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [photoModal, setPhotoModal] = useState<{ hotelName: string; images: string[] } | null>(null);

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [hotelToDelete, setHotelToDelete] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (trip.hotels && trip.hotels.length > 0) {
      setSelectedHotels(trip.hotels.filter((h) => h.is_selected));
    }
  }, [trip.hotels]);

  const handleSearchComplete = (hotelResults: HotelType[]) => {
    setHotels(hotelResults);
    setShowHotelSearch(true);
  };

  const handleHotelSelect = async (hotel: HotelType) => {
    setLoadingHotels(true);
    setError(null);
    try {
      const saved = await hotelApi.selectHotel(trip.id, hotel);
      setSelectedHotels((prev) => [...prev, saved]);
      setShowHotelSearch(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to select hotel');
    } finally {
      setLoadingHotels(false);
    }
  };

  const openDeleteModal = (hotelId: number) => {
    setHotelToDelete(hotelId);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (!hotelToDelete) return;
    setDeleting(true);
    try {
      await hotelApi.deleteHotel(trip.id, hotelToDelete);
      setSelectedHotels((prev) => prev.filter((h) => h.id !== hotelToDelete));
      setShowDeleteModal(false);
      setHotelToDelete(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove hotel');
    } finally {
      setDeleting(false);
    }
  };

  if (!trip.include_hotels) return null;

  return (
    <div className="mb-8 animate-fade-in">
      <div className="flex items-center gap-3 mb-4">
        <Hotel className="w-6 h-6 text-[#F59E0B]" />
        <h3 className="text-2xl font-bold text-white">Hotels</h3>
      </div>

      {error && (
        <div className="glass-card rounded-2xl p-4 mb-4 border-[#EF4444]/30 bg-[#EF4444]/10">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-[#EF4444]" />
            <p className="text-[#FCA5A5]">{error}</p>
          </div>
        </div>
      )}

      {/* Selected Hotels */}
      {selectedHotels.length > 0 && (
        <div className="space-y-4 mb-6">
          {selectedHotels.map((hotel) => (
            <div
              key={hotel.id}
              className="glass-card rounded-3xl overflow-hidden border-[#F59E0B]/30 bg-gradient-to-br from-[#F59E0B]/10 to-[#D97706]/5 animate-fade-in"
            >
              {/* Image strip */}
              

              <div className="p-5">
                {/* Name & Rating */}
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-xl font-bold text-white">{hotel.name}</h3>
                    <div className="flex items-center gap-2 text-[#9CA3AF] text-sm mt-1">
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
                  {hotel.rating && (
                    <div className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/30">
                      <Star className="w-4 h-4 text-[#F59E0B] fill-[#F59E0B]" />
                      <span className="text-white font-bold">{hotel.rating.toFixed(1)}</span>
                      {hotel.reviews_count && (
                        <span className="text-[#9CA3AF] text-xs">
                          ({hotel.reviews_count.toLocaleString()})
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Info message */}
                <div className="mb-4 p-3 rounded-xl bg-[#3B82F6]/10 border border-[#3B82F6]/30">
                  <p className="text-sm text-[#93C5FD]">
                    ℹ️ This hotel is saved for planning. To book, visit the hotel's website.
                  </p>
                </div>

                {/* Stay Details */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="p-3 bg-[#1F2937]/50 rounded-xl text-center">
                    <p className="text-xs text-[#9CA3AF] mb-1">Check-in</p>
                    <p className="text-sm text-white font-medium">{hotel.check_in_date}</p>
                  </div>
                  <div className="p-3 bg-[#1F2937]/50 rounded-xl text-center">
                    <p className="text-xs text-[#9CA3AF] mb-1">Nights</p>
                    <p className="text-sm text-white font-bold">{hotel.nights}</p>
                  </div>
                  <div className="p-3 bg-[#1F2937]/50 rounded-xl text-center">
                    <p className="text-xs text-[#9CA3AF] mb-1">Check-out</p>
                    <p className="text-sm text-white font-medium">{hotel.check_out_date}</p>
                  </div>
                </div>

                {/* Amenities */}
                {hotel.amenities && hotel.amenities.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {hotel.amenities.slice(0, 5).map((a) => (
                      <span
                        key={a}
                        className="px-2 py-1 rounded-lg bg-[#1F2937]/50 text-[#9CA3AF] text-xs border border-[rgba(148,163,184,0.15)]"
                      >
                        {a}
                      </span>
                    ))}
                  </div>
                )}

                {/* Price + Booking */}
                <div className="flex items-center justify-between pt-3 border-t border-[rgba(148,163,184,0.2)]">
                    <div>
                        <p className="text-xs text-[#9CA3AF]">Total Cost</p>
                        <p className="text-2xl font-bold text-[#22C55E]">
                        ${hotel.total_price?.toLocaleString()}{' '}
                        <span className="text-sm font-normal text-[#9CA3AF]">
                            (${hotel.price_per_night}/night)
                        </span>
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* View Photos button */}
                        {hotel.images && hotel.images.length > 0 && (
                        <button
                            onClick={() => setPhotoModal({ hotelName: hotel.name, images: hotel.images! })}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] transition-all text-sm font-medium"
                        >
                            <Images className="w-4 h-4" />
                            Photos ({hotel.images.length})
                        </button>
                        )}
                        {/* Book Now button */}
                        {hotel.booking_url && (
                        <a
                            href={hotel.booking_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/30 text-[#F59E0B] hover:bg-[#F59E0B]/20 transition-all text-sm font-medium"
                        >
                            Book Now <ExternalLink className="w-4 h-4" />
                        </a>
                        )}
                        {/* Remove Hotel button */}
                        {hotel.id && (
                        <button
                            onClick={() => openDeleteModal(hotel.id!)}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444] hover:bg-[#EF4444]/20 transition-all text-sm font-medium cursor-pointer"
                        >
                            <X className="w-4 h-4" />
                            Remove
                        </button>
                        )}
                    </div>
                    </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Search Button / Results */}
      {!showHotelSearch ? (
        <button
          onClick={() => setShowSearchModal(true)}
          className="px-6 py-3 rounded-xl font-bold text-white bg-[#F59E0B] hover:bg-[#D97706] hover:scale-105 active:scale-95 transition-all cursor-pointer"
        >
          <span className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            {selectedHotels.length > 0 ? 'Search Different Hotels' : 'Search Hotels'}
          </span>
        </button>
      ) : (
        <HotelSearchResults
          hotels={hotels}
          onSelectHotel={handleHotelSelect}
          loading={loadingHotels}
          onClose={() => setShowHotelSearch(false)}
        />
      )}

      <HotelSearchModal
        trip={trip}
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
        onSearchComplete={handleSearchComplete}
      />

      <ConfirmModal
        isOpen={showDeleteModal}
        onClose={() => { setShowDeleteModal(false); setHotelToDelete(null); }}
        onConfirm={confirmDelete}
        title="Remove Hotel?"
        message="Are you sure you want to remove this hotel from your trip? This action cannot be undone."
        confirmText="Remove Hotel"
        cancelText="Keep It"
        type="danger"
        loading={deleting}
      />
      {/* Hotel Photo Modal */}
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

export default HotelSection;

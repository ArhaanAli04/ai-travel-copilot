/**
 * MapPeek — blurred map strip that expands to full modal on click
 * Uses real Mapbox GL map underneath blur overlay
 */
import { useState } from 'react';
import { Map, MapPin } from 'lucide-react';
import DayMapModal from './DayMapModal';
import TripMapModal from './TripMapModal';
import type { TripDay, Trip } from '../../services/api';

interface DayMapPeekProps {
  day: TripDay;
  trip: Trip;
}

interface TripMapPeekProps {
  trip: Trip;
}

// ── Day Map Peek ──────────────────────────────────────────────────────────────
export const DayMapPeek = ({ day, trip }: DayMapPeekProps) => {
  const [modalOpen, setModalOpen] = useState(false);

  const locCount = day.activities?.filter(a => a.coordinates).length ?? 0;

  return (
    <>
      <button
        onClick={() => setModalOpen(true)}
        className="w-full mt-4 rounded-2xl overflow-hidden relative group cursor-pointer border border-[rgba(148,163,184,0.15)] hover:border-[#38BDF8]/40 transition-all"
        style={{ height: '120px' }}
      >
        {/* Blurred map background */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(https://api.mapbox.com/styles/v1/mapbox/dark-v11/static/${
              day.activities?.find(a => a.coordinates)?.coordinates
                ? `${day.activities.find(a => a.coordinates)!.coordinates!.lng},${day.activities.find(a => a.coordinates)!.coordinates!.lat},11`
                : '0,0,1'
            },400x120?access_token=${import.meta.env.VITE_MAPBOX_TOKEN}`,
            filter: 'blur(2px)',
            transform: 'scale(1.05)', // prevent blur edge artifacts
          }}
        />

        {/* Dark overlay */}
        <div className="absolute inset-0 bg-[#0a0e14]/60 group-hover:bg-[#0a0e14]/40 transition-all" />

        {/* Content */}
        <div className="absolute inset-0 flex items-center justify-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#38BDF8]/20 border border-[#38BDF8]/40 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Map className="w-5 h-5 text-[#38BDF8]" />
          </div>
          <div className="text-left">
            <p className="text-white font-semibold text-sm">
              {locCount > 0 ? `${locCount} locations mapped` : 'View Day Map'}
            </p>
            <p className="text-[#9CA3AF] text-xs">Click to explore route</p>
          </div>
          {/* Pin icons scattered */}
          <div className="flex gap-1 ml-2">
            {Array.from({ length: Math.min(locCount, 4) }).map((_, i) => (
              <MapPin key={i} className="w-3 h-3 text-[#38BDF8]/60" />
            ))}
          </div>
        </div>
      </button>

      <DayMapModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        day={day}
        trip={trip}
      />
    </>
  );
};

// ── Trip Overview Map Peek ────────────────────────────────────────────────────
export const TripMapPeek = ({ trip }: TripMapPeekProps) => {
  const [modalOpen, setModalOpen] = useState(false);

  const totalLocations = trip.days?.reduce(
    (sum, day) => sum + (day.activities?.filter(a => a.coordinates).length ?? 0), 0
  ) ?? 0;

  return (
    <>
      <button
        onClick={() => setModalOpen(true)}
        className="w-full mb-6 rounded-2xl overflow-hidden relative group cursor-pointer border border-[rgba(148,163,184,0.15)] hover:border-[#F59E0B]/40 transition-all"
        style={{ height: '140px' }}
      >
        {/* Mapbox static image as background */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(https://api.mapbox.com/styles/v1/mapbox/dark-v11/static/${
              trip.destinations[0]
            }/800x140?access_token=${import.meta.env.VITE_MAPBOX_TOKEN})`,
            filter: 'blur(2px)',
            transform: 'scale(1.05)',
          }}
        />
        <div className="absolute inset-0 bg-[#0a0e14]/55 group-hover:bg-[#0a0e14]/35 transition-all" />

        <div className="absolute inset-0 flex items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-[#F59E0B]/20 border border-[#F59E0B]/40 flex items-center justify-center group-hover:scale-110 transition-transform">
            <Map className="w-6 h-6 text-[#F59E0B]" />
          </div>
          <div className="text-left">
            <p className="text-white font-bold">Full Trip Map</p>
            <p className="text-[#9CA3AF] text-sm">
              {trip.destinations.join(' → ')} · {totalLocations} locations
            </p>
            <p className="text-[#6B7280] text-xs mt-0.5">Click to explore entire route</p>
          </div>
        </div>
      </button>

      <TripMapModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        trip={trip}
      />
    </>
  );
};

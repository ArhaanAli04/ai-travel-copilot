import { useEffect, useRef } from 'react';
import { X, MapPin } from 'lucide-react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { TripDay, Trip, Activity } from '../../services/api';

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

const CATEGORY_COLORS: Record<string, string> = {
  sightseeing: '#38BDF8',
  dining: '#F97316',
  entertainment: '#8B5CF6',
  shopping: '#F59E0B',
  relaxation: '#22C55E',
  default: '#9CA3AF',
};

interface Props {
  isOpen: boolean;
  onClose: () => void;
  day: TripDay;
  trip: Trip;
}

const DayMapModal = ({ isOpen, onClose, day, trip }: Props) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  const activitiesWithCoords = (day.activities ?? [])
    .filter(a => a.coordinates?.lat && a.coordinates?.lng)
    .sort((a, b) => a.order - b.order);

  useEffect(() => {
    if (!isOpen || !mapContainer.current || activitiesWithCoords.length === 0) return;

    // Centre on first activity
    const center = activitiesWithCoords[0].coordinates!;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/standard',
      center: [center.lng, center.lat],
      zoom: 14,
      pitch: 45,          // ← ADD: tilt for 3D building effect
  bearing: -17.6,     // ← ADD: slight rotation looks great
  antialias: true,    // ← ADD: smoother rendering
    });

    map.current.on('load', () => {
      if (!map.current) return;

      // ── Draw polyline connecting activities ──
      const coordinates = activitiesWithCoords.map(a => [
        a.coordinates!.lng,
        a.coordinates!.lat,
      ]);

      map.current.addSource('route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates },
        },
      });

      map.current.addLayer({
        id: 'route',
        type: 'line',
        source: 'route',
        paint: {
          'line-color': '#38BDF8',
          'line-width': 2,
          'line-dasharray': [2, 2],
          'line-opacity': 0.7,
        },
      });

      // ── Add numbered markers ──
      activitiesWithCoords.forEach((activity, index) => {
        const color = CATEGORY_COLORS[activity.category ?? 'default'] ?? CATEGORY_COLORS.default;

        // Custom HTML marker with order number
        const el = document.createElement('div');
        el.innerHTML = `
          <div style="
            width: 32px; height: 32px; border-radius: 50%;
            background: ${color}; border: 3px solid white;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 13px; color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
            cursor: pointer;
          ">${index + 1}</div>
        `;

        const popup = new mapboxgl.Popup({ offset: 20, closeButton: false })
          .setHTML(`
            <div style="
              background: #1F2937; border: 1px solid rgba(148,163,184,0.2);
              border-radius: 10px; padding: 10px 14px; min-width: 180px;
            ">
              <p style="color: white; font-weight: 600; margin: 0 0 4px 0; font-size: 14px;">
                ${index + 1}. ${activity.title}
              </p>
              ${activity.start_time ? `<p style="color: #9CA3AF; font-size: 12px; margin: 0 0 2px 0;">🕐 ${activity.start_time}</p>` : ''}
              ${activity.location ? `<p style="color: #9CA3AF; font-size: 12px; margin: 0 0 2px 0;">📍 ${activity.location}</p>` : ''}
              ${activity.estimated_cost ? `<p style="color: #22C55E; font-size: 12px; margin: 0;">💰 ${activity.estimated_cost} ${activity.cost_currency ?? ''}</p>` : ''}
            </div>
          `);

        new mapboxgl.Marker({ element: el })
          .setLngLat([activity.coordinates!.lng, activity.coordinates!.lat])
          .setPopup(popup)
          .addTo(map.current!);
      });

      // ── Fit map to all markers ──
      if (activitiesWithCoords.length > 1) {
        const bounds = activitiesWithCoords.reduce(
          (b, a) => b.extend([a.coordinates!.lng, a.coordinates!.lat]),
          new mapboxgl.LngLatBounds(
            [activitiesWithCoords[0].coordinates!.lng, activitiesWithCoords[0].coordinates!.lat],
            [activitiesWithCoords[0].coordinates!.lng, activitiesWithCoords[0].coordinates!.lat]
          )
        );
        map.current.fitBounds(bounds, { padding: 60, maxZoom: 15 });
      }
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl bg-[#0a0e14] border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl overflow-hidden"
        style={{ height: '80vh' }}>

        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-5 py-4 bg-gradient-to-b from-[#0a0e14] to-transparent">
          <div>
            <h3 className="text-white font-bold text-lg">
              Day {day.day_number} — {day.city}
            </h3>
            <p className="text-[#9CA3AF] text-xs mt-0.5">
              {activitiesWithCoords.length} locations · {new Date(day.date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Map */}
        <div ref={mapContainer} className="w-full h-full" />

        {/* Legend */}
        <div className="absolute bottom-4 left-4 z-10 flex flex-wrap gap-2">
          {Object.entries(CATEGORY_COLORS)
            .filter(([key]) => key !== 'default')
            .map(([category, color]) => (
              <span key={category}
                className="px-2 py-1 rounded-full text-xs font-medium"
                style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}
              >
                {category}
              </span>
            ))}
        </div>

        {/* No coordinates fallback */}
        {activitiesWithCoords.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <MapPin className="w-12 h-12 text-[#6B7280]" />
            <p className="text-white font-semibold">No location data available</p>
            <p className="text-[#9CA3AF] text-sm">Coordinates not yet geocoded for this day</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DayMapModal;

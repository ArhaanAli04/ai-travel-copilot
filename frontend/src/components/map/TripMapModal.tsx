import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { Trip } from '../../services/api';

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

const DAY_COLORS = [
  '#38BDF8', '#F97316', '#22C55E', '#8B5CF6',
  '#F59E0B', '#EC4899', '#14B8A6', '#EF4444',
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
  trip: Trip;
}

const TripMapModal = ({ isOpen, onClose, trip }: Props) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  const allActivities = (trip.days ?? []).flatMap(day =>
    (day.activities ?? [])
      .filter(a => a.coordinates?.lat && a.coordinates?.lng)
      .map(a => ({ ...a, day }))
  );

  useEffect(() => {
    if (!isOpen || !mapContainer.current || allActivities.length === 0) return;

    const center = allActivities[0].coordinates!;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/standard',
      center: [center.lng, center.lat],
      zoom: 12,
      pitch: 30,          // ← ADD: tilt for 3D building effect
  bearing: -17.6,     // ← ADD: slight rotation looks great
  antialias: true, 
    });

    map.current.on('load', () => {
      if (!map.current) return;

      // ── One polyline per day ──
      trip.days?.forEach((day, dayIndex) => {
        const dayActivities = (day.activities ?? [])
          .filter(a => a.coordinates?.lat && a.coordinates?.lng)
          .sort((a, b) => a.order - b.order);

        if (dayActivities.length < 2) return;

        const color = DAY_COLORS[dayIndex % DAY_COLORS.length];
        const coords = dayActivities.map(a => [a.coordinates!.lng, a.coordinates!.lat]);

        map.current!.addSource(`route-day-${day.id}`, {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: { type: 'LineString', coordinates: coords },
          },
        });

        map.current!.addLayer({
          id: `route-day-${day.id}`,
          type: 'line',
          source: `route-day-${day.id}`,
          paint: {
            'line-color': color,
            'line-width': 2,
            'line-dasharray': [2, 2],
            'line-opacity': 0.6,
          },
        });
      });

      // ── Markers for all activities ──
      allActivities.forEach(({ day, ...activity }) => {
        const dayIndex = (trip.days ?? []).findIndex(d => d.id === day.id);
        const color = DAY_COLORS[dayIndex % DAY_COLORS.length];

        const el = document.createElement('div');
        el.innerHTML = `
          <div style="
            width: 28px; height: 28px; border-radius: 50%;
            background: ${color}; border: 2px solid white;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 11px; color: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.5); cursor: pointer;
          ">${activity.order}</div>
        `;

        const popup = new mapboxgl.Popup({ offset: 18, closeButton: false })
          .setHTML(`
            <div style="
              background: #1F2937; border: 1px solid rgba(148,163,184,0.2);
              border-radius: 10px; padding: 10px 14px; min-width: 180px;
            ">
              <p style="color: ${color}; font-size: 11px; margin: 0 0 4px 0; font-weight: 600;">
                Day ${day.day_number} — ${day.city}
              </p>
              <p style="color: white; font-weight: 600; margin: 0 0 3px 0; font-size: 13px;">
                ${activity.title}
              </p>
              ${activity.start_time ? `<p style="color: #9CA3AF; font-size: 12px; margin: 0;">🕐 ${activity.start_time}</p>` : ''}
            </div>
          `);

        new mapboxgl.Marker({ element: el })
          .setLngLat([activity.coordinates!.lng, activity.coordinates!.lat])
          .setPopup(popup)
          .addTo(map.current!);
      });

      // ── Fit bounds ──
      if (allActivities.length > 1) {
        const bounds = allActivities.reduce(
          (b, a) => b.extend([a.coordinates!.lng, a.coordinates!.lat]),
          new mapboxgl.LngLatBounds(
            [allActivities[0].coordinates!.lng, allActivities[0].coordinates!.lat],
            [allActivities[0].coordinates!.lng, allActivities[0].coordinates!.lat]
          )
        );
        map.current.fitBounds(bounds, { padding: 80, maxZoom: 14 });
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
      <div className="relative w-full max-w-5xl bg-[#0a0e14] border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl overflow-hidden"
        style={{ height: '85vh' }}>

        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-5 py-4 bg-gradient-to-b from-[#0a0e14] to-transparent">
          <div>
            <h3 className="text-white font-bold text-lg">Full Trip Map</h3>
            <p className="text-[#9CA3AF] text-xs mt-0.5">
              {trip.destinations.join(' → ')} · {allActivities.length} locations across {trip.days?.length} days
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10 transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Map */}
        <div ref={mapContainer} className="w-full h-full" />

        {/* Day color legend */}
        <div className="absolute bottom-4 left-4 z-10 flex flex-wrap gap-2">
          {trip.days?.map((day, i) => (
            <span key={day.id}
              className="px-2 py-1 rounded-full text-xs font-medium"
              style={{
                background: `${DAY_COLORS[i % DAY_COLORS.length]}20`,
                color: DAY_COLORS[i % DAY_COLORS.length],
                border: `1px solid ${DAY_COLORS[i % DAY_COLORS.length]}40`
              }}
            >
              Day {day.day_number} · {day.city}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TripMapModal;

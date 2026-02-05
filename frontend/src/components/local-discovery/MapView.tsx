/**
 * MapView Component - Side panel map using Leaflet & OpenStreetMap
 */

import React, { useRef, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Tooltip, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { X, Navigation, Star } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  iconRetinaUrl: iconRetina,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface POI {
  poi_id: string;
  name: string;
  category: string;
  location: {
    type: string;
    coordinates: [number, number];
  };
  distance_km: number;
  distance_text: string;
  address?: string;
  average_rating?: number;
  reason?: string;
  feedback_count?: number;
}

interface MapViewProps {
  pois: POI[];
  userLocation: { lat: number; lon: number };
  onClose: () => void;
  onPOIClick?: (poiId: string) => void;
}

// Custom marker icons based on rating
const createCustomIcon = (rating?: number) => {
  let color = '#6B7280';
  if (rating) {
    if (rating >= 4.5) color = '#22C55E';
    else if (rating >= 3.5) color = '#F59E0B';
    else color = '#EF4444';
  }

  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: 30px;
        height: 30px;
        background-color: ${color};
        border: 3px solid white;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <span style="
          transform: rotate(45deg);
          color: white;
          font-size: 16px;
          font-weight: bold;
        ">📍</span>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30],
  });
};

const userLocationIcon = L.divIcon({
  className: 'user-location-marker',
  html: `
    <div style="
      width: 20px;
      height: 20px;
      background-color: #38BDF8;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.6), 0 2px 5px rgba(0,0,0,0.3);
    "></div>
  `,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

// Auto-fit bounds component
const AutoFitBounds: React.FC<{ pois: POI[]; userLocation: { lat: number; lon: number } }> = ({
  pois,
  userLocation,
}) => {
  const map = useMap();

  useEffect(() => {
    if (pois.length === 0) return;

    const bounds = L.latLngBounds([
      [userLocation.lat, userLocation.lon],
      ...pois.map((poi) => [poi.location.coordinates[1], poi.location.coordinates[0]] as [number, number]),
    ]);

    map.fitBounds(bounds, { padding: [50, 50] });
  }, [map, pois, userLocation]);

  return null;
};

export const MapView: React.FC<MapViewProps> = ({
  pois,
  userLocation,
  onClose,
  onPOIClick,
}) => {
  const mapRef = useRef<L.Map>(null);

  const getDirectionsUrl = (poi: POI) => {
    const [lon, lat] = poi.location.coordinates;
    return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;
  };

  const handleMarkerClick = (poiId: string) => {
    if (onPOIClick) {
      onPOIClick(poiId);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0a0e14] border-r border-[rgba(148,163,184,0.2)]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[rgba(148,163,184,0.2)] flex items-center justify-between flex-shrink-0 bg-[#0a0e14]/50 backdrop-blur-xl">
        <div>
          <h3 className="text-base font-semibold text-white">Map View</h3>
          <p className="text-xs text-[#9CA3AF]">
            {pois.length} {pois.length === 1 ? 'place' : 'places'}
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
          aria-label="Close map"
          title="Close map"
        >
          <X className="w-5 h-5 text-[#9CA3AF]" />
        </button>
      </div>

      {/* Map Container */}
      <div className="flex-1 relative">
        <MapContainer
          ref={mapRef}
          center={[userLocation.lat, userLocation.lon]}
          zoom={14}
          style={{ width: '100%', height: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <AutoFitBounds pois={pois} userLocation={userLocation} />

          {/* User Location */}
          <Marker
            position={[userLocation.lat, userLocation.lon]}
            icon={userLocationIcon}
          >
            <Popup>
              <div className="text-center py-1">
                <strong className="text-gray-900">Your Location</strong>
              </div>
            </Popup>
          </Marker>

          {/* Search Radius */}
          <Circle
            center={[userLocation.lat, userLocation.lon]}
            radius={5000}
            pathOptions={{
              color: '#38BDF8',
              fillColor: '#38BDF8',
              fillOpacity: 0.1,
              weight: 2,
            }}
          />

          {/* POI Markers */}
          {pois.map((poi) => {
            const [lon, lat] = poi.location.coordinates;
            return (
              <Marker
                key={poi.poi_id}
                position={[lat, lon]}
                icon={createCustomIcon(poi.average_rating)}
                eventHandlers={{
                  click: () => handleMarkerClick(poi.poi_id),
                }}
              >
                {/* Hover Tooltip */}
                <Tooltip
                  direction="top"
                  offset={[0, -20]}
                  opacity={0.95}
                  permanent={false}
                  className="custom-tooltip"
                >
                  <div className="text-center py-1">
                    <div className="font-semibold text-sm mb-1 text-gray-900">{poi.name}</div>
                    <div className="text-xs text-gray-600 mb-1">
                      {poi.category} • {poi.distance_text}
                    </div>
                    {poi.average_rating && poi.average_rating > 0 && (
                      <div className="flex items-center justify-center gap-1">
                        <span className="text-yellow-500">⭐</span>
                        <span className="text-xs font-medium text-gray-900">
                          {poi.average_rating.toFixed(1)}
                        </span>
                        {poi.feedback_count && poi.feedback_count > 0 && (
                          <span className="text-xs text-gray-400">
                            ({poi.feedback_count})
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </Tooltip>

                {/* Click Popup */}
                <Popup maxWidth={280} closeButton={true}>
                  <div className="p-2">
                    <h3 className="font-semibold text-gray-900 mb-1 text-sm">
                      {poi.name}
                    </h3>
                    
                    <div className="flex items-center gap-2 text-xs text-gray-600 mb-2">
                      <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
                        {poi.category}
                      </span>
                      <span>{poi.distance_text}</span>
                    </div>

                    {poi.average_rating && poi.average_rating > 0 && (
                      <div className="flex items-center gap-1 mb-2">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                        <span className="text-xs font-semibold text-gray-900">
                          {poi.average_rating.toFixed(1)}
                        </span>
                        {poi.feedback_count && poi.feedback_count > 0 && (
                          <span className="text-xs text-gray-500">
                            ({poi.feedback_count})
                          </span>
                        )}
                      </div>
                    )}

                    {poi.reason && (
                      <p className="text-xs text-gray-700 mb-2 line-clamp-2">
                        {poi.reason}
                      </p>
                    )}

                    <a
                      href={getDirectionsUrl(poi)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors w-full justify-center"
                    >
                      <Navigation className="w-3 h-3" />
                      Get Directions
                    </a>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="px-4 py-3 border-t border-[rgba(148,163,184,0.2)] bg-[#1F2937]/30 flex-shrink-0">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 bg-[#38BDF8] rounded-full ring-2 ring-white/20" />
            <span className="text-[#E5E7EB]">You</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 bg-[#22C55E] rounded-full ring-2 ring-white/20" />
            <span className="text-[#E5E7EB]">4.5+ ⭐</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 bg-[#F59E0B] rounded-full ring-2 ring-white/20" />
            <span className="text-[#E5E7EB]">3.5-4.5 ⭐</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 bg-[#EF4444] rounded-full ring-2 ring-white/20" />
            <span className="text-[#E5E7EB]">&lt;3.5 ⭐</span>
          </div>
        </div>
      </div>
    </div>
  );
};

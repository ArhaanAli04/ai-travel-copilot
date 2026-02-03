/**
 * POI Card Component
 * Displays a place recommendation with details
 */

import React from 'react';
import { type POI } from '../../types/local-discovery';
import { 
  MapPin, 
  Phone, 
  Globe, 
  Clock, 
  Star,
  ThumbsUp,
  ThumbsDown,
  ExternalLink,
  Navigation
} from 'lucide-react';

interface POICardProps {
  poi: POI;
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
}

export const POICard: React.FC<POICardProps> = ({ poi, onFeedback }) => {
  const [feedbackGiven, setFeedbackGiven] = React.useState<'up' | 'down' | null>(null);

  const handleFeedback = (type: 'thumbs_up' | 'thumbs_down') => {
    const feedbackType = type === 'thumbs_up' ? 'up' : 'down';
    setFeedbackGiven(feedbackType);
    onFeedback?.(poi.poi_id, type);
  };

  const openInMaps = () => {
    const [lon, lat] = poi.location.coordinates;
    const url = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
    window.open(url, '_blank');
  };

  return (
    <div id={`poi-${poi.poi_id}`}
    className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {poi.name}
          </h3>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
              {poi.category}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {poi.distance_text}
            </span>
          </div>
        </div>

        {/* Rating */}
        {poi.average_rating && poi.average_rating > 0 && (
          <div className="flex items-center gap-1 bg-green-50 px-2 py-1 rounded">
            <Star className="w-4 h-4 fill-green-500 text-green-500" />
            <span className="text-sm font-semibold text-green-700">
              {poi.average_rating.toFixed(1)}
            </span>
            {poi.feedback_count && (
              <span className="text-xs text-gray-500">({poi.feedback_count})</span>
            )}
          </div>
        )}
      </div>

      {/* Reason */}
      <p className="text-sm text-gray-700 mb-3 leading-relaxed">
        {poi.reason}
      </p>

      {/* Highlights */}
      {poi.highlights && poi.highlights.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {poi.highlights.map((highlight, index) => (
            <span
              key={index}
              className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
            >
              {highlight}
            </span>
          ))}
        </div>
      )}

      {/* Best For */}
      <div className="mb-3 p-2 bg-purple-50 rounded text-sm text-purple-700">
        <strong>Best for:</strong> {poi.best_for}
      </div>

      {/* Contact Info */}
      <div className="space-y-2 mb-3 text-sm">
        {poi.address && (
          <div className="flex items-start gap-2 text-gray-600">
            <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span className="flex-1">{poi.address}</span>
          </div>
        )}

        {poi.hours && (
          <div className="flex items-center gap-2 text-gray-600">
            <Clock className="w-4 h-4 flex-shrink-0" />
            <span>{poi.hours}</span>
          </div>
        )}

        {poi.phone && (
          <div className="flex items-center gap-2 text-gray-600">
            <Phone className="w-4 h-4 flex-shrink-0" />
            <a 
              href={`tel:${poi.phone}`}
              className="hover:text-blue-600 transition-colors"
            >
              {poi.phone}
            </a>
          </div>
        )}

        {poi.website && (
          <div className="flex items-center gap-2 text-gray-600">
            <Globe className="w-4 h-4 flex-shrink-0" />
            <a
              href={poi.website}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 transition-colors flex items-center gap-1"
            >
              Visit website
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        {/* Feedback Buttons */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 mr-2">Helpful?</span>
          <button
            onClick={() => handleFeedback('thumbs_up')}
            disabled={feedbackGiven !== null}
            className={`p-1.5 rounded transition-colors ${
              feedbackGiven === 'up'
                ? 'bg-green-100 text-green-600'
                : 'hover:bg-gray-100 text-gray-500'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <ThumbsUp className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleFeedback('thumbs_down')}
            disabled={feedbackGiven !== null}
            className={`p-1.5 rounded transition-colors ${
              feedbackGiven === 'down'
                ? 'bg-red-100 text-red-600'
                : 'hover:bg-gray-100 text-gray-500'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <ThumbsDown className="w-4 h-4" />
          </button>
        </div>

        {/* Directions Button */}
        <button
          onClick={openInMaps}
          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
        >
          <Navigation className="w-4 h-4" />
          Directions
        </button>
      </div>

      {/* Feedback Thank You */}
      {feedbackGiven && (
        <div className="mt-2 text-xs text-green-600 text-center">
          Thanks for your feedback! 🙏
        </div>
      )}
    </div>
  );
};

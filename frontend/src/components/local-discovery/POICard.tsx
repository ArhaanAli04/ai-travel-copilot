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
  Navigation,
  Sparkles,
  Camera
} from 'lucide-react';
import { ImageModal } from './ImageModal';
interface POICardProps {
  poi: POI;
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
}

export const POICard: React.FC<POICardProps> = ({ poi, onFeedback }) => {
  const [feedbackGiven, setFeedbackGiven] = React.useState<'up' | 'down' | null>(null);
  const [showPhotos, setShowPhotos]       = React.useState(false);
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
    <div 
      id={`poi-${poi.poi_id}`}
      className="group p-4 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] hover:bg-[#1F2937]/70 transition-all animate-fade-in"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white mb-2">
            {poi.name}
          </h3>
          
          {/* Category & Distance */}
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="px-2 py-1 rounded-full bg-[#38BDF8]/10 text-[#38BDF8] text-xs font-medium border border-[#38BDF8]/30">
              {poi.category}
            </span>
            <div className="flex items-center gap-1 text-[#9CA3AF]">
              <MapPin className="w-3.5 h-3.5" />
              <span>{poi.distance_text}</span>
            </div>
          </div>
        </div>

        {/* Rating Badge */}
        {poi.average_rating && poi.average_rating > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#22C55E]/10 border border-[#22C55E]/30 ml-3 flex-shrink-0">
            <Star className="w-4 h-4 fill-[#22C55E] text-[#22C55E]" />
            <span className="text-sm font-bold text-[#22C55E]">
              {poi.average_rating.toFixed(1)}
            </span>
            {poi.feedback_count && poi.feedback_count > 0 && (
              <span className="text-xs text-[#9CA3AF]">({poi.feedback_count})</span>
            )}
          </div>
        )}
      </div>

      {/* Reason / Description */}
      {poi.reason && (
        <p className="text-[#E5E7EB] text-sm mb-3 leading-relaxed">
          {poi.reason}
        </p>
      )}

      {/* Highlights Tags */}
      {poi.highlights && poi.highlights.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {poi.highlights.map((highlight, index) => (
            <span
              key={index}
              className="text-xs px-2 py-1 bg-white/5 text-[#9CA3AF] rounded border border-[rgba(148,163,184,0.2)]"
            >
              {highlight}
            </span>
          ))}
        </div>
      )}

      {/* Best For */}
      {poi.best_for && (
        <div className="mb-3 p-3 rounded-lg bg-[#8B5CF6]/10 border border-[#8B5CF6]/30">
          <div className="flex items-center gap-2 text-sm text-[#8B5CF6]">
            <Sparkles className="w-4 h-4" />
            <span className="font-semibold">Best for:</span>
            <span>{poi.best_for}</span>
          </div>
        </div>
      )}

      {/* Contact Info */}
      <div className="space-y-2 mb-4 text-sm">
        {poi.address && (
          <div className="flex items-start gap-2 text-[#9CA3AF]">
            <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span className="flex-1">{poi.address}</span>
          </div>
        )}

        {poi.hours && (
          <div className="flex items-center gap-2 text-[#9CA3AF]">
            <Clock className="w-4 h-4 flex-shrink-0" />
            <span>{poi.hours}</span>
          </div>
        )}

        {poi.phone && (
          <div className="flex items-center gap-2 text-[#9CA3AF]">
            <Phone className="w-4 h-4 flex-shrink-0" />
            <a 
              href={`tel:${poi.phone}`}
              className="hover:text-[#38BDF8] transition-colors"
            >
              {poi.phone}
            </a>
          </div>
        )}

        {poi.website && (
          <div className="flex items-center gap-2 text-[#9CA3AF]">
            <Globe className="w-4 h-4 flex-shrink-0" />
            <a
              href={poi.website}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[#38BDF8] transition-colors flex items-center gap-1"
            >
              Visit website
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-[rgba(148,163,184,0.1)]">
        {/* Feedback Buttons */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6B7280] mr-1">Helpful?</span>
          <button
            onClick={() => handleFeedback('thumbs_up')}
            disabled={feedbackGiven !== null}
            className={`p-1.5 rounded-lg transition-all ${
              feedbackGiven === 'up'
                ? 'bg-[#22C55E]/20 text-[#22C55E] border border-[#22C55E]/30'
                : 'bg-white/5 border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:bg-[#22C55E]/10 hover:text-[#22C55E]'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title="Helpful"
          >
            <ThumbsUp className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleFeedback('thumbs_down')}
            disabled={feedbackGiven !== null}
            className={`p-1.5 rounded-lg transition-all ${
              feedbackGiven === 'down'
                ? 'bg-[#EF4444]/20 text-[#EF4444] border border-[#EF4444]/30'
                : 'bg-white/5 border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:bg-[#EF4444]/10 hover:text-[#EF4444]'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title="Not helpful"
          >
            <ThumbsDown className="w-4 h-4" />
          </button>
        </div>

        {/* ↓ RIGHT SIDE BUTTONS — replace old Directions-only button with this ↓ */}
        <div className="flex items-center gap-2">
          {/* Photos Button */}
          <button
            onClick={() => setShowPhotos(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/5 border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] text-sm font-medium hover:bg-[#8B5CF6]/10 hover:text-[#8B5CF6] hover:border-[#8B5CF6]/30 transition-all"
          >
            <Camera className="w-4 h-4" />
            Photos
          </button>

          {/* Directions Button */}
          <button
            onClick={openInMaps}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#38BDF8] text-white text-sm font-medium hover:bg-[#3B82F6] transition-all shadow-lg hover:shadow-[#38BDF8]/20"
          >
            <Navigation className="w-4 h-4" />
            Directions
          </button>
        </div>
      </div>

      {/* Feedback Thank You */}
      {feedbackGiven && (
        <div className="mt-3 p-2 rounded-lg bg-[#22C55E]/10 border border-[#22C55E]/30 text-center">
          <span className="text-xs text-[#22C55E] font-medium">
            ✓ Thanks for your feedback!
          </span>
        </div>
      )}

      {/* Photo Modal */}                          {/* ← ADD THIS BLOCK */}
      {showPhotos && (
        <ImageModal
          poiId={poi.poi_id}
          poiName={poi.name}
          category={poi.category}
          onClose={() => setShowPhotos(false)}
        />
      )}
    </div>
  );
};

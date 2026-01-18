import React, { useState, useEffect } from 'react';
import { Card } from './shared/Card';
import { disruptionApi } from '../services/api';
import type { DisruptionCase, PassengerRights } from '../types/disruption';

interface RightsSummaryCardProps {
  disruptionCase: DisruptionCase;
}

export const RightsSummaryCard: React.FC<RightsSummaryCardProps> = ({ disruptionCase }) => {
  const [rights, setRights] = useState<PassengerRights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    fetchRights();
  }, [disruptionCase.id]);

  const fetchRights = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await disruptionApi.explainRights(disruptionCase.id);
      setRights(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch passenger rights');
      console.error('Rights fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const regionColors: Record<string, { bg: string; text: string; border: string }> = {
    EU: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
    US: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30' },
    UK: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30' },
    UNKNOWN: { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/30' },
  };

  if (loading) {
    return (
      <Card className="space-y-4">
        <div className="flex items-center gap-2">
          <span>⚖️</span>
          <h3 className="text-white font-semibold">Your Rights</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }

  if (error || !rights) {
    return (
      <Card className="space-y-4">
        <div className="flex items-center gap-2">
          <span>⚖️</span>
          <h3 className="text-white font-semibold">Your Rights</h3>
        </div>
        <div className="text-gray-400 text-sm text-center py-4">
          {error || 'Unable to load rights information'}
        </div>
        <button
          onClick={fetchRights}
          className="w-full py-2 px-4 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors text-sm"
        >
          Retry
        </button>
      </Card>
    );
  }

  const regionColor = regionColors[rights.region as keyof typeof regionColors] || regionColors.UNKNOWN;

  return (
    <Card className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>⚖️</span>
          Your Rights
        </h3>
        {rights.cached && (
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
            </svg>
            <span>Cached</span>
          </div>
        )}
      </div>

      {/* Regulation Badge */}
      <div className={`p-3 rounded-lg ${regionColor.bg} border ${regionColor.border}`}>
        <div className="text-xs text-gray-400 mb-1">Applicable Regulation</div>
        <div className={`font-semibold ${regionColor.text}`}>
          {rights.applicable_regulation || 'Checking...'}
        </div>
      </div>

      {/* Compensation Amount */}
      {rights.compensation_amount && rights.compensation_amount > 0 && (
        <div className="p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg">
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-1">Estimated Compensation</div>
            <div className="text-3xl font-bold text-green-400">
              {rights.compensation_currency}{rights.compensation_amount}
            </div>
          </div>
        </div>
      )}

      {/* Rights Bullets */}
      {rights.rights_bullets && rights.rights_bullets.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-gray-500 uppercase">Your Entitlements</div>
          <ul className="space-y-2">
            {rights.rights_bullets.slice(0, expanded ? undefined : 3).map((right, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="text-green-400 flex-shrink-0 mt-0.5">✓</span>
                <span className="text-gray-300">{right}</span>
              </li>
            ))}
          </ul>
          
          {rights.rights_bullets.length > 3 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-blue-400 hover:text-blue-300 text-sm transition-colors mt-2"
            >
              {expanded ? '← Show less' : `+ ${rights.rights_bullets.length - 3} more rights`}
            </button>
          )}
        </div>
      )}

      {/* Next Steps */}
      {rights.next_steps && rights.next_steps.length > 0 && (
        <div className="space-y-2 pt-3 border-t border-[rgba(148,163,184,0.2)]">
          <div className="text-xs text-gray-500 uppercase">Next Steps</div>
          <ol className="space-y-2">
            {rights.next_steps.slice(0, expanded ? undefined : 2).map((step, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="text-blue-400 font-semibold flex-shrink-0">{index + 1}.</span>
                <span className="text-gray-300">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* View Full Details Button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full py-2 px-4 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors text-sm font-medium"
      >
        {expanded ? 'Hide Details' : 'View Full Rights'}
      </button>

      {/* Source Links (when expanded) */}
      {expanded && rights.source_links && rights.source_links.length > 0 && (
        <div className="pt-3 border-t border-[rgba(148,163,184,0.2)] space-y-2">
          <div className="text-xs text-gray-500 uppercase">Official Sources</div>
          <div className="space-y-1">
            {rights.source_links.map((source, index) => (
              <a
                key={index}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                  <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                </svg>
                <span className="truncate">{source.title}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Last Updated */}
      {rights.generated_at && (
        <div className="text-xs text-gray-500 text-center pt-2 border-t border-[rgba(148,163,184,0.2)]">
          Generated {new Date(rights.generated_at).toLocaleString()}
        </div>
      )}
    </Card>
  );
};

export default RightsSummaryCard;

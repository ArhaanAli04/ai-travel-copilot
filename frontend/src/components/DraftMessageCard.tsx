import React, { useState, useEffect } from 'react';
import { disruptionApi } from '../services/api';
import type { DisruptionCase } from '../types/disruption';

interface DraftMessage {
  id: number;
  case_id: number;
  recipient: string;
  subject: string;
  body: string;
  tone: string;
  generated_at: string;
}

interface DraftMessageCardProps {
  disruptionCase: DisruptionCase;
}

export const DraftMessageCard: React.FC<DraftMessageCardProps> = ({ disruptionCase }) => {
  const [drafts, setDrafts] = useState<DraftMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDraft, setSelectedDraft] = useState<number>(0);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [hasFetched, setHasFetched] = useState(false); 

  useEffect(() => {
    // ✅ FIX: Only fetch once per case
    if (!hasFetched) {
        fetchDrafts();
        setHasFetched(true);
    }
    }, [disruptionCase.id]); // ✅ Re-run only when case ID changes

    // ✅ Reset hasFetched when case changes
    useEffect(() => {
    setHasFetched(false);
    }, [disruptionCase.id]);

  const fetchDrafts = async () => {
    if (loading) return; // ✅ Prevent multiple simultaneous calls
    
    setLoading(true);
    setError(null);
    
    try {
        // ✅ Step 1: Check if drafts already exist
        console.log(`🔍 Checking for existing drafts for case ${disruptionCase.id}...`);
        const existingDrafts = await disruptionApi.getMessages(disruptionCase.id);
        
        if (existingDrafts && existingDrafts.length > 0) {
        console.log(`✅ Found ${existingDrafts.length} existing drafts`);
        setDrafts(existingDrafts.slice(0, 3));
        setSelectedDraft(0);
        return;
        }
        
        // ✅ Step 2: Generate new drafts only if none exist
        console.log('🔄 No drafts found, generating new ones...');
        const response = await disruptionApi.generateDrafts(disruptionCase.id);
        
        if (response.drafts && response.drafts.length > 0) {
        console.log(`✅ Generated ${response.drafts.length} new drafts`);
        setDrafts(response.drafts);
        setSelectedDraft(0);
        } else {
        throw new Error('No drafts were generated');
        }
        
    } catch (err: any) {
        console.error('Drafts fetch error:', err);
        setError(err.message || 'Failed to load draft messages');
    } finally {
        setLoading(false);
    }
    };

  const handleRegenerate = async () => {
    setRegenerating(true);
    setHasFetched(false); // ✅ Allow refetch
    try {
        await fetchDrafts();
    } finally {
        setRegenerating(false);
    }
    };

  const copyToClipboard = async (draft: DraftMessage) => {
    const fullText = `Subject: ${draft.subject}\n\n${draft.body}`;
    try {
      await navigator.clipboard.writeText(fullText);
      setCopiedId(draft.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const toneIcons: Record<string, string> = {
    professional: '💼',
    firm: '⚖️',
    friendly: '🤝',
    urgent: '⚠️',
  };

  const toneColors: Record<string, string> = {
    professional: 'text-blue-400',
    firm: 'text-orange-400',
    friendly: 'text-green-400',
    urgent: 'text-red-400',
  };

  if (loading) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>📧</span>
          Draft Messages
        </h3>
        <div className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-400 text-sm">Generating draft messages...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>📧</span>
          Draft Messages
        </h3>
        <div className="text-center py-8 space-y-4">
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={fetchDrafts}
            className="px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (drafts.length === 0) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>📧</span>
          Draft Messages
        </h3>
        <div className="text-center py-8">
          <p className="text-gray-400 text-sm">No draft messages available</p>
        </div>
      </div>
    );
  }

  const currentDraft = drafts[selectedDraft];

  return (
    <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>📧</span>
          Draft Messages
        </h3>
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="text-sm text-gray-400 hover:text-white transition-colors disabled:opacity-50"
        >
          {regenerating ? (
            <span className="flex items-center gap-1">
              <div className="animate-spin rounded-full h-3 w-3 border-b border-gray-400"></div>
              Generating...
            </span>
          ) : (
            '🔄 Regenerate'
          )}
        </button>
      </div>

      {/* Draft Selector Tabs */}
      {drafts.length > 1 && (
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
          {drafts.map((draft, index) => {
            const icon = toneIcons[draft.tone] || '📝';
            const color = toneColors[draft.tone] || 'text-gray-400';
            
            return (
              <button
                key={draft.id}
                onClick={() => setSelectedDraft(index)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  selectedDraft === index
                    ? 'bg-blue-500/20 border border-blue-500/40 text-blue-400'
                    : 'bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] text-gray-400 hover:text-white'
                }`}
              >
                <span className="mr-1">{icon}</span>
                {draft.tone.charAt(0).toUpperCase() + draft.tone.slice(1)}
              </button>
            );
          })}
        </div>
      )}

      {/* Current Draft Display */}
      <div className="space-y-4">
        {/* Recipient */}
        <div className="p-3 bg-[rgba(15,23,42,0.5)] rounded-lg border border-[rgba(148,163,184,0.2)]">
          <div className="text-xs text-gray-500 mb-1">To:</div>
          <div className="text-white font-medium">{currentDraft.recipient}</div>
        </div>

        {/* Subject */}
        <div className="p-3 bg-[rgba(15,23,42,0.5)] rounded-lg border border-[rgba(148,163,184,0.2)]">
          <div className="text-xs text-gray-500 mb-1">Subject:</div>
          <div className="text-white font-medium">{currentDraft.subject}</div>
        </div>

        {/* Body */}
        <div className="p-4 bg-[rgba(15,23,42,0.5)] rounded-lg border border-[rgba(148,163,184,0.2)]">
          <div className="text-xs text-gray-500 mb-3">Message:</div>
          <div className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
            {currentDraft.body}
          </div>
        </div>

        {/* Tone Badge */}
        <div className="flex items-center justify-between p-3 bg-[rgba(15,23,42,0.5)] rounded-lg border border-[rgba(148,163,184,0.2)]">
          <span className="text-xs text-gray-500">Tone:</span>
          <span className={`text-sm font-medium flex items-center gap-1 ${toneColors[currentDraft.tone] || 'text-gray-400'}`}>
            <span>{toneIcons[currentDraft.tone] || '📝'}</span>
            {currentDraft.tone.charAt(0).toUpperCase() + currentDraft.tone.slice(1)}
          </span>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3 pt-2">
          <button
            onClick={() => copyToClipboard(currentDraft)}
            className={`py-3 px-4 rounded-lg text-sm font-semibold transition-all ${
              copiedId === currentDraft.id
                ? 'bg-green-500/20 border border-green-500/40 text-green-400'
                : 'bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-400'
            }`}
          >
            {copiedId === currentDraft.id ? (
              <>
                <span className="mr-1">✓</span>
                Copied!
              </>
            ) : (
              <>
                <span className="mr-1">📋</span>
                Copy to Clipboard
              </>
            )}
          </button>

          <button
            onClick={() => {
              const mailtoLink = `mailto:${currentDraft.recipient}?subject=${encodeURIComponent(currentDraft.subject)}&body=${encodeURIComponent(currentDraft.body)}`;
              window.location.href = mailtoLink;
            }}
            className="py-3 px-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-sm font-semibold rounded-lg transition-all"
          >
            <span className="mr-1">✉️</span>
            Open in Email
          </button>
        </div>

        {/* Tips */}
        <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-blue-400 flex-shrink-0">💡</span>
            <div className="text-xs text-blue-300">
              <div className="font-semibold mb-1">Pro Tip</div>
              <div className="text-blue-400/80">
                Review and personalize the message before sending. Include your booking reference (PNR) and contact details.
              </div>
            </div>
          </div>
        </div>

        {/* Generated At */}
        {currentDraft.generated_at && (
          <div className="text-xs text-gray-500 text-center pt-2 border-t border-[rgba(148,163,184,0.2)]">
            Generated {new Date(currentDraft.generated_at).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
};

export default DraftMessageCard;

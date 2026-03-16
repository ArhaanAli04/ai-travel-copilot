import { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Shield,
  Scale,
  Phone,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  AlertTriangle,
  CheckSquare,
  Square,
  Loader2,
  Maximize2,  // ← ADD
  Minimize2,  // ← ADD
} from 'lucide-react';
import { documentationApi } from '../services/api';
import type {
  DocumentationResponse,
  DocumentChecklist,
  EntryRequirements,
  LegalAdvisories,
  EmergencyContacts,
  AdvisorySeverity,
} from '../types/documentation';

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

type TabId = 'documents' | 'entry' | 'legal' | 'emergency';

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'documents',  label: 'Documents',  icon: <FileText className="w-4 h-4" /> },
  { id: 'entry',      label: 'Entry',      icon: <Shield className="w-4 h-4" /> },
  { id: 'legal',      label: 'Legal',      icon: <Scale className="w-4 h-4" /> },
  { id: 'emergency',  label: 'SOS',        icon: <Phone className="w-4 h-4" /> },
];

const SEVERITY_CONFIG: Record<AdvisorySeverity, {
  bg: string; border: string; text: string; badge: string; dot: string; label: string;
}> = {
  critical: {
    bg:     'bg-[#EF4444]/8',
    border: 'border-[#EF4444]/30',
    text:   'text-[#EF4444]',
    badge:  'bg-[#EF4444]/15 text-[#EF4444]',
    dot:    'bg-[#EF4444]',
    label:  'Prohibited',
  },
  warning: {
    bg:     'bg-[#F59E0B]/8',
    border: 'border-[#F59E0B]/30',
    text:   'text-[#F59E0B]',
    badge:  'bg-[#F59E0B]/15 text-[#F59E0B]',
    dot:    'bg-[#F59E0B]',
    label:  'Restricted',
  },
  info: {
    bg:     'bg-[#38BDF8]/8',
    border: 'border-[#38BDF8]/20',
    text:   'text-[#38BDF8]',
    badge:  'bg-[#38BDF8]/15 text-[#38BDF8]',
    dot:    'bg-[#38BDF8]',
    label:  'Info',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────────────

interface DocumentationModalProps {
  isOpen:     boolean;
  onClose:    () => void;
  tripId:     number;
  tripTitle:  string;
  destinations: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Skeleton
// ─────────────────────────────────────────────────────────────────────────────

const SkeletonBlock = ({ className = '' }: { className?: string }) => (
  <div className={`bg-[#1F2937]/60 rounded-lg animate-pulse ${className}`} />
);

const DocumentationSkeleton = () => (
  <div className="space-y-4 p-6">
    <SkeletonBlock className="h-10 w-full" />
    <SkeletonBlock className="h-10 w-3/4" />
    <div className="space-y-3 mt-6">
      {[1, 2, 3].map(i => (
        <div key={i} className="p-4 rounded-xl border border-[rgba(148,163,184,0.1)] space-y-2">
          <SkeletonBlock className="h-4 w-1/3" />
          <SkeletonBlock className="h-3 w-full" />
          <SkeletonBlock className="h-3 w-5/6" />
          <SkeletonBlock className="h-3 w-2/3" />
        </div>
      ))}
    </div>
    <div className="flex items-center justify-center gap-3 pt-4 text-[#9CA3AF]">
      <Loader2 className="w-4 h-4 animate-spin text-[#38BDF8]" />
      <span className="text-sm">Fetching live visa & entry data with Google Search…</span>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

// Destination accordion wrapper
const DestinationAccordion = ({
  destination,
  defaultOpen = true,
  children,
}: {
  destination: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-[rgba(148,163,184,0.12)] overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-[#1F2937]/40 hover:bg-[#1F2937]/70 transition-colors"
      >
        <span className="text-sm font-semibold text-white">{destination}</span>
        {open
          ? <ChevronUp className="w-4 h-4 text-[#9CA3AF]" />
          : <ChevronDown className="w-4 h-4 text-[#9CA3AF]" />}
      </button>
      {open && <div className="p-4 space-y-3 bg-[#0a0e14]/40">{children}</div>}
    </div>
  );
};

// ── Documents Tab ─────────────────────────────────────────────────────────────

const DocumentsTab = ({
  data,
  checkedItems,
  onToggle,
}: {
  data: DocumentChecklist[];
  checkedItems: Record<string, boolean>;
  onToggle: (key: string) => void;
}) => (
  <div className="space-y-4">
    {data.map((dest, di) => (
      <DestinationAccordion key={di} destination={dest.destination} defaultOpen={di === 0}>

        {/* Visa info row */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="p-3 rounded-lg bg-[#1F2937]/50 border border-[rgba(148,163,184,0.08)]">
            <p className="text-xs text-[#6B7280] uppercase tracking-wide mb-0.5">Visa Type</p>
            <p className="text-xs font-semibold text-white leading-tight">{dest.visa_type}</p>
          </div>
          <div className="p-3 rounded-lg bg-[#1F2937]/50 border border-[rgba(148,163,184,0.08)]">
            <p className="text-xs text-[#6B7280] uppercase tracking-wide mb-0.5">Cost</p>
            <p className="text-xs font-semibold text-[#22C55E] leading-tight">{dest.visa_cost}</p>
          </div>
          <div className="p-3 rounded-lg bg-[#1F2937]/50 border border-[rgba(148,163,184,0.08)]">
            <p className="text-xs text-[#6B7280] uppercase tracking-wide mb-0.5">Processing</p>
            <p className="text-xs font-semibold text-[#F59E0B] leading-tight">{dest.processing_days}</p>
          </div>
          <div className="p-3 rounded-lg bg-[#1F2937]/50 border border-[rgba(148,163,184,0.08)]">
            <p className="text-xs text-[#6B7280] uppercase tracking-wide mb-0.5">Apply</p>
            <a
              href={dest.apply_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold text-[#38BDF8] hover:text-[#7DD3FC] flex items-center gap-1 transition-colors"
            >
              Official Site <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* Procedure */}
        <div className="p-3 rounded-lg bg-[#1F2937]/30 border border-[rgba(148,163,184,0.08)] mb-3">
          <p className="text-xs text-[#6B7280] uppercase tracking-wide mb-1">Procedure</p>
          <p className="text-sm text-[#9CA3AF] leading-relaxed">{dest.procedure}</p>
        </div>

        {/* Checklist items */}
        <div>
          <p className="text-xs text-[#6B7280] uppercase tracking-wide mb-2">Document Checklist</p>
          <div className="space-y-2">
            {dest.checklist_items.map((item, ii) => {
              const key = `${di}-${ii}`;
              const checked = checkedItems[key] ?? false;
              return (
                <button
                  key={ii}
                  onClick={() => onToggle(key)}
                  className="w-full flex items-start gap-3 p-2.5 rounded-lg hover:bg-[#1F2937]/50 transition-colors text-left group"
                >
                  <div className="mt-0.5 flex-shrink-0">
                    {checked
                      ? <CheckSquare className="w-4 h-4 text-[#22C55E]" />
                      : <Square className="w-4 h-4 text-[#4B5563] group-hover:text-[#9CA3AF] transition-colors" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium transition-colors ${checked ? 'text-[#6B7280] line-through' : 'text-white'}`}>
                        {item.item}
                      </span>
                      {item.required && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#EF4444]/15 text-[#EF4444] font-medium flex-shrink-0">
                          Required
                        </span>
                      )}
                    </div>
                    {item.notes && (
                      <p className="text-sm text-[#6B7280] mt-0.5 leading-relaxed">{item.notes}</p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

      </DestinationAccordion>
    ))}
  </div>
);

// ── Entry Requirements Tab ────────────────────────────────────────────────────

const ENTRY_CATEGORY_COLORS: Record<string, string> = {
  Health:             'text-[#22C55E] bg-[#22C55E]/10',
  Customs:            'text-[#F59E0B] bg-[#F59E0B]/10',
  'Restricted Items': 'text-[#EF4444] bg-[#EF4444]/10',
  'Minor Travel':     'text-[#A78BFA] bg-[#A78BFA]/10',
  Currency:           'text-[#38BDF8] bg-[#38BDF8]/10',
};

const EntryTab = ({ data }: { data: EntryRequirements[] }) => (
  <div className="space-y-4">
    {data.map((dest, di) => (
      <DestinationAccordion key={di} destination={dest.destination} defaultOpen={di === 0}>
        <div className="space-y-2">
          {dest.items.map((item, ii) => {
            const color = ENTRY_CATEGORY_COLORS[item.category] ?? 'text-[#9CA3AF] bg-[#9CA3AF]/10';
            return (
              <div
                key={ii}
                className="p-3 rounded-lg bg-[#1F2937]/40 border border-[rgba(148,163,184,0.08)]"
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${color}`}>
                    {item.category}
                  </span>
                  <span className="text-xs font-medium text-white">{item.description}</span>
                </div>
                <p className="text-sm text-[#9CA3AF] leading-relaxed">{item.details}</p>
              </div>
            );
          })}
        </div>
      </DestinationAccordion>
    ))}
  </div>
);

// ── Legal Advisories Tab ──────────────────────────────────────────────────────

const LegalTab = ({ data }: { data: LegalAdvisories[] }) => (
  <div className="space-y-4">
    {data.map((dest, di) => (
      <DestinationAccordion key={di} destination={dest.destination} defaultOpen={di === 0}>
        <div className="space-y-2">
          {dest.advisories.map((adv, ai) => {
            const cfg = SEVERITY_CONFIG[adv.severity] ?? SEVERITY_CONFIG.info;
            return (
              <div
                key={ai}
                className={`p-3 rounded-lg border ${cfg.bg} ${cfg.border}`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot}`} />
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.badge}`}>
                    {cfg.label}
                  </span>
                  <span className="text-xs font-medium text-white">{adv.category}</span>
                </div>
                <p className="text-sm text-[#9CA3AF] leading-relaxed pl-4">{adv.description}</p>
              </div>
            );
          })}
        </div>
      </DestinationAccordion>
    ))}
  </div>
);

// ── Emergency / SOS Tab ───────────────────────────────────────────────────────

const EmergencyTab = ({ data, originCountry }: { data: EmergencyContacts[]; originCountry: string  }) => (
  <div className="space-y-4">
    {data.map((dest, di) => (
      <DestinationAccordion key={di} destination={dest.destination} defaultOpen={di === 0}>

        {/* Emergency numbers grid */}
        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { label: 'Police',    number: dest.police },
            { label: 'Ambulance', number: dest.ambulance },
            { label: 'Fire',      number: dest.fire },
          ].map(({ label, number }) => (
            <a
              key={label}
              href={`tel:${number}`}
              className="flex flex-col items-center p-3 rounded-xl bg-[#EF4444]/8 border border-[#EF4444]/20 hover:bg-[#EF4444]/15 transition-colors group"
            >
              <Phone className="w-4 h-4 text-[#EF4444] mb-1.5 group-hover:scale-110 transition-transform" />
              <span className="text-sm font-bold text-white">{number}</span>
              <span className="text-xs text-[#9CA3AF] mt-0.5">{label}</span>
            </a>
          ))}
        </div>

        {/* Embassy */}
        <div className="p-3 rounded-lg bg-[#1F2937]/50 border border-[rgba(148,163,184,0.08)] space-y-1.5">
          <p className="text-xs text-[#6B7280] uppercase tracking-wide">{originCountry} Embassy</p>
          <a
            href={`tel:${dest.embassy_phone.split(',')[0].trim()}`}
            className="text-sm font-semibold text-[#38BDF8] hover:text-[#7DD3FC] transition-colors block"
          >
            {dest.embassy_phone}
          </a>
          <p className="text-xs text-[#9CA3AF]">{dest.embassy_address}</p>
          <a
            href={dest.embassy_website}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[#38BDF8] hover:text-[#7DD3FC] flex items-center gap-1 transition-colors"
          >
            Embassy Website <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        {/* Hospitals */}
        {dest.hospital_recommendations.length > 0 && (
          <div>
            <p className="text-xs text-[#6B7280] uppercase tracking-wide mb-2">Recommended Hospitals</p>
            <div className="space-y-2">
              {dest.hospital_recommendations.map((h, hi) => (
                <div
                  key={hi}
                  className="p-3 rounded-lg bg-[#1F2937]/40 border border-[rgba(148,163,184,0.08)]"
                >
                  <p className="text-xs font-semibold text-white">{h.name}</p>
                  <p className="text-sm text-[#6B7280] mt-0.5">{h.address}</p>
                  <a
                    href={`tel:${h.phone}`}
                    className="text-sm text-[#38BDF8] hover:text-[#7DD3FC] transition-colors mt-0.5 block"
                  >
                    {h.phone}
                  </a>
                  {h.notes && (
                    <p className="text-xs text-[#4B5563] mt-1 italic">{h.notes}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Travel advisory */}
        {dest.travel_advisory_level && (
          <div className="p-2.5 rounded-lg bg-[#22C55E]/8 border border-[#22C55E]/20 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#22C55E] flex-shrink-0" />
            <div>
              <span className="text-xs font-medium text-[#22C55E]">{dest.travel_advisory_level}</span>
              <span className="text-xs text-[#6B7280] ml-1.5">— {dest.travel_advisory_source}</span>
            </div>
          </div>
        )}

      </DestinationAccordion>
    ))}
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Main Modal
// ─────────────────────────────────────────────────────────────────────────────

export const DocumentationModal = ({
  isOpen,
  onClose,
  tripId,
  tripTitle,
  destinations,
}: DocumentationModalProps) => {
  const [activeTab,    setActiveTab]    = useState<TabId>('documents');
  const [data,         setData]         = useState<DocumentationResponse | null>(null);
  const [loading,      setLoading]      = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error,        setError]        = useState<string | null>(null);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Load or generate on open
  useEffect(() => {
    if (!isOpen) return;
    setActiveTab('documents');
    setError(null);
    setIsFullscreen(false);
    loadDocumentation();
  }, [isOpen, tripId]);

  const loadDocumentation = async () => {
    setLoading(true);
    setError(null);
    try {
      // Try fetching existing first
      const existing = await documentationApi.get(tripId);
      setData(existing);
    } catch (err: any) {
      if (err.response?.status === 404) {
        // Not generated yet — auto-generate
        try {
          const generated = await documentationApi.generate(tripId);
          setData(generated);
        } catch (genErr: any) {
          setError('Failed to generate documentation. Please try again.');
        }
      } else {
        setError('Failed to load documentation. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    setError(null);
    try {
      const updated = await documentationApi.regenerate(tripId);
      setData(updated);
      setCheckedItems({}); // reset checklist on regenerate
    } catch (err: any) {
      setError('Regeneration failed. Please try again.');
    } finally {
      setRegenerating(false);
    }
  };

  const toggleChecked = (key: string) => {
    setCheckedItems(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const formatGeneratedAt = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1)  return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24)   return `${diffH}h ago`;
    return d.toLocaleDateString();
  };

  if (!isOpen) return null;

  return (
    <div className={`fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in ${isFullscreen ? 'p-0' : 'p-4'}`}>
      <div className={`relative w-full bg-[#0a0e14]/95 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] shadow-2xl animate-scale-in flex flex-col transition-all duration-300 ${
  isFullscreen
    ? 'max-w-full h-screen max-h-screen rounded-none'
    : 'max-w-4xl max-h-[90vh] rounded-2xl'
}`}>

        {/* ── Header ── */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(148,163,184,0.1)] flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#F59E0B]/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-[#F59E0B]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Legal & Travel Documents</h2>
              <p className="text-xs text-[#9CA3AF] truncate max-w-[340px]">
                {destinations.join(', ')}
                {data?.generated_at && (
                  <span className="ml-2 text-[#6B7280]">· Generated {formatGeneratedAt(data.generated_at)}</span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
          <button
            onClick={() => setIsFullscreen(f => !f)}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
            {isFullscreen
                ? <Minimize2 className="w-5 h-5 text-gray-400" />
                : <Maximize2 className="w-5 h-5 text-gray-400" />}
            </button>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>
        </div>
        {/* ── Disclaimer — always visible ── */}
        <div className="mx-6 mt-4 flex-shrink-0 flex items-start gap-2.5 p-3 rounded-xl bg-[#F59E0B]/8 border border-[#F59E0B]/25">
          <AlertTriangle className="w-4 h-4 text-[#F59E0B] flex-shrink-0 mt-0.5" />
          <p className="text-sm text-[#D97706] leading-relaxed">
            <span className="font-semibold">Disclaimer:</span> This information is AI-generated and may not reflect the latest regulations.
            Always verify visa requirements, entry rules, and legal advisories with official government sources before travel.
          </p>
        </div>

        {/* ── Tab Bar ── */}
        {!loading && data && (
          <div className="flex gap-1 mx-6 mt-4 p-1 bg-[#1F2937]/50 rounded-xl flex-shrink-0">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-[#38BDF8] text-[#0a0e14] shadow-sm'
                    : 'text-[#9CA3AF] hover:text-white hover:bg-white/5'
                }`}
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>
        )}

        {/* ── Scrollable Content ── */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-4 min-h-0">

          {/* Loading */}
          {loading && <DocumentationSkeleton />}

          {/* Error */}
          {!loading && error && (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <div className="w-12 h-12 rounded-full bg-[#EF4444]/10 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-[#EF4444]" />
              </div>
              <p className="text-sm text-[#EF4444] text-center">{error}</p>
              <button
                onClick={loadDocumentation}
                className="px-4 py-2 bg-[#38BDF8] hover:bg-[#0EA5E9] text-[#0a0e14] font-semibold text-sm rounded-lg transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Content */}
          {!loading && !error && data && (
            <>
              {activeTab === 'documents' && (
                <DocumentsTab
                  data={data.document_checklist}
                  checkedItems={checkedItems}
                  onToggle={toggleChecked}
                />
              )}
              {activeTab === 'entry' && (
                <EntryTab data={data.entry_requirements} />
              )}
              {activeTab === 'legal' && (
                <LegalTab data={data.legal_advisories} />
              )}
              {activeTab === 'emergency' && (
                <EmergencyTab data={data.emergency_contacts} originCountry={data.origin_country} />
              )}
            </>
          )}
        </div>

        {/* ── Footer — Regenerate ── */}
        {!loading && data && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-[rgba(148,163,184,0.1)] flex-shrink-0">
            <p className="text-sm text-[#4B5563]">
              Powered by Gemini + Google Search grounding
            </p>
            <button
              onClick={handleRegenerate}
              disabled={regenerating}
              className="flex items-center gap-2 px-4 py-2 bg-[#1F2937]/80 hover:bg-[#1F2937] border border-[rgba(148,163,184,0.2)] hover:border-[#38BDF8]/40 text-white disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium rounded-lg transition-all"
            >
              {regenerating
                ? <Loader2 className="w-4 h-4 animate-spin text-[#38BDF8]" />
                : <RefreshCw className="w-4 h-4 text-[#38BDF8]" />}
              {regenerating ? 'Regenerating…' : 'Regenerate'}
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

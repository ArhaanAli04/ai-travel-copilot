import { useState, useEffect, type JSX } from 'react';
import { X, Share2, Mail, Copy, Check, Trash2, ChevronDown, Users, Clock, UserCheck } from 'lucide-react';
import { collaboratorApi } from '../services/api';
import type { Collaborator, CollaboratorRole } from '../types/collaborator';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  tripId: number;
  tripTitle: string;
  isOwner?: boolean;
}

const ROLE_LABELS: Record<CollaboratorRole, { label: string; description: string; color: string }> = {
  editor: {
    label: 'Editor',
    description: 'Can view and edit itinerary',
    color: 'text-[#38BDF8] bg-[#38BDF8]/10',
  },
  viewer: {
    label: 'Viewer',
    description: 'Can view itinerary only',
    color: 'text-[#9CA3AF] bg-[#9CA3AF]/10',
  },
};

const STATUS_ICON: Record<string, JSX.Element> = {
  pending:  <Clock className="w-3.5 h-3.5 text-[#F59E0B]" />,
  accepted: <UserCheck className="w-3.5 h-3.5 text-[#22C55E]" />,
  declined: <X className="w-3.5 h-3.5 text-[#EF4444]" />,
};

export const ShareModal = ({ isOpen, onClose, tripId, tripTitle, isOwner = false }: ShareModalProps) => {
  const [email, setEmail]                     = useState('');
  const [role, setRole]                       = useState<CollaboratorRole>('viewer');
  const [collaborators, setCollaborators]     = useState<Collaborator[]>([]);
  const [loading, setLoading]                 = useState(false);
  const [listLoading, setListLoading]         = useState(false);
  const [inviteLoading, setInviteLoading]     = useState(false);
  const [error, setError]                     = useState<string | null>(null);
  const [successMsg, setSuccessMsg]           = useState<string | null>(null);
  const [copied, setCopied]                   = useState(false);
  const [roleDropdown, setRoleDropdown]       = useState<number | null>(null); // collabId with open dropdown

  useEffect(() => {
    if (isOpen) {
      fetchCollaborators();
      setError(null);
      setSuccessMsg(null);
      setEmail('');
    }
  }, [isOpen, tripId]);

  const fetchCollaborators = async () => {
    setListLoading(true);
    try {
      const data = await collaboratorApi.getCollaborators(tripId);
      setCollaborators(data.collaborators);
    } catch (err: any) {
      console.error('Failed to load collaborators:', err);
    } finally {
      setListLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!email.trim()) return;
    setInviteLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await collaboratorApi.inviteCollaborator(tripId, email.trim(), role);
      setSuccessMsg(`Invite sent to ${email.trim()} ✅`);
      setEmail('');
      await fetchCollaborators();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Failed to send invite');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleRemove = async (collabId: number, collabEmail: string) => {
    if (!confirm(`Remove ${collabEmail} from this trip?`)) return;
    setLoading(true);
    try {
      await collaboratorApi.removeCollaborator(tripId, collabId);
      setCollaborators(prev => prev.filter(c => c.id !== collabId));
    } catch (err: any) {
      setError('Failed to remove collaborator');
    } finally {
      setLoading(false);
    }
  };

  const handleChangeRole = async (collabId: number, newRole: CollaboratorRole) => {
    setRoleDropdown(null);
    try {
      const updated = await collaboratorApi.changeRole(tripId, collabId, newRole);
      setCollaborators(prev => prev.map(c => c.id === collabId ? updated : c));
    } catch (err: any) {
      setError('Failed to change role');
    }
  };

  const handleCopyLink = async (token: string) => {
    const url = `${window.location.origin}/invites/${token}/accept`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-[#0a0e14]/95 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl animate-scale-in">

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#38BDF8]/10 flex items-center justify-center">
              <Share2 className="w-5 h-5 text-[#38BDF8]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Share Trip</h2>
              <p className="text-xs text-[#9CA3AF] truncate max-w-[260px]">{tripTitle}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Invite Form */}
        {isOwner && (
        <div className="p-6 border-b border-[rgba(148,163,184,0.1)]">
          <label className="block text-sm font-medium text-[#9CA3AF] mb-3">
            Invite by email
          </label>
          <div className="flex gap-2">
            {/* Email input */}
            <div className="flex-1 relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleInvite()}
                placeholder="friend@example.com"
                className="w-full pl-9 pr-3 py-2.5 bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-[#6B7280] text-sm focus:outline-none focus:border-[#38BDF8]/50 transition-colors"
              />
            </div>

            {/* Role selector */}
            <select
              value={role}
              onChange={e => setRole(e.target.value as CollaboratorRole)}
              className="px-3 py-2.5 bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] rounded-lg text-white text-sm focus:outline-none focus:border-[#38BDF8]/50 transition-colors cursor-pointer"
            >
              <option value="viewer">Viewer</option>
              <option value="editor">Editor</option>
            </select>

            {/* Send button */}
            <button
              onClick={handleInvite}
              disabled={inviteLoading || !email.trim()}
              className="px-4 py-2.5 bg-[#38BDF8] hover:bg-[#0EA5E9] disabled:opacity-50 disabled:cursor-not-allowed text-[#0a0e14] font-semibold text-sm rounded-lg transition-colors flex items-center gap-2 whitespace-nowrap"
            >
              {inviteLoading ? (
                <div className="w-4 h-4 border-2 border-[#0a0e14]/30 border-t-[#0a0e14] rounded-full animate-spin" />
              ) : (
                'Send Invite'
              )}
            </button>
          </div>

          {/* Role description */}
          <p className="text-xs text-[#6B7280] mt-2">
            {role === 'editor'
              ? '✏️ Editors can view and modify the itinerary'
              : '👁️ Viewers can only view the itinerary'}
          </p>

          {/* Feedback messages */}
          {error && (
            <p className="mt-2 text-sm text-[#EF4444] bg-[#EF4444]/10 rounded-lg px-3 py-2">{error}</p>
          )}
          {successMsg && (
            <p className="mt-2 text-sm text-[#22C55E] bg-[#22C55E]/10 rounded-lg px-3 py-2">{successMsg}</p>
          )}
        </div>
        )}

        {/* Collaborator List */}
        <div className="p-6 max-h-64 overflow-y-auto custom-scrollbar">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-4 h-4 text-[#9CA3AF]" />
            <h3 className="text-sm font-semibold text-[#9CA3AF] uppercase tracking-wide">
              People with access
            </h3>
            {collaborators.length > 0 && (
              <span className="ml-auto text-xs text-[#6B7280]">{collaborators.length} invited</span>
            )}
          </div>

          {listLoading ? (
            <div className="flex justify-center py-6">
              <div className="w-6 h-6 border-2 border-[#38BDF8]/30 border-t-[#38BDF8] rounded-full animate-spin" />
            </div>
          ) : collaborators.length === 0 ? (
            <div className="text-center py-6">
              <Users className="w-10 h-10 text-[#374151] mx-auto mb-2" />
              <p className="text-sm text-[#6B7280]">No collaborators yet</p>
              <p className="text-xs text-[#4B5563] mt-1">Invite someone above to share this trip</p>
            </div>
          ) : (
            <div className="space-y-2">
              {collaborators.map(collab => (
                <div
                  key={collab.id}
                  className="flex items-center gap-3 p-3 rounded-xl bg-[#1F2937]/30 border border-[rgba(148,163,184,0.08)] group"
                >
                  {/* Avatar */}
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#38BDF8]/20 to-[#F97316]/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-white uppercase">
                      {collab.email[0]}
                    </span>
                  </div>

                  {/* Email + status */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{collab.email}</p>
                    <div className="flex items-center gap-1 mt-0.5">
                      {STATUS_ICON[collab.status]}
                      <span className="text-xs text-[#6B7280] capitalize">{collab.status}</span>
                    </div>
                  </div>

                  {/* Role dropdown */}
                  {isOwner && (
                  <div className="relative">
                    <button
                      onClick={() => setRoleDropdown(roleDropdown === collab.id ? null : collab.id)}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${ROLE_LABELS[collab.role].color} hover:opacity-80`}
                    >
                      {ROLE_LABELS[collab.role].label}
                      <ChevronDown className="w-3 h-3" />
                    </button>
                    {roleDropdown === collab.id && (
                      <div className="absolute right-0 top-8 z-10 w-36 bg-[#1F2937] border border-[rgba(148,163,184,0.2)] rounded-xl shadow-xl overflow-hidden">
                        {(['viewer', 'editor'] as CollaboratorRole[]).map(r => (
                          <button
                            key={r}
                            onClick={() => handleChangeRole(collab.id, r)}
                            className={`w-full text-left px-3 py-2.5 text-xs transition-colors hover:bg-white/5 ${
                              collab.role === r ? 'text-[#38BDF8] font-semibold' : 'text-white'
                            }`}
                          >
                            <div className="font-medium capitalize">{r}</div>
                            <div className="text-[#6B7280] text-[10px]">{ROLE_LABELS[r].description}</div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  )}

                  {/* Copy link */}
                  {isOwner && (
                  <button
                    onClick={() => handleCopyLink(collab.invite_token)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg bg-[#38BDF8]/10 hover:bg-[#38BDF8]/20"
                    title="Copy invite link"
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5 text-[#22C55E]" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 text-[#38BDF8]" />
                    )}
                  </button>
                  )}

                  {/* Remove */}
                  {isOwner && (
                  <button
                    onClick={() => handleRemove(collab.id, collab.email)}
                    disabled={loading}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg bg-[#EF4444]/10 hover:bg-[#EF4444]/20 disabled:opacity-30"
                    title="Remove collaborator"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-[#EF4444]" />
                  </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

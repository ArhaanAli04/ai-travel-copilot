import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@clerk/react';
import { Plane, MapPin, Calendar, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { collaboratorApi } from '../services/api';
import type { InvitePreviewResponse } from '../types/collaborator';

type PageState = 'loading' | 'preview' | 'accepting' | 'success' | 'error';

const AcceptInvitePage = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { isSignedIn, isLoaded } = useAuth();

  const [pageState, setPageState]   = useState<PageState>('loading');
  const [preview, setPreview]       = useState<InvitePreviewResponse | null>(null);
  const [errorMsg, setErrorMsg]     = useState<string>('');

  // Fetch preview on mount
  useEffect(() => {
    if (!token) return;
    fetchPreview();
  }, [token]);

  // Auto-accept once signed in and preview is loaded
  useEffect(() => {
    if (isLoaded && isSignedIn && preview && preview.status === 'pending') {
      handleAccept();
    }
  }, [isLoaded, isSignedIn, preview]);

  const fetchPreview = async () => {
    setPageState('loading');
    try {
      const data = await collaboratorApi.getInvitePreview(token!);
      setPreview(data);
      setPageState('preview');
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Invalid or expired invite link';
      setErrorMsg(detail);
      setPageState('error');
    }
  };

  const handleAccept = async () => {
    if (!token) return;
    setPageState('accepting');
    try {
      await collaboratorApi.acceptInvite(token);
      setPageState('success');
      // Redirect to planner with the trip selected after 2s
      setTimeout(() => {
        navigate('/planner', { state: { selectTripId: preview?.trip_id } });
      }, 2000);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to accept invite';
      setErrorMsg(detail);
      setPageState('error');
    }
  };

  // ── Loading ──────────────────────────────────────────────────────
  if (pageState === 'loading' || !isLoaded) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-[#38BDF8] animate-spin mx-auto mb-4" />
          <p className="text-[#9CA3AF]">Loading invite...</p>
        </div>
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────
  if (pageState === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[#0a0e14]/95 border border-[rgba(148,163,184,0.2)] rounded-2xl p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-[#EF4444]/10 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-[#EF4444]" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Invite Not Found</h2>
          <p className="text-[#9CA3AF] mb-6">{errorMsg}</p>
          <button
            onClick={() => navigate('/planner')}
            className="px-6 py-2.5 bg-[#38BDF8] hover:bg-[#0EA5E9] text-[#0a0e14] font-semibold rounded-lg transition-colors"
          >
            Go to Planner
          </button>
        </div>
      </div>
    );
  }

  // ── Success ──────────────────────────────────────────────────────
  if (pageState === 'success') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[#0a0e14]/95 border border-[#22C55E]/30 rounded-2xl p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-[#22C55E]/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-[#22C55E]" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">You're In! 🎉</h2>
          <p className="text-[#9CA3AF] mb-2">
            You now have <span className="text-[#38BDF8] font-semibold capitalize">{preview?.role}</span> access to
          </p>
          <p className="text-white font-semibold text-lg mb-6">"{preview?.trip_title}"</p>
          <div className="flex items-center justify-center gap-2 text-[#6B7280] text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Redirecting to your trip...
          </div>
        </div>
      </div>
    );
  }

  // ── Accepting (spinner while API call runs) ──────────────────────
  if (pageState === 'accepting') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-[#38BDF8] animate-spin mx-auto mb-4" />
          <p className="text-[#9CA3AF]">Joining trip...</p>
        </div>
      </div>
    );
  }

  // ── Preview (main state) ─────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120] flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-4">

        {/* Header */}
        <div className="text-center mb-6">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Plane className="w-6 h-6 text-[#38BDF8]" />
            <span className="text-xl font-bold text-white">AI Travel Copilot</span>
          </div>
          <p className="text-[#9CA3AF] text-sm">
            <span className="text-white font-medium">{preview?.invited_by_name}</span> invited you to collaborate
          </p>
        </div>

        {/* Trip Preview Card */}
        <div className="bg-[#0a0e14]/95 border border-[rgba(148,163,184,0.2)] rounded-2xl p-6">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#38BDF8]/20 to-[#F97316]/20 flex items-center justify-center flex-shrink-0">
              <Plane className="w-6 h-6 text-[#38BDF8]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-bold text-white truncate">{preview?.trip_title}</h2>
              <span className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                preview?.role === 'editor'
                  ? 'bg-[#38BDF8]/10 text-[#38BDF8]'
                  : 'bg-[#9CA3AF]/10 text-[#9CA3AF]'
              }`}>
                {preview?.role === 'editor' ? '✏️ Editor' : '👁️ Viewer'} access
              </span>
            </div>
          </div>

          <div className="space-y-2 text-sm text-[#9CA3AF]">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#38BDF8] flex-shrink-0" />
              <span>{preview?.destinations.join(' → ')}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-[#38BDF8] flex-shrink-0" />
              <span>
                {preview && new Date(preview.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                {' → '}
                {preview && new Date(preview.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#38BDF8] flex-shrink-0" />
              <span>From {preview?.trip_origin}</span>
            </div>
          </div>
        </div>

        {/* CTA */}
        {!isSignedIn ? (
          <div className="space-y-3">
            <button
                onClick={() => navigate('/sign-in', { state: { returnTo: `/invites/${token}/accept` } })}
                className="w-full py-3 bg-[#38BDF8] hover:bg-[#0EA5E9] text-[#0a0e14] font-bold rounded-xl transition-colors"
                >
                Sign in to Accept Invite
                </button>
                <button
                onClick={() => navigate('/sign-up', { state: { returnTo: `/invites/${token}/accept` } })}
                className="w-full py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-colors border border-[rgba(148,163,184,0.2)]"
                >
                Create account & join
                </button>
          </div>
        ) : (
          <button
            onClick={handleAccept}
            className="w-full py-3 bg-gradient-to-r from-[#38BDF8] to-[#F97316] hover:opacity-90 text-white font-bold rounded-xl transition-opacity"
          >
            Accept & Join Trip
          </button>
        )}

      </div>
    </div>
  );
};

export default AcceptInvitePage;

import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import DisruptionForm from '../components/DisruptionForm';
import AlertBanner from '../components/AlertBanner';
import FlightStatusCard from '../components/FlightStatusCard';
import WeatherAlertCard from '../components/WeatherAlertCard';
import RightsSummaryCard from '../components/RightsSummaryCard';
import { disruptionApi } from '../services/api';
import type { DisruptionCase } from '../types/disruption';
import AlternativeFlightsGrid from '../components/AlternativeFlightsGrid';
import OptionsGrid from '../components/OptionsGrid';
import DraftMessageCard from '../components/DraftMessageCard';
import ChatWidget from '../components/ChatWidget';
import { Navigation } from '../components/Navigation';
import UnifiedSidebar from '../components/UnifiedSidebar';
import { MessageSquare, X } from 'lucide-react';

const CHAT_WIDTH = 400; // px — fixed chat panel width

const DisruptionPage: React.FC = () => {
  const [showDashboard, setShowDashboard] = useState(false);
  const [disruptionData, setDisruptionData] = useState<DisruptionCase | null>(null);
  const [loading, setLoading] = useState(false);
  const [chatExpanded, setChatExpanded] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const loadCase = async (caseId: number) => {
    setLoading(true);
    try {
      const data = await disruptionApi.getCase(caseId);
      setDisruptionData(data);
      setShowDashboard(true);
    } catch (error) {
      console.error('Failed to load case:', error);
      navigate('/disruptions', { replace: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) loadCase(Number(id));
  }, [id]);

  useEffect(() => {
    const state = location.state as { selectCaseId?: number; newCase?: boolean } | null;
    if (state?.selectCaseId) {
      navigate(`/disruptions/${state.selectCaseId}`, { replace: true, state: {} });
    } else if (state?.newCase) {
      setShowDashboard(false);
      setDisruptionData(null);
      navigate('/disruptions', { replace: true, state: {} });
    }
  }, [location.state]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <UnifiedSidebar currentCaseId={disruptionData?.id} />

      <div className="ml-20 transition-all duration-300">
        <Navigation />

        <div className="max-w-7xl mx-auto px-6 py-8">
          {loading ? (
            <div className="min-h-[80vh] flex items-center justify-center">
              <div className="text-center space-y-3">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto" />
                <p className="text-gray-400 text-sm">Loading disruption case...</p>
              </div>
            </div>
          ) : !showDashboard ? (
            <div className="min-h-[80vh] flex items-center justify-center py-12">
              <DisruptionForm
                onSuccess={(caseId) => navigate(`/disruptions/${caseId}`)}
              />
            </div>
          ) : (
            <div className="space-y-6">
              {disruptionData && (
                <AlertBanner
                  disruptionCase={disruptionData}
                  onDismiss={() => navigate('/disruptions')}
                />
              )}

              {/* Main content + chat panel side by side */}
              <div className="flex gap-6 transition-all duration-300" style={{ minHeight: 'calc(100vh - 200px)' }}>

                {/* ===== CARDS AREA ===== */}
                <div className="flex-1 min-w-0 transition-all duration-300">
                  {chatExpanded ? (
                    // EXPANDED: single column, all cards stacked
                    <div className="space-y-4">
                      {disruptionData && (
                        <>
                          <FlightStatusCard
                            disruptionCase={disruptionData}
                            onRefresh={() => loadCase(disruptionData.id)}
                            expanded={true} 
                          />
                          <WeatherAlertCard disruptionCase={disruptionData} />
                          <RightsSummaryCard disruptionCase={disruptionData} />
                          <AlternativeFlightsGrid disruptionCase={disruptionData} />
                          <OptionsGrid disruptionCase={disruptionData} />
                          <DraftMessageCard disruptionCase={disruptionData} />
                        </>
                      )}
                    </div>
                  ) : (
                    // DEFAULT: original 3+9 two-column grid
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                      <div className="lg:col-span-3 space-y-4">
                        {disruptionData && (
                          <>
                            <FlightStatusCard
                              disruptionCase={disruptionData}
                              onRefresh={() => loadCase(disruptionData.id)}
                            />
                            <WeatherAlertCard disruptionCase={disruptionData} />
                            <RightsSummaryCard disruptionCase={disruptionData} />
                          </>
                        )}
                      </div>
                      <div className="lg:col-span-9 space-y-4">
                        {disruptionData && (
                          <>
                            <AlternativeFlightsGrid disruptionCase={disruptionData} />
                            <OptionsGrid disruptionCase={disruptionData} />
                            <DraftMessageCard disruptionCase={disruptionData} />
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* ===== CHAT PANEL (DevTools-style) ===== */}
                <div
                  className="flex-shrink-0 transition-all duration-300 ease-in-out"
                  style={{
                    width: chatExpanded ? `${CHAT_WIDTH}px` : '0px',
                    overflow: chatExpanded ? 'visible' : 'hidden',
                    opacity: chatExpanded ? 1 : 0,
                  }}
                >
                  {disruptionData && (
                    <div
                      className="sticky top-6 flex flex-col"
                      style={{
                        width: `${CHAT_WIDTH}px`,
                        height: 'calc(100vh - 3rem)',
                      }}
                    >
                      {/* Panel header with collapse button */}
                      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 bg-[rgba(26,29,36,0.8)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-t-xl border-b-0">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-lg bg-[#8B5CF6] flex items-center justify-center text-xs text-white">✦</div>
                          <span className="text-white text-sm font-semibold">AI Assistant</span>
                          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        </div>
                        <button
                          onClick={() => setChatExpanded(false)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[rgba(148,163,184,0.1)] transition-all"
                          title="Close chat panel"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Chat widget — fills remaining height */}
                      <div className="flex-1 min-h-0">
                        <ChatWidget
                          disruptionCase={disruptionData}
                          hideHeader // we render our own header above
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ===== FLOATING CHAT TOGGLE BUTTON ===== */}
      {showDashboard && disruptionData && !chatExpanded && (
        <button
          onClick={() => setChatExpanded(true)}
          className="fixed bottom-8 right-8 z-50 flex items-center gap-2.5 px-5 py-3 rounded-2xl text-white font-semibold text-sm shadow-2xl transition-all hover:scale-105 active:scale-95"
          style={{
            background: 'linear-gradient(135deg, #8B5CF6, #3B82F6)',
            boxShadow: '0 0 30px rgba(139,92,246,0.4), 0 8px 32px rgba(0,0,0,0.3)',
          }}
        >
          <MessageSquare className="w-4 h-4" />
          AI Assistant
          {/* Unread dot — shows if there are messages */}
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        </button>
      )}
    </div>
  );
};

export default DisruptionPage;

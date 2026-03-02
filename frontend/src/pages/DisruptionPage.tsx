import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';  // ✅ add useParams
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

const DisruptionPage: React.FC = () => {
  const [showDashboard, setShowDashboard] = useState(false);
  const [disruptionData, setDisruptionData] = useState<DisruptionCase | null>(null);
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();  // ✅ read :id from URL

  const loadCase = async (caseId: number) => {
    setLoading(true);
    try {
      const data = await disruptionApi.getCase(caseId);
      setDisruptionData(data);
      setShowDashboard(true);
    } catch (error) {
      console.error('Failed to load case:', error);
      navigate('/disruptions', { replace: true });  // fallback to form on error
    } finally {
      setLoading(false);
    }
  };

  // ✅ On mount: restore from URL param (handles hard refresh)
  useEffect(() => {
    if (id) {
      loadCase(Number(id));
    }
  }, [id]);

  // ✅ Handle navigation state from sidebar (selectCaseId / newCase)
  useEffect(() => {
    const state = location.state as { selectCaseId?: number; newCase?: boolean } | null;
    if (state?.selectCaseId) {
      navigate(`/disruptions/${state.selectCaseId}`, { replace: true, state: {} });  // ✅ push to URL
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
            // ✅ Show spinner during case load (prevents flash of form on refresh)
            <div className="min-h-[80vh] flex items-center justify-center">
              <div className="text-center space-y-3">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto" />
                <p className="text-gray-400 text-sm">Loading disruption case...</p>
              </div>
            </div>
          ) : !showDashboard ? (
            <div className="min-h-[80vh] flex items-center justify-center py-12">
              <DisruptionForm
                onSuccess={(caseId) => {
                  navigate(`/disruptions/${caseId}`);  // ✅ push to URL on form submit
                }}
              />
            </div>
          ) : (
            <div className="space-y-6">
              {disruptionData && (
                <AlertBanner
                  disruptionCase={disruptionData}
                  onDismiss={() => navigate('/disruptions')}  // ✅ go to clean form URL
                />
              )}

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

                <div className="lg:col-span-6 space-y-4">
                  {disruptionData && (
                    <>
                      <AlternativeFlightsGrid disruptionCase={disruptionData} />
                      <OptionsGrid disruptionCase={disruptionData} />
                      <DraftMessageCard disruptionCase={disruptionData} />
                    </>
                  )}
                </div>

                <div className="lg:col-span-3">
                  {disruptionData && (
                    <ChatWidget disruptionCase={disruptionData} />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DisruptionPage;

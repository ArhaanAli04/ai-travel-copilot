import React, { useState,useEffect } from 'react';
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
import UnifiedSidebar from '../components/UnifiedSidebar'; // ✅ ADD
import { useLocation, useNavigate } from 'react-router-dom';

const DisruptionPage: React.FC = () => {
  const [showDashboard, setShowDashboard] = useState(false);
  const [caseId, setCaseId] = useState<number | null>(null);
  const [disruptionData, setDisruptionData] = useState<DisruptionCase | null>(null);
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const state = location.state as { selectCaseId?: number;newCase?: boolean  } | null;
    if (state?.selectCaseId) {
      loadCase(state.selectCaseId);
      setShowDashboard(true);
      // Clear state so back-navigation doesn't reload the same case
      navigate('/disruptions', { replace: true, state: {} });
    }else if (state?.newCase) {
    // Reset to form view
    setShowDashboard(false);
    setDisruptionData(null);
    navigate('/disruptions', { replace: true, state: {} });
  }
  }, [location.state]);

  const loadCase = async (id: number) => {
    setLoading(true);
    try {
      const data = await disruptionApi.getCase(id);
      setDisruptionData(data);
    } catch (error) {
      console.error('Failed to load case:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">

      {/* ✅ Unified Sidebar — same as Planner, no props needed on Disruption page */}
      <UnifiedSidebar currentCaseId={disruptionData?.id}/>

      {/* ✅ ml-20 shifts content right to clear the sidebar rail */}
      <div className="ml-20 transition-all duration-300">

        <Navigation />

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          {!showDashboard ? (
            <div className="min-h-[80vh] flex items-center justify-center py-12">
              <DisruptionForm
                onSuccess={(caseId) => {
                  setCaseId(caseId);
                  loadCase(caseId);
                  setShowDashboard(true);
                }}
              />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Alert Banner */}
              {disruptionData && (
                <AlertBanner
                  disruptionCase={disruptionData}
                  onDismiss={() => setShowDashboard(false)}
                />
              )}

              {/* 3-Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                {/* Left Sidebar - Status Panel */}
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

                {/* Center - Action Cards */}
                <div className="lg:col-span-6 space-y-4">
                  {disruptionData && (
                    <>
                      <AlternativeFlightsGrid disruptionCase={disruptionData} />
                      <OptionsGrid disruptionCase={disruptionData} />
                      <DraftMessageCard disruptionCase={disruptionData} />
                    </>
                  )}
                </div>

                {/* Right Sidebar - Chat Widget */}
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

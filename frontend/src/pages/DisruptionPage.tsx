import React, { useState,useEffect } from 'react';
import DisruptionForm from '../components/DisruptionForm'; // 
import AlertBanner from '../components/AlertBanner';
import FlightStatusCard from '../components/FlightStatusCard';
import WeatherAlertCard from '../components/WeatherAlertCard';
import RightsSummaryCard from '../components/RightsSummaryCard';
import { disruptionApi } from '../services/api'; // ✅ 
import type { DisruptionCase } from '../types/disruption'; // 
import AlternativeFlightsGrid from '../components/AlternativeFlightsGrid';
import OptionsGrid from '../components/OptionsGrid';
import DraftMessageCard from '../components/DraftMessageCard';
import ChatWidget from '../components/ChatWidget';

const DisruptionPage: React.FC = () => {
  const [showDashboard, setShowDashboard] = useState(false);
  const [caseId, setCaseId] = useState<number | null>(null);
  const [disruptionData, setDisruptionData] = useState<DisruptionCase | null>(null);
  const [loading, setLoading] = useState(false);

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
      {/* Navigation Bar */}
      <nav className="bg-[rgba(26,29,36,0.8)] backdrop-blur-xl border-b border-[rgba(148,163,184,0.2)] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="text-2xl">🌍</a>
            <h1 className="text-xl font-bold text-white">AI Travel Copilot</h1>
            <span className="text-sm text-gray-400">| Disruption Assistant</span>
          </div>
          <div className="flex gap-4">
            <a href="/planner" className="text-gray-400 hover:text-white transition-colors">
              Planner
            </a>
            <a href="/disruption" className="text-white border-b-2 border-orange-500">
              Disruptions
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {!showDashboard ? (
          // Landing View - Flight Input Form (we'll build this next)
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
          // Dashboard View - 3-Column Layout
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
            {/* Left Sidebar - Status Panel (30%) */}
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

            {/* Center - Action Cards (50%) */}
            <div className="lg:col-span-6 space-y-4">
                

                {disruptionData && (
                    <>
                        <AlternativeFlightsGrid disruptionCase={disruptionData} />
                        <OptionsGrid disruptionCase={disruptionData} />
                        <DraftMessageCard disruptionCase={disruptionData} />
                    </>
                    )}

                
            </div>

            {/* Right Sidebar - Chat Widget (20%) */}
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
        );
        };

export default DisruptionPage;

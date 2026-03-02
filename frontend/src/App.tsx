import { BrowserRouter , Routes, Route,Navigate } from 'react-router-dom';
import Planner from './pages/Planner';
import DisruptionPage from './pages/DisruptionPage'; 
import LocalDiscovery from './pages/LocalDiscovery';
import { ErrorBoundary } from './components/ErrorBoundary'; // ✨ NEW
import { NetworkStatus } from './components/NetworkStatus';
// Placeholder components (keep for future)
const Home = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center px-8">
      <h1 className="text-5xl font-bold text-white mb-4">🌍 AI Travel Copilot</h1>
      <p className="text-xl text-[#9CA3AF] mb-6">
        Your intelligent travel companion powered by AI
      </p>
      <a 
        href="/planner" 
        className="inline-block px-6 py-3 bg-gradient-to-r from-[#F97316] to-[#38BDF8] text-white rounded-xl font-semibold hover:scale-105 transition-transform"
      >
        Get Started →
      </a>
    </div>
  </div>
);




const Safety = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center px-8">
      <h2 className="text-4xl font-bold text-white mb-4">🛡️ Safety & Scam Awareness</h2>
      <p className="text-lg text-[#9CA3AF] mb-2">Stay safe with real-time advisories and scam alerts</p>
      <p className="text-[#6B7280]">Coming soon in Day 21...</p>
    </div>
  </div>
);

function App() {
  return (
    <ErrorBoundary> {/* ✨ NEW: Global error boundary */}
      <BrowserRouter>
        <NetworkStatus /> {/* ✨ NEW: Global network status */}
        <Routes>
          <Route path="/" element={<Navigate to="/planner" replace />} />
          <Route path="/planner" element={<Planner />} />
          <Route path="/disruptions" element={<DisruptionPage />} />
          <Route path="/disruptions/:id" element={<DisruptionPage />} />
          <Route path="/local-discovery" element={<LocalDiscovery />} />
          <Route path="/local-discovery/:sessionId" element={<LocalDiscovery />} />
          <Route path="/safety" element={<Safety />} /> {/* ✅ ADDED */}
          <Route path="*" element={<Navigate to="/planner" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;

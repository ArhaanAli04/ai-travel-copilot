import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Planner from './pages/Planner';

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

const Disruption = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center px-8">
      <h2 className="text-4xl font-bold text-white mb-4">🚨 Disruption Copilot</h2>
      <p className="text-lg text-[#9CA3AF] mb-2">Handle flight delays, cancellations, and rerouting</p>
      <p className="text-[#6B7280]">Coming soon in Day 11...</p>
    </div>
  </div>
);

const Local = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center px-8">
      <h2 className="text-4xl font-bold text-white mb-4">📍 Local Discovery</h2>
      <p className="text-lg text-[#9CA3AF] mb-2">Find hyper-local experiences and hidden gems</p>
      <p className="text-[#6B7280]">Coming soon in Day 16...</p>
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
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/planner" element={<Planner />} />
        <Route path="/disruption" element={<Disruption />} />
        <Route path="/local" element={<Local />} />
        <Route path="/safety" element={<Safety />} />
      </Routes>
    </Router>
  );
}

export default App;

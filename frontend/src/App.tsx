import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';

// Placeholder components (we'll build these properly later)
const Home = () => (
  <div style={{ textAlign: 'center', padding: '3rem' }}>
    <h1>🌍 AI Travel Copilot</h1>
    <p style={{ fontSize: '1.2rem', color: '#666' }}>
      Your intelligent travel companion powered by AI
    </p>
    <p>Select a module from the navigation above to get started.</p>
  </div>
);

const Planner = () => (
  <div>
    <h2>✈️ Trip Planner</h2>
    <p>AI-powered itinerary generation and re-planning</p>
    <p style={{ color: '#999' }}>Coming soon in Day 3...</p>
  </div>
);

const Disruption = () => (
  <div>
    <h2>🚨 Disruption Copilot</h2>
    <p>Handle flight delays, cancellations, and rerouting</p>
    <p style={{ color: '#999' }}>Coming soon in Day 11...</p>
  </div>
);

const Local = () => (
  <div>
    <h2>📍 Local Discovery</h2>
    <p>Find hyper-local experiences and hidden gems</p>
    <p style={{ color: '#999' }}>Coming soon in Day 16...</p>
  </div>
);

const Safety = () => (
  <div>
    <h2>🛡️ Safety & Scam Awareness</h2>
    <p>Stay safe with real-time advisories and scam alerts</p>
    <p style={{ color: '#999' }}>Coming soon in Day 21...</p>
  </div>
);

function App() {
  return (
    <Router>
      <div className="app" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <nav style={{ 
          padding: '1rem 2rem', 
          background: '#1a1a1a', 
          color: 'white',
          display: 'flex',
          gap: '2rem',
          alignItems: 'center'
        }}>
          <Link to="/" style={{ 
            color: 'white', 
            textDecoration: 'none', 
            fontWeight: 'bold',
            fontSize: '1.2rem'
          }}>
            AI Travel Copilot
          </Link>
          <div style={{ display: 'flex', gap: '1.5rem', marginLeft: 'auto' }}>
            <Link to="/planner" style={{ color: 'white', textDecoration: 'none' }}>Planner</Link>
            <Link to="/disruption" style={{ color: 'white', textDecoration: 'none' }}>Disruption</Link>
            <Link to="/local" style={{ color: 'white', textDecoration: 'none' }}>Local</Link>
            <Link to="/safety" style={{ color: 'white', textDecoration: 'none' }}>Safety</Link>
          </div>
        </nav>
        
        <main style={{ padding: '2rem', flex: 1 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/planner" element={<Planner />} />
            <Route path="/disruption" element={<Disruption />} />
            <Route path="/local" element={<Local />} />
            <Route path="/safety" element={<Safety />} />
          </Routes>
        </main>
        
        <footer style={{ 
          padding: '1rem', 
          textAlign: 'center', 
          background: '#f5f5f5',
          color: '#666',
          fontSize: '0.9rem'
        }}>
          AI Travel Copilot v0.1.0 | Day 2 Complete ✅
        </footer>
      </div>
    </Router>
  );
}

export default App;

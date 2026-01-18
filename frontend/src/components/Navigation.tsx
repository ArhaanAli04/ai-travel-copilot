import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Plane } from 'lucide-react';

const navItems = [
  { name: "Planner", path: "/planner" },
  { name: "Disruption", path: "/disruption" },
  { name: "Local", path: "/local" },
  { name: "Safety", path: "/safety" },
];

export function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Check if current path matches nav item
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className={`sticky top-0 z-50 transition-all duration-300 ${scrolled ? "glass-nav shadow-lg" : "glass-nav"}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div 
            className="flex items-center gap-3 cursor-pointer" 
            onClick={() => navigate('/')}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#38BDF8] to-[#3B82F6] flex items-center justify-center">
              <Plane className="w-5 h-5 text-white" />
            </div>
            <span className="text-white font-semibold text-lg">AI Travel Copilot</span>
          </div>

          {/* Center Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.name}
                onClick={() => navigate(item.path)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive(item.path)
                    ? "text-[#38BDF8] bg-[#38BDF8]/10 shadow-[0_0_20px_rgba(56,189,248,0.3)]"
                    : "text-[#9CA3AF] hover:text-white hover:bg-white/5"
                }`}
              >
                {item.name}
              </button>
            ))}
          </div>

          {/* User Avatar */}
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#38BDF8] to-[#3B82F6] flex items-center justify-center text-white text-sm font-semibold">
            TC
          </div>
        </div>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </nav>
  );
}

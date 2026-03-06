import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Plane, LogOut, ChevronDown } from 'lucide-react';
import { useAuth, useUser } from '@clerk/react';

const navItems = [
  { name: "Planner", path: "/planner" },
  { name: "Disruption", path: "/disruptions" },
  { name: "Local Discovery", path: "/local-discovery" },
  { name: "Safety", path: "/safety" },
];

export function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { signOut } = useAuth();
  const { user } = useUser();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isActive = (path: string) => location.pathname.startsWith(path);

  const handleSignOut = async () => {
    await signOut();
    navigate('/sign-in');
  };

  // Get initials from name or email
  const getInitials = () => {
    if (user?.fullName) {
      return user.fullName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }
    if (user?.primaryEmailAddress?.emailAddress) {
      return user.primaryEmailAddress.emailAddress[0].toUpperCase();
    }
    return 'U';
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
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                  isActive(item.path)
                    ? "text-[#38BDF8] bg-[#38BDF8]/10 shadow-[0_0_20px_rgba(56,189,248,0.3)]"
                    : "text-[#9CA3AF] hover:text-white hover:bg-white/5"
                }`}
              >
                {item.name}
              </button>
            ))}
          </div>

          {/* User Avatar + Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(prev => !prev)}
              className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-full hover:bg-white/5 transition-all cursor-pointer"
            >
              {/* Avatar: photo if available, else initials */}
              {user?.imageUrl ? (
                <img
                  src={user.imageUrl}
                  alt="avatar"
                  className="w-8 h-8 rounded-full object-cover ring-2 ring-[#38BDF8]/40"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#38BDF8] to-[#3B82F6] flex items-center justify-center text-white text-sm font-semibold">
                  {getInitials()}
                </div>
              )}
              <ChevronDown className={`w-3.5 h-3.5 text-[#9CA3AF] transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 glass-card rounded-2xl border border-[rgba(148,163,184,0.2)] shadow-xl animate-fade-in overflow-hidden">
                {/* User info */}
                <div className="px-4 py-3 border-b border-[rgba(148,163,184,0.1)]">
                  <p className="text-white text-sm font-semibold truncate">
                    {user?.fullName || 'Traveler'}
                  </p>
                  <p className="text-[#6B7280] text-xs truncate">
                    {user?.primaryEmailAddress?.emailAddress || ''}
                  </p>
                </div>

                {/* Sign out */}
                <button
                  onClick={handleSignOut}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-[#9CA3AF] hover:text-white hover:bg-white/5 transition-all cursor-pointer"
                >
                  <LogOut className="w-4 h-4 text-[#EF4444]" />
                  <span>Sign out</span>
                </button>
              </div>
            )}
          </div>

        </div>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </nav>
  );
}

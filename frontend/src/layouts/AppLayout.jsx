import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  UtensilsCrossed,
  BarChart3,
  MessageSquare,
  Compass,
  Target,
  User,
  LogOut,
  Menu,
  X,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Meals', to: '/meals', icon: UtensilsCrossed },
    { name: 'Nutrition', to: '/nutrition', icon: BarChart3 },
    { name: 'AI Assistant', to: '/assistant', icon: MessageSquare },
    { name: 'Recommendations', to: '/recommendations', icon: Compass },
    { name: 'Goals', to: '/goals', icon: Target },
    { name: 'Profile', to: '/profile', icon: User },
  ];

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white border-r border-slate-200/90 z-30">
        {/* Brand */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-base font-bold tracking-tight text-slate-900 leading-none">Nutrino</div>
            <div className="text-[10px] font-semibold text-emerald-700 tracking-wider uppercase mt-1">Health-Tech OS</div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-800 font-semibold shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Profile & Logout */}
        <div className="p-3 border-t border-slate-100">
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50/80 border border-slate-200/60">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center justify-center shrink-0">
                {getInitials(user?.name)}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-900 truncate">{user?.name || 'User'}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email || ''}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile Top Header */}
      <div className="lg:hidden fixed top-0 inset-x-0 h-16 bg-white border-b border-slate-200/90 px-4 flex items-center justify-between z-40">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center text-white">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <span className="text-base font-bold text-slate-900">Nutrino</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Slide-over Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white shadow-xl">
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center text-white">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <span className="text-base font-bold text-slate-900">Nutrino</span>
              </div>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md"
                aria-label="Close menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3.5 py-3 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-emerald-50 text-emerald-800 font-semibold'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                      }`
                    }
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>

            <div className="p-4 border-t border-slate-100">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200/60 mb-2">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center justify-center shrink-0">
                    {getInitials(user?.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-900 truncate">{user?.name || 'User'}</p>
                    <p className="text-[11px] text-slate-500 truncate">{user?.email || ''}</p>
                  </div>
                </div>
              </div>
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  handleLogout();
                }}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 lg:pl-64 flex flex-col min-w-0 pt-16 lg:pt-0">
        <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

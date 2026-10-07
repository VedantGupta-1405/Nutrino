import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function PublicLayout() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight text-slate-900 leading-none">Nutrino</span>
              <span className="text-[10px] font-semibold text-emerald-700 tracking-wider uppercase mt-0.5">Precision Health</span>
            </div>
          </Link>

          <nav className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="text-xs font-semibold px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-sm"
              >
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-xs font-semibold px-3.5 py-2 text-slate-600 hover:text-slate-900 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="text-xs font-semibold px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-sm"
                >
                  Get Started
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Main Outlet */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Public Footer */}
      <footer className="bg-white border-t border-slate-200/80 py-8 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          <p className="font-medium text-slate-600">Nutrino Precision Health-Tech Platform</p>
          <p className="mt-1 text-slate-400">Deterministic nutrition aggregation, grounded AI guidance, and personalized recommendations.</p>
        </div>
      </footer>
    </div>
  );
}

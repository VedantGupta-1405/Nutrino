import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { Button } from '../components/common/Button';

export function NotFoundPage() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mx-auto mb-4 border border-slate-200">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">404 — Page Not Found</h1>
        <p className="mt-2 text-xs sm:text-sm text-slate-500">
          The requested screen or resource does not exist in Nutrino.
        </p>
        <div className="mt-6">
          <Link to="/dashboard">
            <Button variant="primary" size="md" icon={ArrowLeft}>
              Return to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

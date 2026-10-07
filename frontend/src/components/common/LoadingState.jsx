import React from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingState({
  message = 'Loading data...',
  description = 'Please wait while we fetch the latest nutrition records.',
  type = 'spinner', // 'spinner' | 'skeleton'
  className = '',
}) {
  if (type === 'skeleton') {
    return (
      <div className={`space-y-4 animate-pulse ${className}`}>
        <div className="h-6 bg-slate-200 rounded w-1/4"></div>
        <div className="h-24 bg-slate-100 rounded-xl"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-20 bg-slate-100 rounded-xl"></div>
          <div className="h-20 bg-slate-100 rounded-xl"></div>
          <div className="h-20 bg-slate-100 rounded-xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center justify-center py-16 px-4 text-center ${className}`}>
      <div className="p-3 bg-emerald-50 text-emerald-600 rounded-full mb-3.5">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
      <h4 className="text-sm font-semibold text-slate-800">{message}</h4>
      {description && <p className="text-xs text-slate-500 mt-1 max-w-sm">{description}</p>}
    </div>
  );
}

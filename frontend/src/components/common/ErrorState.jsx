import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export function ErrorState({
  title = 'Failed to load data',
  message = 'An unexpected error occurred while communicating with the server.',
  onRetry = null,
  className = '',
}) {
  return (
    <div className={`p-6 rounded-xl border border-rose-200/80 bg-rose-50/40 text-center flex flex-col items-center justify-center ${className}`}>
      <div className="p-2.5 bg-rose-100 text-rose-600 rounded-full mb-3">
        <AlertCircle className="w-5 h-5" />
      </div>
      <h4 className="text-sm font-semibold text-rose-900">{title}</h4>
      <p className="text-xs text-rose-700 mt-1 max-w-md leading-relaxed">{message}</p>
      {onRetry && (
        <div className="mt-4">
          <Button variant="outline" size="sm" onClick={onRetry} icon={RefreshCw}>
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
}

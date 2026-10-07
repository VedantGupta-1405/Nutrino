import React from 'react';
import { Inbox } from 'lucide-react';

export function EmptyState({
  icon: Icon = Inbox,
  title = 'No records found',
  description = 'There is currently no data to display for this view.',
  action = null,
  className = '',
}) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 text-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 ${className}`}>
      <div className="p-3 bg-white border border-slate-200/80 text-slate-400 rounded-full shadow-sm mb-3.5">
        <Icon className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
      <p className="text-xs text-slate-500 mt-1 max-w-sm leading-relaxed">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

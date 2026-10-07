import React from 'react';

export function PageHeader({
  title,
  description,
  badge = null,
  action = null,
  className = '',
}) {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200/80 mb-6 ${className}`}>
      <div>
        <div className="flex items-center gap-2.5">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          {badge}
        </div>
        {description && <p className="mt-1 text-sm text-slate-500 max-w-2xl">{description}</p>}
      </div>
      {action && <div className="flex items-center gap-3 shrink-0">{action}</div>}
    </div>
  );
}

import React from 'react';

export function SectionHeader({
  title,
  description,
  action = null,
  className = '',
}) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      <div>
        <h2 className="text-base font-semibold text-slate-900 tracking-tight">{title}</h2>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

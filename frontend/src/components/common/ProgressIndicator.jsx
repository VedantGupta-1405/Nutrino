import React from 'react';

export function ProgressIndicator({
  value = 0,
  max = 100,
  label,
  sublabel,
  color = 'emerald',
  size = 'md',
  showValues = true,
  unit = '',
  className = '',
}) {
  const numValue = Number(value) || 0;
  const numMax = Number(max) || 0;
  const percentage = numMax > 0 ? Math.min(Math.round((numValue / numMax) * 100), 100) : 0;
  const isOver = numMax > 0 && numValue > numMax;

  const colorStyles = {
    emerald: 'bg-emerald-600',
    blue: 'bg-sky-600',
    amber: 'bg-amber-500',
    rose: 'bg-rose-500',
    purple: 'bg-indigo-600',
  };

  const barHeight = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className={`w-full ${className}`}>
      {(label || showValues) && (
        <div className="flex items-center justify-between mb-1.5 text-xs">
          <div>
            {label && <span className="font-semibold text-slate-800">{label}</span>}
            {sublabel && <span className="text-slate-500 ml-1.5">({sublabel})</span>}
          </div>
          {showValues && (
            <div className="text-right">
              <span className="font-bold text-slate-900">{Math.round(numValue)}</span>
              {numMax > 0 && (
                <span className="text-slate-500 font-normal"> / {Math.round(numMax)} {unit}</span>
              )}
              {numMax > 0 && (
                <span className={`ml-2 font-medium ${isOver ? 'text-amber-600' : 'text-slate-500'}`}>
                  {percentage}%
                </span>
              )}
            </div>
          )}
        </div>
      )}
      <div className={`w-full bg-slate-100 rounded-full overflow-hidden ${barHeight[size] || barHeight.md}`}>
        <div
          className={`${colorStyles[color] || colorStyles.emerald} transition-all duration-500 rounded-full h-full`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
          role="progressbar"
          aria-valuenow={numValue}
          aria-valuemin="0"
          aria-valuemax={numMax}
        />
      </div>
    </div>
  );
}

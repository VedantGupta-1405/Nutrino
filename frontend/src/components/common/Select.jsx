import React, { forwardRef } from 'react';

export const Select = forwardRef(function Select(
  {
    label,
    error,
    helperText,
    options = [],
    id,
    className = '',
    disabled = false,
    required = false,
    ...props
  },
  ref
) {
  const generatedId = React.useId();
  const selectId = id || props.name || generatedId;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <select
        ref={ref}
        id={selectId}
        disabled={disabled}
        required={required}
        className={`w-full rounded-lg border bg-white text-slate-900 text-sm px-3.5 py-2 transition-colors
          focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600
          disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed
          ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500/20' : 'border-slate-200 hover:border-slate-300'}
          ${className}`}
        {...props}
      >
        {options.map((opt) => {
          const val = typeof opt === 'object' ? opt.value : opt;
          const lbl = typeof opt === 'object' ? opt.label : opt;
          return (
            <option key={val} value={val}>
              {lbl}
            </option>
          );
        })}
      </select>
      {error && <p className="mt-1 text-xs text-red-600 font-medium">{error}</p>}
      {!error && helperText && <p className="mt-1 text-xs text-slate-500">{helperText}</p>}
    </div>
  );
});

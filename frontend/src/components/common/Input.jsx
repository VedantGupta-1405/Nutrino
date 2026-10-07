import React, { forwardRef } from 'react';

export const Input = forwardRef(function Input(
  {
    label,
    error,
    helperText,
    icon: Icon = null,
    id,
    type = 'text',
    className = '',
    disabled = false,
    required = false,
    ...props
  },
  ref
) {
  const generatedId = React.useId();
  const inputId = id || props.name || generatedId;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <input
          ref={ref}
          id={inputId}
          type={type}
          disabled={disabled}
          required={required}
          className={`w-full rounded-lg border bg-white text-slate-900 placeholder:text-slate-400 text-sm transition-colors
            focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600
            disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed
            ${Icon ? 'pl-9 pr-3' : 'px-3.5'} py-2
            ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500/20' : 'border-slate-200 hover:border-slate-300'}
            ${className}`}
          {...props}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-600 font-medium">{error}</p>}
      {!error && helperText && <p className="mt-1 text-xs text-slate-500">{helperText}</p>}
    </div>
  );
});

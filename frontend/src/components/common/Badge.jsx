import React from 'react';

export function Badge({
  children,
  variant = 'neutral',
  size = 'md',
  icon: Icon = null,
  className = '',
  ...props
}) {
  const variantStyles = {
    neutral: 'bg-slate-100 text-slate-700 border border-slate-200/80',
    brand: 'bg-emerald-50 text-emerald-800 border border-emerald-200',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    warning: 'bg-amber-50 text-amber-800 border border-amber-200',
    error: 'bg-rose-50 text-rose-700 border border-rose-200',
    info: 'bg-sky-50 text-sky-700 border border-sky-200',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-0.5 gap-1.5',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${variantStyles[variant] || variantStyles.neutral} ${sizeStyles[size] || sizeStyles.md} ${className}`}
      {...props}
    >
      {Icon && <Icon className="w-3 h-3 shrink-0" />}
      <span>{children}</span>
    </span>
  );
}

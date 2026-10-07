import React from 'react';

export function Card({
  children,
  className = '',
  hover = false,
  padding = 'default',
  ...props
}) {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    default: 'p-5 sm:p-6',
    lg: 'p-6 sm:p-8',
  };

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200/90 shadow-card ${
        hover ? 'transition-all duration-200 hover:shadow-card-hover hover:border-slate-300' : ''
      } ${paddingStyles[padding] || paddingStyles.default} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '', ...props }) {
  return (
    <div className={`mb-4 flex flex-col gap-1 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '', ...props }) {
  return (
    <h3 className={`text-base font-semibold text-slate-900 tracking-tight ${className}`} {...props}>
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = '', ...props }) {
  return (
    <p className={`text-xs text-slate-500 font-normal leading-relaxed ${className}`} {...props}>
      {children}
    </p>
  );
}

export function CardContent({ children, className = '', ...props }) {
  return (
    <div className={`${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = '', ...props }) {
  return (
    <div className={`mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 ${className}`} {...props}>
      {children}
    </div>
  );
}

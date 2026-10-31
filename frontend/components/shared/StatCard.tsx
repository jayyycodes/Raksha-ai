import React from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  accentColor?: string;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  icon,
  accentColor,
  className,
}) => {
  return (
    <div
      className={cn(
        'bg-card rounded-md border border-border p-4 shadow-sm flex flex-col justify-between transition-shadow hover:shadow',
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
          {label}
        </span>
        {icon && <div className="text-text-muted">{icon}</div>}
      </div>

      <div className="flex items-baseline gap-2">
        <span
          className="text-2xl font-serif font-bold text-text-primary tracking-tight"
          style={accentColor ? { color: accentColor } : undefined}
        >
          {value}
        </span>
        {subtext && <span className="text-xs text-text-muted">{subtext}</span>}
      </div>
    </div>
  );
};

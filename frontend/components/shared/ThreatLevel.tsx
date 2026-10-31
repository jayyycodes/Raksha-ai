import React from 'react';
import { ThreatCategory } from '@/lib/api/types';
import { cn } from '@/lib/utils';

interface ThreatLevelProps {
  level: ThreatCategory;
  num?: number;
  className?: string;
  showNumeric?: boolean;
}

const THREAT_CONFIG: Record<ThreatCategory, { label: string; textClass: string; bgClass: string; borderClass: string; icon: string }> = {
  low: {
    label: 'Low Threat',
    textClass: 'text-[#1E5734]',
    bgClass: 'bg-[#EBF7EE]',
    borderClass: 'border-[#C3E8CC]',
    icon: '🛡️',
  },
  medium: {
    label: 'Medium Threat',
    textClass: 'text-[#7D5213]',
    bgClass: 'bg-[#FEF7EC]',
    borderClass: 'border-[#F8E3BE]',
    icon: '⚠️',
  },
  high: {
    label: 'High Threat',
    textClass: 'text-[#8C1B13]',
    bgClass: 'bg-[#FEECEB]',
    borderClass: 'border-[#F8C8C5]',
    icon: '🚨',
  },
};

export const ThreatLevel: React.FC<ThreatLevelProps> = ({ level, num, className, showNumeric = true }) => {
  const config = THREAT_CONFIG[level] || THREAT_CONFIG.low;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold border',
        config.bgClass,
        config.textClass,
        config.borderClass,
        className
      )}
      title={`Threat Level: ${config.label}${num ? ` (${num}/10)` : ''}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{config.label}</span>
      {showNumeric && num !== undefined && (
        <span className="font-mono text-[11px] opacity-80 border-l border-current pl-1 ml-0.5">
          {num}/10
        </span>
      )}
    </span>
  );
};

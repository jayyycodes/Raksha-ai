import React from 'react';
import { SourceStatusType } from '@/lib/api/types';
import { cn } from '@/lib/utils';

interface StatusPillProps {
  status: SourceStatusType;
  className?: string;
}

const STATUS_CONFIG: Record<SourceStatusType, { label: string; textClass: string; bgClass: string; dotClass: string }> = {
  ok: {
    label: 'Operational',
    textClass: 'text-[#1E5734]',
    bgClass: 'bg-[#EBF7EE] border-[#C3E8CC]',
    dotClass: 'bg-[#2F7D4F]',
  },
  stale: {
    label: 'Stale (>4h)',
    textClass: 'text-[#7D5213]',
    bgClass: 'bg-[#FEF7EC] border-[#F8E3BE]',
    dotClass: 'bg-[#B7791F]',
  },
  failed: {
    label: 'Failing',
    textClass: 'text-[#8C1B13]',
    bgClass: 'bg-[#FEECEB] border-[#F8C8C5]',
    dotClass: 'bg-[#B42318]',
  },
  empty: {
    label: 'Empty',
    textClass: 'text-[#1E457F]',
    bgClass: 'bg-[#EDF4FC] border-[#CDE1F7]',
    dotClass: 'bg-[#2B5FAE]',
  },
};

export const StatusPill: React.FC<StatusPillProps> = ({ status, className }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.ok;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border',
        config.bgClass,
        config.textClass,
        className
      )}
    >
      <span className={cn('w-2 h-2 rounded-full shrink-0', config.dotClass)} aria-hidden="true" />
      <span>{config.label}</span>
    </span>
  );
};


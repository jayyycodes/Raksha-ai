import React from 'react';
import { RingId } from '@/lib/api/types';
import { cn } from '@/lib/utils';

interface RingMarkerProps {
  ring: RingId;
  showLabel?: boolean;
  className?: string;
}

const RING_CONFIG: Record<RingId, { label: string; badgeClass: string; dotClass: string; icon: string }> = {
  1: {
    label: 'Ring 1 · India',
    badgeClass: 'bg-[#FEF3EB] text-[#8C3A04] border-[#F8D8C3]',
    dotClass: 'bg-[#C2570C]',
    icon: '🇮🇳',
  },
  2: {
    label: 'Ring 2 · Adversaries',
    badgeClass: 'bg-[#FDF2F2] text-[#822020] border-[#F9D4D4]',
    dotClass: 'bg-[#9B2C2C]',
    icon: '⚔️',
  },
  3: {
    label: 'Ring 3 · Regional',
    badgeClass: 'bg-[#F4F2F9] text-[#483A70] border-[#DDD6ED]',
    dotClass: 'bg-[#5B4B8A]',
    icon: '🗺️',
  },
  4: {
    label: 'Ring 4 · Global',
    badgeClass: 'bg-[#EDF4FC] text-[#1E457F] border-[#CDE1F7]',
    dotClass: 'bg-[#2B5FAE]',
    icon: '🌐',
  },
};

export const RingMarker: React.FC<RingMarkerProps> = ({ ring, showLabel = true, className }) => {
  const config = RING_CONFIG[ring] || RING_CONFIG[1];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border tracking-wide',
        config.badgeClass,
        className
      )}
      title={config.label}
    >
      <span className={cn('w-2 h-2 rounded-full shrink-0', config.dotClass)} aria-hidden="true" />
      {showLabel ? config.label : `Ring ${ring}`}
    </span>
  );
};

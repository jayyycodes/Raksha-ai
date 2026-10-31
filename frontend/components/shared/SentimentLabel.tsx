import React from 'react';
import { SentimentType } from '@/lib/api/types';
import { cn } from '@/lib/utils';

interface SentimentLabelProps {
  sentiment: SentimentType;
  className?: string;
}

const SENTIMENT_CONFIG: Record<SentimentType, { label: string; textClass: string; bgClass: string; icon: string }> = {
  negative: {
    label: 'Critical / Alarming',
    textClass: 'text-[#8C1B13]',
    bgClass: 'bg-[#FEECEB] border-[#F8C8C5]',
    icon: '▼',
  },
  neutral: {
    label: 'Neutral',
    textClass: 'text-[#2D333F]',
    bgClass: 'bg-[#F0EEEA] border-[#DED9D0]',
    icon: '●',
  },
  positive: {
    label: 'Cooperative / De-escalating',
    textClass: 'text-[#1E5734]',
    bgClass: 'bg-[#EBF7EE] border-[#C3E8CC]',
    icon: '▲',
  },
};

export const SentimentLabel: React.FC<SentimentLabelProps> = ({ sentiment, className }) => {
  const config = SENTIMENT_CONFIG[sentiment] || SENTIMENT_CONFIG.neutral;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border',
        config.bgClass,
        config.textClass,
        className
      )}
      title={`Sentiment: ${config.label}`}
    >
      <span aria-hidden="true" className="text-[10px] font-bold">
        {config.icon}
      </span>
      <span>{config.label}</span>
    </span>
  );
};

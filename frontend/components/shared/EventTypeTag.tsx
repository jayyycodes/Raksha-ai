import React from 'react';
import { cn } from '@/lib/utils';

interface EventTypeTagProps {
  eventType: string;
  className?: string;
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  border_incident: 'Border Incident',
  military_movement: 'Military Movement',
  diplomatic: 'Diplomatic',
  aerial: 'Aerial Activity',
  naval: 'Naval Operation',
  cyber_attack: 'Cyber Security',
  terror_activity: 'Security Incident',
  nuclear: 'Strategic / Nuclear',
  disinformation: 'Information Warfare',
  general: 'General Defense',
};

export const EventTypeTag: React.FC<EventTypeTagProps> = ({ eventType, className }) => {
  const normalized = (eventType || 'general').toLowerCase();
  const label = EVENT_TYPE_LABELS[normalized] || normalized.replace(/_/g, ' ');

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#EFECE5] text-[#2D333F] border border-[#DDD8CC]',
        className
      )}
    >
      {label}
    </span>
  );
};

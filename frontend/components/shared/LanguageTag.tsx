import React from 'react';
import { cn } from '@/lib/utils';

interface LanguageTagProps {
  language: string;
  translated?: boolean;
  className?: string;
}

const LANG_MAP: Record<string, string> = {
  en: 'English',
  ur: 'Urdu',
  zh: 'Chinese',
  hi: 'Hindi',
  fa: 'Persian',
  ps: 'Pashto',
};

export const LanguageTag: React.FC<LanguageTagProps> = ({ language, translated, className }) => {
  const code = (language || 'en').toLowerCase();
  const label = LANG_MAP[code] || code.toUpperCase();

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs text-[#4A5365] bg-[#F7F5F0] border border-[#DDD8CC]',
        className
      )}
      title={`Language: ${label}${translated ? ' (Translated to English)' : ''}`}
    >
      <span className="font-semibold uppercase text-[10px] tracking-wider text-[#1A1F2B]">
        {code}
      </span>
      {translated && (
        <span className="text-[10px] text-[#2F7D4F] font-medium border-l border-[#DDD8CC] pl-1">
          Translated
        </span>
      )}
    </span>
  );
};

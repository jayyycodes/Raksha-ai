'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { formatISTTimeOnly } from '@/lib/utils';

interface TopBarProps {
  onToggleSidebar?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onToggleSidebar }) => {
  const pathname = usePathname();
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const update = () => setTimeStr(formatISTTimeOnly(new Date().toISOString()));
    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, []);

  const getPageTitle = () => {
    if (pathname.startsWith('/articles/')) return 'Article Detail & Intelligence Provenance';
    if (pathname.startsWith('/articles')) return 'Live Intelligence Feed';
    if (pathname.startsWith('/sources')) return 'Source Monitoring & Feed Health';
    return 'Analyst Workbench';
  };

  return (
    <header className="h-14 bg-card border-b border-border px-4 lg:px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="lg:hidden p-1.5 rounded border border-border text-text-secondary hover:bg-subtle-fill focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          aria-label="Toggle Navigation Sidebar"
        >
          ☰
        </button>
        <div>
          <h1 className="text-sm font-serif font-bold text-text-primary tracking-tight">
            {getPageTitle()}
          </h1>
          <p className="text-[10px] text-text-muted hidden sm:block">
            Open-Source Intelligence Landscape · India & Surrounding Rings
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Environment / Mode Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-subtle-fill text-text-secondary text-xs border border-border">
          <span className="w-1.5 h-1.5 rounded-full bg-status-green animate-pulse" />
          <span className="font-semibold text-[11px]">System Active</span>
          {timeStr && (
            <span className="text-text-muted border-l border-border pl-1.5 text-[11px]">
              {timeStr}
            </span>
          )}
        </div>
      </div>
    </header>
  );
};


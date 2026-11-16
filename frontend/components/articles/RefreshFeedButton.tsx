'use client';

import React, { useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { triggerSourcesRefresh } from '@/lib/api/client';

interface RefreshFeedButtonProps {
  className?: string;
  variant?: 'primary' | 'secondary' | 'compact';
  showTimestamp?: boolean;
}

export const RefreshFeedButton: React.FC<RefreshFeedButtonProps> = ({
  className = '',
  variant = 'secondary',
  showTimestamp = true,
}) => {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // 1. Trigger backend live multi-source scrape & ingestion cycle
      await triggerSourcesRefresh();

      // 2. Re-fetch Server Components data (stats + articles list)
      startTransition(() => {
        router.refresh();
      });

      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setLastRefreshed(timeStr);
    } catch (err) {
      console.error('Failed to refresh intelligence feed:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const loading = isRefreshing || isPending;

  return (
    <div className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={handleRefresh}
        disabled={loading}
        title="Poll all 40 monitored sources for fresh wires and update the intelligence stream"
        className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded transition-all shadow-sm ${
          loading
            ? 'bg-subtle-fill text-text-muted cursor-not-allowed border border-border'
            : variant === 'primary'
            ? 'bg-primary-navy hover:bg-primary-navy-dark text-white border border-transparent'
            : 'bg-card hover:bg-subtle-fill text-text-primary border border-border hover:border-text-secondary/40'
        } ${className}`}
      >
        <svg
          className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-status-amber' : 'text-primary-navy'}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        <span>{loading ? 'Fetching Wires...' : 'Refresh Feed'}</span>
      </button>

      {showTimestamp && lastRefreshed && (
        <span className="text-[10px] text-text-muted hidden sm:inline" title="Last checked">
          Updated {lastRefreshed}
        </span>
      )}
    </div>
  );
};

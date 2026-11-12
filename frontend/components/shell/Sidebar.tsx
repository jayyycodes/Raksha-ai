'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

interface SidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ className, onNavigate }) => {
  const pathname = usePathname();

  const isArticlesActive = pathname.startsWith('/articles');
  const isSourcesActive = pathname.startsWith('/sources');
  const isMapActive = pathname.startsWith('/map');
  const isGraphActive = pathname.startsWith('/graph');
  const isProfilesActive = pathname.startsWith('/profiles');
  const isEventsActive = pathname.startsWith('/events');
  const isThreatsActive = pathname.startsWith('/threats');
  const isWatchlistsActive = pathname.startsWith('/watchlists');
  const isReviewActive = pathname.startsWith('/review');
  const isSitrepActive = pathname.startsWith('/sitrep');

  return (
    <aside
      className={cn(
        'w-64 bg-card border-r border-border flex flex-col justify-between h-full select-none',
        className
      )}
    >
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-border flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-primary-navy text-accent-saffron flex items-center justify-center font-serif font-black text-lg tracking-tighter">
              R
            </div>
            <div>
              <span className="font-serif font-bold text-lg text-text-primary tracking-tight">
                RAKSHA AI
              </span>
              <span className="text-[10px] uppercase font-bold text-accent-saffron ml-1.5 px-1.5 py-0.5 rounded bg-accent-saffron-light border border-accent-saffron/20">
                STAGE 2
              </span>
            </div>
          </div>
          <p className="text-[11px] text-text-muted mt-1 leading-tight">
            OSINT Intelligence Analyst Workbench
          </p>
        </div>

        {/* Primary Navigation */}
        <div className="px-3 py-4">
          <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Intelligence Feeds
          </div>
          <nav className="space-y-1">
            <Link
              href="/articles"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isArticlesActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">📰</span>
              <span>Article Feed</span>
            </Link>

            <Link
              href="/sources"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isSourcesActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">📡</span>
              <span>Source Status</span>
            </Link>
          </nav>

          {/* Stage 2 Intelligence Modules */}
          <div className="mt-6 px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Intelligence Analysis
          </div>
          <nav className="space-y-1">
            <Link
              href="/map"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isMapActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">🗺️</span>
              <span>Incident Map</span>
            </Link>

            <Link
              href="/graph"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isGraphActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">🕸️</span>
              <span>Entity Graph</span>
            </Link>

            <Link
              href="/profiles"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isProfilesActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">👤</span>
              <span>Entity Profiles</span>
            </Link>

            <Link
              href="/events"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isEventsActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">⏳</span>
              <span>Event Timelines</span>
            </Link>

            <Link
              href="/threats"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isThreatsActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">📈</span>
              <span>Threats & Alerts</span>
            </Link>

            <Link
              href="/watchlists"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isWatchlistsActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">🔔</span>
              <span>Watchlists</span>
            </Link>

            <Link
              href="/review"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isReviewActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">⚖️</span>
              <span>Review Queue</span>
            </Link>

            <Link
              href="/sitrep"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isSitrepActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base">📑</span>
              <span>Situation Report</span>
            </Link>
          </nav>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-border bg-canvas/50 text-[11px] text-text-muted flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-text-secondary">Security Ring Model</span>
          <span className="text-[10px] text-accent-saffron font-bold">4 Rings</span>
        </div>
        <p className="text-[10px] leading-tight text-text-muted">
          All intelligence extracted strictly from public news & syndication feeds.
        </p>
      </div>
    </aside>
  );
};


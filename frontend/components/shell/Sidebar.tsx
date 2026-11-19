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
  const isAlertsActive = pathname.startsWith('/alerts');
  const isWatchlistsActive = pathname.startsWith('/watchlists');
  const isReviewActive = pathname.startsWith('/review');
  const isSitrepActive = pathname.startsWith('/sitrep');
  const isCasesActive = pathname.startsWith('/cases');
  const isUploadActive = pathname.startsWith('/upload');
  const isAuditActive = pathname.startsWith('/audit');

  return (
    <aside
      className={cn(
        'w-64 bg-card border-r border-border flex flex-col h-full select-none overflow-hidden',
        className
      )}
    >
      {/* Brand Header: Always fixed at top, never scrolls */}
      <div className="p-4 border-b border-border flex flex-col gap-1 shrink-0 bg-card">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-primary-navy text-accent-saffron flex items-center justify-center font-serif font-black text-lg tracking-tighter shadow-sm">
            R
          </div>
          <div>
            <span className="font-serif font-bold text-lg text-text-primary tracking-tight">
              RAKSHA AI
            </span>
            <span className="text-[10px] uppercase font-bold text-accent-saffron ml-1.5 px-1.5 py-0.5 rounded bg-accent-saffron-light border border-accent-saffron/20">
              STAGE 3
            </span>
          </div>
        </div>
        <p className="text-[11px] text-text-muted mt-1 leading-tight">
          OSINT Intelligence Analyst Workbench
        </p>
      </div>

      {/* Primary Navigation: Independently scrollable container */}
      <div className="flex-1 overflow-y-auto min-h-0 px-3 py-3 space-y-4">
        {/* Section 1: Feeds */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Intelligence Feeds
          </div>
          <nav className="space-y-0.5">
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
              <span className="text-base leading-none">📰</span>
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
              <span className="text-base leading-none">📡</span>
              <span>Source Status</span>
            </Link>
          </nav>
        </div>

        {/* Section 2: Stage 2 Intelligence Modules */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Intelligence Analysis
          </div>
          <nav className="space-y-0.5">
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
              <span className="text-base leading-none">🗺️</span>
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
              <span className="text-base leading-none">🕸️</span>
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
              <span className="text-base leading-none">👤</span>
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
              <span className="text-base leading-none">⏳</span>
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
              <span className="text-base leading-none">📈</span>
              <span>Threats & Scores</span>
            </Link>

            <Link
              href="/alerts"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isAlertsActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base leading-none">🚨</span>
              <span>Security Alerts</span>
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
              <span className="text-base leading-none">🔔</span>
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
              <span className="text-base leading-none">⚖️</span>
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
              <span className="text-base leading-none">📑</span>
              <span>Situation Report</span>
            </Link>

            <Link
              href="/cases"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isCasesActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base leading-none">💼</span>
              <span>Cases & Dossiers</span>
            </Link>

            <Link
              href="/upload"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isUploadActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base leading-none">📥</span>
              <span>Upload Custom Data</span>
            </Link>
          </nav>
        </div>

        {/* Section 3: Governance & Security */}
        <div className="pt-2 border-t border-border/60">
          <div className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Governance & Security
          </div>
          <nav className="space-y-0.5">
            <Link
              href="/audit"
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy',
                isAuditActive
                  ? 'bg-subtle-fill text-primary-navy font-bold border-l-2 border-primary-navy'
                  : 'text-text-secondary hover:bg-subtle-fill/60 hover:text-text-primary'
              )}
            >
              <span className="text-base leading-none">🛡️</span>
              <span>Audit & Lineage</span>
            </Link>
          </nav>
        </div>
      </div>

      {/* Footer Info: Fixed at bottom, never scrolls or clips */}
      <div className="p-3.5 border-t border-border bg-canvas/60 text-[11px] text-text-muted flex flex-col gap-1 shrink-0">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-text-secondary text-xs">Security Ring Model</span>
          <span className="text-[10px] text-accent-saffron font-bold px-1.5 py-0.5 rounded bg-accent-saffron-light border border-accent-saffron/30">
            4 Rings
          </span>
        </div>
        <p className="text-[10px] leading-tight text-text-muted mt-0.5">
          All intelligence extracted strictly from public news & syndication feeds.
        </p>
      </div>
    </aside>
  );
};


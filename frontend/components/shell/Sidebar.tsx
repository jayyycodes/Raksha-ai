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
                MVP
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

          {/* Coming Later in Mid / Solid Stage */}
          <div className="mt-8 px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Advanced Modules
          </div>
          <div className="space-y-1 opacity-70">
            <div
              className="flex items-center justify-between px-3 py-2 text-xs text-text-muted cursor-not-allowed rounded"
              title="Available in Stage 2 (Mid)"
            >
              <div className="flex items-center gap-3">
                <span className="text-base">🗺️</span>
                <span>Incident Map</span>
              </div>
              <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-subtle-fill border border-border text-text-muted">
                Mid
              </span>
            </div>

            <div
              className="flex items-center justify-between px-3 py-2 text-xs text-text-muted cursor-not-allowed rounded"
              title="Available in Stage 2 (Mid)"
            >
              <div className="flex items-center gap-3">
                <span className="text-base">🕸️</span>
                <span>Entity Graph</span>
              </div>
              <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-subtle-fill border border-border text-text-muted">
                Mid
              </span>
            </div>

            <div
              className="flex items-center justify-between px-3 py-2 text-xs text-text-muted cursor-not-allowed rounded"
              title="Available in Stage 2 (Mid)"
            >
              <div className="flex items-center gap-3">
                <span className="text-base">👤</span>
                <span>Entity Profiles</span>
              </div>
              <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-subtle-fill border border-border text-text-muted">
                Mid
              </span>
            </div>

            <div
              className="flex items-center justify-between px-3 py-2 text-xs text-text-muted cursor-not-allowed rounded"
              title="Available in Stage 2 (Mid)"
            >
              <div className="flex items-center gap-3">
                <span className="text-base">📑</span>
                <span>Situation Report</span>
              </div>
              <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-subtle-fill border border-border text-text-muted">
                Mid
              </span>
            </div>

            <div
              className="flex items-center justify-between px-3 py-2 text-xs text-text-muted cursor-not-allowed rounded"
              title="Available in Stage 2 (Mid)"
            >
              <div className="flex items-center gap-3">
                <span className="text-base">🔍</span>
                <span>Unified Search</span>
              </div>
              <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-subtle-fill border border-border text-text-muted">
                Mid
              </span>
            </div>
          </div>
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


'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { formatISTTimeOnly } from '@/lib/utils';
import { fetchUnifiedSearch } from '@/lib/api/client';
import { UnifiedSearchResponse } from '@/lib/api/types';

interface TopBarProps {
  onToggleSidebar?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onToggleSidebar }) => {
  const pathname = usePathname();
  const [timeStr, setTimeStr] = useState<string>('');
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<UnifiedSearchResponse | null>(null);
  const [searching, setSearching] = useState<boolean>(false);
  const [open, setOpen] = useState<boolean>(false);
  const searchBoxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const update = () => setTimeStr(formatISTTimeOnly(new Date().toISOString()));
    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults(null);
      setOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setSearching(true);
      const res = await fetchUnifiedSearch(trimmed);
      setResults(res);
      setSearching(false);
      setOpen(true);
    }, 260);

    return () => clearTimeout(timer);
  }, [query]);

  const getPageTitle = () => {
    if (pathname.startsWith('/articles/')) return 'Article Detail & Intelligence Provenance';
    if (pathname.startsWith('/articles')) return 'Live Intelligence Feed';
    if (pathname.startsWith('/sources')) return 'Source Monitoring & Feed Health';
    if (pathname.startsWith('/map')) return 'Geospatial Incident Map';
    if (pathname.startsWith('/graph')) return 'Entity Knowledge Graph';
    if (pathname.startsWith('/profiles')) return 'Entity Profiles & Object Views';
    if (pathname.startsWith('/events')) return 'Threaded Event Timelines';
    if (pathname.startsWith('/threats')) return 'Regional Threat Scoring & Alerts';
    if (pathname.startsWith('/watchlists')) return 'Intelligence Watchlists';
    if (pathname.startsWith('/review')) return 'Disambiguation Review Queue';
    if (pathname.startsWith('/sitrep')) return 'Daily Grounded SitRep';
    return 'Analyst Workbench';
  };

  return (
    <header className="h-14 bg-card border-b border-border px-4 lg:px-6 flex items-center justify-between gap-4 sticky top-0 z-30">
      <div className="flex items-center gap-3 shrink-0">
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
          <p className="text-[10px] text-text-muted hidden md:block">
            Open-Source Intelligence Landscape · India & Surrounding Rings
          </p>
        </div>
      </div>

      {/* Global Unified Search */}
      <div ref={searchBoxRef} className="relative flex-1 max-w-md hidden sm:block">
        <input
          type="text"
          placeholder="Search entities, events, or articles..."
          value={query}
          onFocus={() => {
            if (results) setOpen(true);
          }}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full text-xs bg-canvas border border-border rounded-md px-3 py-1.5 text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
        />
        {searching && (
          <span className="absolute right-3 top-2 text-[10px] text-text-muted">...</span>
        )}

        {open && results && (
          <div className="absolute left-0 right-0 mt-1.5 bg-card border border-border rounded-lg shadow-xl max-h-96 overflow-y-auto z-50 divide-y divide-border/60">
            <div className="px-3 py-2 bg-subtle-fill/60 flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-text-muted">
              <span>Unified Intelligence Search</span>
              <span>{results.total_matches} match(es)</span>
            </div>

            {results.entities.length > 0 && (
              <div className="p-2 space-y-1">
                <div className="px-1.5 text-[10px] font-bold uppercase text-primary-navy">
                  Entities ({results.entities.length})
                </div>
                {results.entities.map((ent) => (
                  <Link
                    key={`ent-${ent.id}`}
                    href={`/profiles/${ent.id}`}
                    onClick={() => setOpen(false)}
                    className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-subtle-fill text-xs transition-colors"
                  >
                    <span className="font-semibold text-text-primary">{ent.name}</span>
                    <span className="text-[10px] text-text-muted uppercase">
                      {ent.entity_type} · Ring {ent.primary_ring}
                    </span>
                  </Link>
                ))}
              </div>
            )}

            {results.events.length > 0 && (
              <div className="p-2 space-y-1">
                <div className="px-1.5 text-[10px] font-bold uppercase text-accent-saffron">
                  Threaded Events ({results.events.length})
                </div>
                {results.events.map((ev) => (
                  <Link
                    key={`ev-${ev.id}`}
                    href={`/events/${ev.id}`}
                    onClick={() => setOpen(false)}
                    className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-subtle-fill text-xs transition-colors"
                  >
                    <span className="font-semibold text-text-primary truncate mr-2">{ev.title}</span>
                    <span className="text-[10px] text-text-muted shrink-0">
                      {ev.article_count} articles
                    </span>
                  </Link>
                ))}
              </div>
            )}

            {results.articles.length > 0 && (
              <div className="p-2 space-y-1">
                <div className="px-1.5 text-[10px] font-bold uppercase text-status-green">
                  Wire Articles ({results.articles.length})
                </div>
                {results.articles.map((art) => (
                  <Link
                    key={`art-${art.id}`}
                    href={`/articles/${art.id}`}
                    onClick={() => setOpen(false)}
                    className="block px-2 py-1.5 rounded hover:bg-subtle-fill text-xs transition-colors"
                  >
                    <span className="font-medium text-text-primary block truncate">{art.title}</span>
                    <span className="text-[10px] text-text-muted">
                      {art.source_name} · Ring {art.ring}
                    </span>
                  </Link>
                ))}
              </div>
            )}

            {results.total_matches === 0 && (
              <div className="p-4 text-center text-xs text-text-muted">
                No matching entities, events, or articles for &ldquo;{results.query}&rdquo;.
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 shrink-0">
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

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';

export const ArticleFilters: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [q, setQ] = useState(searchParams.get('q') || '');

  // Keep search input in sync if URL changes
  useEffect(() => {
    setQ(searchParams.get('q') || '');
  }, [searchParams]);

  const updateParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (!value || value === 'all') {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    params.delete('page'); // Reset to page 1 on filter change
    router.push(`${pathname}?${params.toString()}`);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateParam('q', q.trim());
  };

  const clearAllFilters = () => {
    setQ('');
    router.push(pathname);
  };

  const hasActiveFilters = Boolean(
    searchParams.get('ring') ||
    searchParams.get('event_type') ||
    searchParams.get('language') ||
    searchParams.get('sort') ||
    searchParams.get('q')
  );

  return (
    <div className="bg-card rounded-md border border-border p-4 shadow-sm mb-6 flex flex-col gap-3">
      {/* Search Input Bar */}
      <form onSubmit={handleSearchSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search headlines or intelligence summaries..."
            className="w-full pl-9 pr-3 py-2 text-xs bg-canvas rounded border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary-navy"
          />
          <span className="absolute left-3 top-2.5 text-text-muted text-xs">🔍</span>
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-primary-navy hover:bg-primary-navy-dark text-white text-xs font-semibold rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
        >
          Search
        </button>
      </form>

      {/* Dropdown Filters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
        {/* Ring Filter */}
        <div>
          <label htmlFor="ring-select" className="block text-[10px] font-bold uppercase text-text-muted mb-1">
            Source Ring
          </label>
          <select
            id="ring-select"
            value={searchParams.get('ring') || 'all'}
            onChange={(e) => updateParam('ring', e.target.value)}
            className="w-full text-xs bg-canvas border border-border rounded px-2.5 py-1.5 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-navy"
          >
            <option value="all">All Rings</option>
            <option value="1">Ring 1 · India</option>
            <option value="2">Ring 2 · Adversaries</option>
            <option value="3">Ring 3 · Regional</option>
            <option value="4">Ring 4 · Global</option>
          </select>
        </div>

        {/* Event Type Filter */}
        <div>
          <label htmlFor="event-select" className="block text-[10px] font-bold uppercase text-text-muted mb-1">
            Event Classification
          </label>
          <select
            id="event-select"
            value={searchParams.get('event_type') || 'all'}
            onChange={(e) => updateParam('event_type', e.target.value)}
            className="w-full text-xs bg-canvas border border-border rounded px-2.5 py-1.5 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-navy"
          >
            <option value="all">All Classifications</option>
            <option value="border_incident">Border Incident</option>
            <option value="military_movement">Military Movement</option>
            <option value="aerial">Aerial Activity</option>
            <option value="naval">Naval Operations</option>
            <option value="diplomatic">Diplomatic</option>
            <option value="cyber_attack">Cyber Security</option>
            <option value="terror_activity">Security Incident</option>
            <option value="disinformation">Information Warfare</option>
            <option value="general">General</option>
          </select>
        </div>

        {/* Language Filter */}
        <div>
          <label htmlFor="lang-select" className="block text-[10px] font-bold uppercase text-text-muted mb-1">
            Source Language
          </label>
          <select
            id="lang-select"
            value={searchParams.get('language') || 'all'}
            onChange={(e) => updateParam('language', e.target.value)}
            className="w-full text-xs bg-canvas border border-border rounded px-2.5 py-1.5 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-navy"
          >
            <option value="all">All Languages</option>
            <option value="en">English (EN)</option>
            <option value="ur">Urdu (UR)</option>
            <option value="zh">Chinese (ZH)</option>
            <option value="hi">Hindi (HI)</option>
          </select>
        </div>

        {/* Sort Filter */}
        <div>
          <label htmlFor="sort-select" className="block text-[10px] font-bold uppercase text-text-muted mb-1">
            Sort Order
          </label>
          <select
            id="sort-select"
            value={searchParams.get('sort') || 'newest'}
            onChange={(e) => updateParam('sort', e.target.value)}
            className="w-full text-xs bg-canvas border border-border rounded px-2.5 py-1.5 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-navy"
          >
            <option value="newest">Newest First</option>
            <option value="threat">Highest Threat Level</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>
      </div>

      {/* Active Filter Clear Bar */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-2 border-t border-border/60 text-xs text-text-muted">
          <span>Active filters applied</span>
          <button
            type="button"
            onClick={clearAllFilters}
            className="text-accent-saffron hover:underline font-semibold text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-saffron"
          >
            Clear all filters ✕
          </button>
        </div>
      )}
    </div>
  );
};


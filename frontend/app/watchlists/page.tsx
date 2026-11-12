'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  fetchWatchlists,
  createWatchlist,
  toggleWatchlist,
  deleteWatchlist,
} from '@/lib/api/client';
import { WatchlistItem } from '@/lib/api/types';
import { formatISTDate } from '@/lib/utils';

export default function WatchlistsPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [queryType, setQueryType] = useState<'entity' | 'region' | 'keyword'>('keyword');
  const [queryValue, setQueryValue] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    const res = await fetchWatchlists();
    setItems(res);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !queryValue.trim()) return;
    setSubmitting(true);
    const ok = await createWatchlist({
      name: name.trim(),
      query_type: queryType,
      query_value: queryValue.trim(),
    });
    if (ok) {
      setName('');
      setQueryValue('');
      await loadData();
    }
    setSubmitting(false);
  };

  const handleToggle = async (id: number, current: boolean) => {
    const ok = await toggleWatchlist(id, !current);
    if (ok) {
      setItems((prev) => prev.map((w) => (w.id === id ? { ...w, is_active: !current } : w)));
    }
  };

  const handleDelete = async (id: number) => {
    const ok = await deleteWatchlist(id);
    if (ok) {
      setItems((prev) => prev.filter((w) => w.id !== id));
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="font-serif font-bold text-2xl text-text-primary tracking-tight">
          Intelligence Watchlists
        </h1>
        <p className="text-xs text-text-muted mt-0.5">
          Track strategic entities, flashpoint regions, and priority defence keywords; triggers alerts automatically on new matches.
        </p>
      </div>

      {/* Create Watchlist Form */}
      <form
        onSubmit={handleCreate}
        className="bg-card border border-border rounded-lg p-5 shadow-sm grid grid-cols-1 md:grid-cols-4 gap-3 items-end"
      >
        <div>
          <label className="block text-[11px] font-semibold text-text-secondary mb-1">
            Watchlist Label
          </label>
          <input
            type="text"
            placeholder="e.g., S-400 Air Defence"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full text-xs bg-canvas border border-border rounded px-3 py-2 text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-text-secondary mb-1">
            Monitor Type
          </label>
          <select
            value={queryType}
            onChange={(e) => setQueryType(e.target.value as 'entity' | 'region' | 'keyword')}
            className="w-full text-xs bg-canvas border border-border rounded px-3 py-2 text-text-primary font-medium"
          >
            <option value="keyword">Keyword / Weapon System</option>
            <option value="entity">Named Entity / Group</option>
            <option value="region">Strategic Region / Sector</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-text-secondary mb-1">
            Match Term / Value
          </label>
          <input
            type="text"
            placeholder="e.g., Depsang, Rafale, LAC-Ladakh"
            value={queryValue}
            onChange={(e) => setQueryValue(e.target.value)}
            required
            className="w-full text-xs bg-canvas border border-border rounded px-3 py-2 text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="text-xs font-semibold px-4 py-2 rounded bg-primary-navy text-white hover:bg-primary-navy-dark disabled:opacity-60 transition-colors"
        >
          {submitting ? 'Adding Watch...' : '+ Add Watchlist Trigger'}
        </button>
      </form>

      {/* Watchlists List */}
      {loading ? (
        <div className="p-10 text-center text-xs text-text-muted bg-card border border-border rounded-lg">
          Loading active watchlists...
        </div>
      ) : items.length > 0 ? (
        <div className="space-y-4">
          {items.map((wl) => (
            <div
              key={wl.id}
              className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        wl.is_active ? 'bg-status-green' : 'bg-text-muted'
                      }`}
                    />
                    <h3 className="font-serif font-bold text-base text-text-primary">
                      {wl.name}
                    </h3>
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary">
                      {wl.query_type}
                    </span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-primary-navy/10 text-primary-navy font-semibold">
                      &ldquo;{wl.query_value}&rdquo;
                    </span>
                  </div>
                  <p className="text-[11px] text-text-muted">
                    Alerts triggered: <strong className="text-text-primary">{wl.alert_count}</strong>
                    {wl.last_triggered_at && ` · Last hit ${formatISTDate(wl.last_triggered_at)}`}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleToggle(wl.id, wl.is_active)}
                    className="text-xs font-semibold px-3 py-1.5 rounded border border-border bg-subtle-fill hover:bg-border text-text-primary transition-colors"
                  >
                    {wl.is_active ? 'Pause' : 'Resume'}
                  </button>
                  <button
                    onClick={() => handleDelete(wl.id)}
                    className="text-xs font-semibold px-3 py-1.5 rounded border border-red-200 text-red-700 hover:bg-red-50 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>

              {wl.recent_matches && wl.recent_matches.length > 0 && (
                <div className="pt-3 border-t border-border/60 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                    Recent Matching Wires ({wl.recent_matches.length})
                  </span>
                  <div className="space-y-1">
                    {wl.recent_matches.map((m) => (
                      <Link
                        key={m.article_id}
                        href={`/articles/${m.article_id}`}
                        className="flex items-center justify-between gap-2 p-2 rounded bg-subtle-fill/40 hover:bg-subtle-fill text-xs transition-colors"
                      >
                        <span className="font-medium text-text-primary truncate">{m.title}</span>
                        <span className="text-[10px] text-text-muted shrink-0">
                          {m.source_name} · {formatISTDate(m.published_at)}
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="p-10 text-center text-xs text-text-muted bg-card border border-border rounded-lg">
          No active watchlists yet. Create a watch trigger above to monitor priority entities or sectors.
        </div>
      )}
    </div>
  );
}


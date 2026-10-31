'use client';

import React, { useState } from 'react';
import { SourceHealth, RingId, SourceStatusType } from '@/lib/api/types';
import { RingMarker } from '@/components/shared/RingMarker';
import { StatusPill } from '@/components/shared/StatusPill';
import { LanguageTag } from '@/components/shared/LanguageTag';
import { formatIST, formatRelativeTime } from '@/lib/utils';

export const SourceTable: React.FC<{ sources: SourceHealth[] }> = ({ sources }) => {
  const [ringFilter, setRingFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const toggleRow = (id: number) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const filtered = sources.filter((s) => {
    if (ringFilter !== 'all' && s.ring !== Number(ringFilter)) return false;
    if (statusFilter !== 'all' && s.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="flex flex-col gap-4">
      {/* Table Filters Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-card p-3 rounded-md border border-border">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div>
            <label htmlFor="source-ring-filter" className="text-[10px] font-bold uppercase text-text-muted mr-1.5">
              Ring:
            </label>
            <select
              id="source-ring-filter"
              value={ringFilter}
              onChange={(e) => setRingFilter(e.target.value)}
              className="text-xs bg-canvas border border-border rounded px-2 py-1 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-navy"
            >
              <option value="all">All Rings ({sources.length})</option>
              <option value="1">Ring 1 · India</option>
              <option value="2">Ring 2 · Adversaries</option>
              <option value="3">Ring 3 · Regional</option>
              <option value="4">Ring 4 · Global</option>
            </select>
          </div>

          <div>
            <label htmlFor="source-status-filter" className="text-[10px] font-bold uppercase text-text-muted mr-1.5">
              Status:
            </label>
            <select
              id="source-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs bg-canvas border border-border rounded px-2 py-1 text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-navy"
            >
              <option value="all">All Statuses</option>
              <option value="ok">Operational</option>
              <option value="stale">Stale (&gt;4h)</option>
              <option value="failed">Failing</option>
              <option value="empty">Empty</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-text-muted">
          Showing <span className="font-semibold text-text-primary">{filtered.length}</span> of {sources.length} feeds
        </div>
      </div>

      {/* Source Health Table */}
      <div className="bg-card rounded-md border border-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-subtle-fill border-b border-border text-[11px] font-bold uppercase tracking-wider text-text-secondary">
                <th scope="col" className="p-3.5">Source Name</th>
                <th scope="col" className="p-3.5">Security Ring</th>
                <th scope="col" className="p-3.5">Language</th>
                <th scope="col" className="p-3.5">Health Status</th>
                <th scope="col" className="p-3.5">Last Collected</th>
                <th scope="col" className="p-3.5 text-right">Today</th>
                <th scope="col" className="p-3.5 text-right">Total</th>
                <th scope="col" className="p-3.5 text-center">Diagnostics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((s) => {
                const isExpanded = expandedId === s.id;
                const hasDiagnostics = Boolean(s.last_error || s.retries || s.status !== 'ok');

                return (
                  <React.Fragment key={s.id}>
                    <tr
                      className={`hover:bg-subtle-fill/40 transition-colors ${
                        isExpanded ? 'bg-subtle-fill/50' : ''
                      }`}
                    >
                      {/* Name */}
                      <td className="p-3.5">
                        <div className="flex flex-col">
                          <a
                            href={s.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-semibold text-text-primary hover:text-primary-navy hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-navy"
                          >
                            {s.name} ↗
                          </a>
                          {s.country && (
                            <span className="text-[10px] text-text-muted">{s.country}</span>
                          )}
                        </div>
                      </td>

                      {/* Ring */}
                      <td className="p-3.5 whitespace-nowrap">
                        <RingMarker ring={s.ring} />
                      </td>

                      {/* Language */}
                      <td className="p-3.5 whitespace-nowrap">
                        <LanguageTag language={s.language} />
                      </td>

                      {/* Status */}
                      <td className="p-3.5 whitespace-nowrap">
                        <StatusPill status={s.status} />
                      </td>

                      {/* Last Collected */}
                      <td className="p-3.5 whitespace-nowrap text-text-muted" title={formatIST(s.last_collected_at)}>
                        {s.last_collected_at ? formatRelativeTime(s.last_collected_at) : 'Never'}
                      </td>

                      {/* Articles Today */}
                      <td className="p-3.5 text-right font-mono font-medium text-text-primary">
                        {s.articles_today}
                      </td>

                      {/* Total Articles */}
                      <td className="p-3.5 text-right font-mono font-semibold text-text-primary">
                        {s.total_articles}
                      </td>

                      {/* Diagnostics Toggle */}
                      <td className="p-3.5 text-center whitespace-nowrap">
                        {hasDiagnostics ? (
                          <button
                            type="button"
                            onClick={() => toggleRow(s.id)}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary-navy hover:underline px-2 py-0.5 rounded border border-border bg-canvas focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
                            aria-expanded={isExpanded}
                            aria-label={`Toggle diagnostics for ${s.name}`}
                          >
                            <span>{isExpanded ? 'Hide' : 'Inspect'}</span>
                            <span aria-hidden="true">{isExpanded ? '▲' : '▼'}</span>
                          </button>
                        ) : (
                          <span className="text-[11px] text-text-muted">—</span>
                        )}
                      </td>
                    </tr>

                    {/* Expandable Diagnostics Drawer */}
                    {isExpanded && (
                      <tr className="bg-subtle-fill/70 border-b border-border">
                        <td colSpan={8} className="p-4">
                          <div className="bg-card p-3.5 rounded border border-border flex flex-col gap-2 text-xs">
                            <div className="flex items-center justify-between border-b border-border/60 pb-2">
                              <span className="font-bold text-text-primary flex items-center gap-1.5">
                                <span>⚠️</span>
                                <span>Feed Telemetry & Diagnostics: {s.name}</span>
                              </span>
                              <span className="text-[11px] text-text-muted">
                                Next Scheduled Poll: {formatIST(s.next_run_at)}
                              </span>
                            </div>

                            {s.last_error ? (
                              <div className="text-[11px] text-[#8C1B13] bg-[#FEECEB] p-2.5 rounded border border-[#F8C8C5] font-mono leading-relaxed">
                                {s.last_error}
                              </div>
                            ) : (
                              <p className="text-text-muted text-[11px]">
                                No unhandled exception logged. Feed response verified within operational thresholds.
                              </p>
                            )}

                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1">
                              <div>
                                <span className="text-text-muted block text-[10px] uppercase">Retries:</span>
                                <span className="font-semibold">{s.retries || 0} attempts</span>
                              </div>
                              <div>
                                <span className="text-text-muted block text-[10px] uppercase">Last Success:</span>
                                <span>{formatIST(s.last_success_at)}</span>
                              </div>
                              <div>
                                <span className="text-text-muted block text-[10px] uppercase">Syndication Feed:</span>
                                <span className="truncate block font-mono text-[10px] text-text-secondary" title={s.rss_url || s.source_url}>
                                  {s.rss_url || s.source_url}
                                </span>
                              </div>
                              <div>
                                <span className="text-text-muted block text-[10px] uppercase">Protocol:</span>
                                <span className="font-mono text-[10px]">RSS 2.0 / Atom XML</span>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


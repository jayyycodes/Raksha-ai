'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { fetchAlerts, markAlertRead, triggerAnomalyScan } from '@/lib/api/client';
import { AlertItem } from '@/lib/api/types';
import { formatISTDate } from '@/lib/utils';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [scanning, setScanning] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    const res = await fetchAlerts({
      unread_only: unreadOnly,
      severity: severityFilter,
    });
    setAlerts(res.alerts);
    setUnreadCount(res.unread_count);
    setLoading(false);
  }, [unreadOnly, severityFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleMarkRead = async (id: number) => {
    const ok = await markAlertRead(id);
    if (ok) {
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, is_read: true } : a))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    }
  };

  const handleTriggerScan = async () => {
    setScanning(true);
    await triggerAnomalyScan();
    await loadData();
    setScanning(false);
  };

  const severityColor = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'high':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-primary-navy text-white">
              Monitoring Grid
            </span>
            {unreadCount > 0 && (
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">
                {unreadCount} Unread
              </span>
            )}
          </div>
          <h1 className="font-serif font-black text-2xl text-text-primary tracking-tight">
            Security Alerts & Anomaly Center
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Real-time statistical surges, volume spikes, and automated watchlist triggers across monitored defence regions.
          </p>
        </div>

        <button
          onClick={handleTriggerScan}
          disabled={scanning}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded bg-accent-gold text-primary-navy hover:brightness-110 disabled:opacity-50 transition"
        >
          {scanning ? (
            <>
              <span className="inline-block w-3.5 h-3.5 border-2 border-primary-navy border-t-transparent rounded-full animate-spin" />
              Scanning Baselines...
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Trigger Anomaly Scan
            </>
          )}
        </button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-surface-card border border-border-card rounded-lg">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-text-muted">Severity:</span>
          {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-2.5 py-1 text-xs rounded capitalize transition ${
                severityFilter === sev
                  ? 'bg-primary-navy text-white font-semibold'
                  : 'text-text-muted hover:text-text-primary hover:bg-surface-elevated'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-xs text-text-muted cursor-pointer select-none">
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={(e) => setUnreadOnly(e.target.checked)}
            className="rounded border-border-card bg-surface-card text-accent-gold focus:ring-accent-gold/20"
          />
          Show Unread Only
        </label>
      </div>

      {/* Alerts Feed */}
      {loading ? (
        <div className="p-12 text-center text-text-muted text-xs font-mono">
          Loading alerts grid...
        </div>
      ) : alerts.length === 0 ? (
        <div className="p-12 text-center border border-dashed border-border-card rounded-lg bg-surface-card/40">
          <svg className="w-8 h-8 mx-auto text-text-muted mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-semibold text-text-primary">No matching alerts found</p>
          <p className="text-xs text-text-muted mt-1">
            All regional baselines are within expected statistical thresholds.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((item) => (
            <div
              key={item.id}
              className={`p-4 rounded-lg border transition ${
                item.is_read
                  ? 'bg-surface-card/60 border-border-card opacity-85'
                  : 'bg-surface-card border-l-4 border-l-accent-gold border-border-card shadow-sm'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${severityColor(item.severity)}`}>
                      {item.severity}
                    </span>
                    <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-surface-elevated text-text-primary border border-border-card">
                      {item.region}
                    </span>
                    <span className="text-[11px] font-mono text-text-muted">
                      {item.alert_type}
                    </span>
                    <span className="text-[11px] font-mono text-text-muted">
                      • {formatISTDate(item.triggered_at)}
                    </span>
                  </div>

                  <p className="text-xs text-text-primary leading-relaxed">
                    {item.description}
                  </p>

                  {item.source_article_ids && item.source_article_ids.length > 0 && (
                    <div className="flex items-center gap-2 pt-1 text-[11px] text-text-muted">
                      <span>Source articles:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {item.source_article_ids.slice(0, 4).map((aid) => (
                          <Link
                            key={aid}
                            href={`/articles/${aid}`}
                            className="font-mono text-accent-gold hover:underline"
                          >
                            #{aid}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {!item.is_read && (
                  <button
                    onClick={() => handleMarkRead(item.id)}
                    className="self-end sm:self-center px-2.5 py-1 text-[11px] font-semibold rounded bg-surface-elevated text-text-muted hover:text-text-primary border border-border-card transition shrink-0"
                  >
                    Mark Read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

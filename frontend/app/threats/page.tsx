'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import {
  fetchThreats,
  fetchThreatHistory,
  fetchAlerts,
  markAlertRead,
  triggerAnomalyScan,
} from '@/lib/api/client';
import { ThreatRegionScore, ThreatHistoryPoint, AlertItem } from '@/lib/api/types';
import { formatISTDate } from '@/lib/utils';

const TREND_BADGES: Record<string, { label: string; cls: string }> = {
  rising: { label: '▲ RISING', cls: 'text-red-700 bg-red-50 border-red-200' },
  falling: { label: '▼ FALLING', cls: 'text-status-green bg-emerald-50 border-emerald-200' },
  stable: { label: '● STABLE', cls: 'text-text-secondary bg-subtle-fill border-border' },
};

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  medium: 'bg-amber-50 text-amber-800 border-amber-200',
  low: 'bg-subtle-fill text-text-secondary border-border',
};

export default function ThreatsAndAlertsPage() {
  const [regions, setRegions] = useState<ThreatRegionScore[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>('LAC-Ladakh');
  const [history, setHistory] = useState<ThreatHistoryPoint[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);
  const [scanning, setScanning] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const loadAll = useCallback(async (activeReg?: string, onlyUnread?: boolean) => {
    setLoading(true);
    const [regList, alertRes] = await Promise.all([
      fetchThreats(),
      fetchAlerts({ unread_only: onlyUnread }),
    ]);
    setRegions(regList);
    setAlerts(alertRes.alerts);
    setUnreadCount(alertRes.unread_count);

    const targetRegion = activeReg || (regList[0]?.region ?? 'LAC-Ladakh');
    setSelectedRegion(targetRegion);
    const hist = await fetchThreatHistory(targetRegion, 30);
    setHistory(hist);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadAll(undefined, unreadOnly);
  }, [loadAll, unreadOnly]);

  const handleSelectRegion = async (reg: string) => {
    setSelectedRegion(reg);
    const hist = await fetchThreatHistory(reg, 30);
    setHistory(hist);
  };

  const handleMarkRead = async (id: number) => {
    const ok = await markAlertRead(id);
    if (ok) {
      setAlerts((prev) =>
        unreadOnly
          ? prev.filter((a) => a.id !== id)
          : prev.map((a) => (a.id === id ? { ...a, is_read: true } : a))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    }
  };

  const handleScan = async () => {
    setScanning(true);
    await triggerAnomalyScan();
    await loadAll(selectedRegion, unreadOnly);
    setScanning(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="font-serif font-bold text-2xl text-text-primary tracking-tight">
            Regional Threat Scoring & Anomaly Alerts
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Weighted theatre threat indicators (1–10), 30-day trend analysis, and statistical/watchlist alert monitoring.
          </p>
        </div>

        <button
          onClick={handleScan}
          disabled={scanning}
          className="text-xs font-semibold px-3.5 py-2 rounded bg-primary-navy text-white hover:bg-primary-navy-dark disabled:opacity-60 transition-colors shadow-sm self-start"
        >
          {scanning ? 'Scanning Corpus...' : 'Run Live Anomaly & Watchlist Scan'}
        </button>
      </div>

      {/* Theatre Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {regions.map((item) => {
          const isSelected = item.region === selectedRegion;
          const trendCfg = TREND_BADGES[item.trend] || TREND_BADGES.stable;
          const barColor =
            item.score >= 7
              ? 'bg-red-600'
              : item.score >= 4.5
                ? 'bg-accent-saffron'
                : 'bg-status-green';

          return (
            <button
              key={item.region}
              onClick={() => handleSelectRegion(item.region)}
              className={`text-left p-4 rounded-lg border transition-all bg-card ${
                isSelected
                  ? 'border-primary-navy ring-2 ring-primary-navy/15 shadow-sm'
                  : 'border-border hover:border-primary-navy/50'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="font-serif font-bold text-sm text-text-primary">
                  {item.region}
                </span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${trendCfg.cls}`}>
                  {trendCfg.label}
                </span>
              </div>

              <div className="flex items-baseline justify-between mb-2">
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-black font-serif text-text-primary">
                    {item.score.toFixed(1)}
                  </span>
                  <span className="text-xs text-text-muted">/ 10</span>
                </div>
                <span className="text-[11px] text-text-muted">
                  {item.article_count} articles in window
                </span>
              </div>

              <div className="w-full h-1.5 bg-subtle-fill rounded-full overflow-hidden">
                <div
                  className={`h-full ${barColor} transition-all`}
                  style={{ width: `${Math.min(100, item.score * 10)}%` }}
                />
              </div>
            </button>
          );
        })}
      </div>

      {/* 30-Day Recharts Threat Timeline */}
      <div className="bg-card border border-border rounded-lg p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
          <div>
            <h2 className="font-serif font-bold text-base text-text-primary">
              30-Day Regional Threat Trajectory — {selectedRegion}
            </h2>
            <p className="text-[11px] text-text-muted">
              Historical regional threat score snapshots recorded across scrape cycles (IST).
            </p>
          </div>
          <span className="text-[11px] font-mono text-text-secondary bg-subtle-fill px-2.5 py-1 rounded border border-border">
            {history.length} data point(s)
          </span>
        </div>

        <div className="w-full h-64">
          {loading ? (
            <div className="h-full flex items-center justify-center text-xs text-text-muted">
              Loading threat timeline...
            </div>
          ) : history.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 10, right: 16, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1F3A5F" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#1F3A5F" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E0D5" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis domain={[0, 10]} tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#DDD8CC',
                    fontSize: '12px',
                    borderRadius: '6px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  name="Threat Score"
                  stroke="#1F3A5F"
                  strokeWidth={2.5}
                  fill="url(#threatGrad)"
                  activeDot={{ r: 5, fill: '#C2570C' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-text-muted">
              No recorded threat snapshots for {selectedRegion} yet.
            </div>
          )}
        </div>
      </div>

      {/* Live Anomaly & Watchlist Alerts Feed */}
      <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <h2 className="font-serif font-bold text-base text-text-primary">
              Anomaly & Watchlist Alert Feed
            </h2>
            {unreadCount > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-600 text-white">
                {unreadCount} Unread
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={unreadOnly}
                onChange={(e) => setUnreadOnly(e.target.checked)}
                className="rounded border-border"
              />
              <span>Unread only</span>
            </label>
            <Link
              href="/watchlists"
              className="text-xs font-semibold text-primary-navy hover:underline"
            >
              Configure Watchlists →
            </Link>
          </div>
        </div>

        <div className="divide-y divide-border/70 border border-border rounded-md overflow-hidden">
          {alerts.length > 0 ? (
            alerts.map((al) => {
              const sevCls = SEVERITY_STYLES[al.severity.toLowerCase()] || SEVERITY_STYLES.low;
              return (
                <div
                  key={al.id}
                  className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    al.is_read ? 'bg-card opacity-75' : 'bg-subtle-fill/35'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${sevCls}`}>
                        {al.severity}
                      </span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-primary-navy/10 text-primary-navy">
                        {al.alert_type}
                      </span>
                      <span className="text-xs font-semibold text-text-primary">{al.region}</span>
                      <span className="text-[11px] text-text-muted">
                        {formatISTDate(al.triggered_at)}
                      </span>
                    </div>

                    <p className="text-xs text-text-primary leading-relaxed">
                      {al.description}
                    </p>

                    {al.source_article_ids && al.source_article_ids.length > 0 && (
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <span className="text-[10px] text-text-muted">Provenance links:</span>
                        {al.source_article_ids.slice(0, 4).map((aid) => (
                          <Link
                            key={aid}
                            href={`/articles/${aid}`}
                            className="text-[10px] font-mono font-semibold text-primary-navy hover:underline"
                          >
                            Article #{aid}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>

                  {!al.is_read ? (
                    <button
                      onClick={() => handleMarkRead(al.id)}
                      className="text-xs font-semibold px-3 py-1.5 rounded border border-border bg-card hover:bg-subtle-fill text-text-primary shrink-0 transition-colors"
                    >
                      Mark Read
                    </button>
                  ) : (
                    <span className="text-[11px] text-text-muted shrink-0">Acknowledged</span>
                  )}
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs text-text-muted">
              No statistical spikes or watchlist alerts triggered in this window.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { fetchAuditLogs, fetchAuditSummary } from '@/lib/api/client';
import { AuditEventItem, AuditSummaryData } from '@/lib/api/types';
import { StatCard } from '@/components/shared/StatCard';
import { formatISTDate } from '@/lib/utils';

export default function AuditLogPage() {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [summary, setSummary] = useState<AuditSummaryData | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [entityFilter, setEntityFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDetails, setSelectedDetails] = useState<Record<string, any> | null>(null);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const [logData, summaryData] = await Promise.all([
        fetchAuditLogs({
          action: actionFilter !== 'all' ? actionFilter : undefined,
          entity_type: entityFilter !== 'all' ? entityFilter : undefined,
          page,
          limit: 25,
        }),
        fetchAuditSummary(),
      ]);
      setEvents(logData.events);
      setTotal(logData.total);
      setSummary(summaryData);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  }, [actionFilter, entityFilter, page]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const getActionBadge = (action: string) => {
    if (action.includes('login_success') || action.includes('register')) {
      return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-status-green/10 text-status-green border border-status-green/20">Auth Success</span>;
    }
    if (action.includes('failed') || action.includes('blocked')) {
      return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-status-red/10 text-status-red border border-status-red/20">Security Alert</span>;
    }
    if (action.includes('merge') || action.includes('split')) {
      return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-status-amber/10 text-status-amber border border-status-amber/20">Ontology Mutation</span>;
    }
    if (action.includes('approve') || action.includes('export')) {
      return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary-navy/10 text-primary-navy border border-primary-navy/20">SitRep Sign-Off</span>;
    }
    return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-subtle-fill text-text-secondary border border-border">System Operation</span>;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-serif font-bold text-text-primary tracking-tight">
          Immutable Audit Log & Security Lineage
        </h1>
        <p className="text-xs text-text-muted mt-1">
          Cryptographically recorded, append-only operational telemetry tracking analyst intelligence access, merges, exports, and authentications.
        </p>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          label="Total Audit Records"
          value={summary?.total_audit_records || total}
          subtext="Immutable ledger entries"
          icon={<span>🛡️</span>}
        />
        <StatCard
          label="Activity Last 24h"
          value={summary?.records_last_24h || 0}
          subtext="Logged analyst actions"
          icon={<span>⏱️</span>}
          accentColor="#C2570C"
        />
        <StatCard
          label="Access Control"
          value="RBAC Enforced"
          subtext="Admin · Analyst · Viewer"
          icon={<span>🔒</span>}
          accentColor="#1F3A5F"
        />
        <StatCard
          label="Compliance Standard"
          value="DPDP & Palantir"
          subtext="Strict lineage & provenance"
          icon={<span>⚖️</span>}
          accentColor="#2F7D4F"
        />
      </div>

      {/* Filter Bar */}
      <div className="bg-card p-3 rounded-md border border-border flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="action-filter" className="text-[10px] font-bold uppercase text-text-muted">
              Action:
            </label>
            <select
              id="action-filter"
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              className="bg-canvas border border-border rounded px-2.5 py-1 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
            >
              <option value="all">All Actions</option>
              <option value="auth.login_success">auth.login_success</option>
              <option value="auth.login_failed">auth.login_failed</option>
              <option value="auth.register">auth.register</option>
              <option value="system.seed_auth">system.seed_auth</option>
              <option value="profile.merge">profile.merge</option>
              <option value="profile.split">profile.split</option>
              <option value="sitrep.approve">sitrep.approve</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="entity-filter" className="text-[10px] font-bold uppercase text-text-muted">
              Entity Type:
            </label>
            <select
              id="entity-filter"
              value={entityFilter}
              onChange={(e) => {
                setEntityFilter(e.target.value);
                setPage(1);
              }}
              className="bg-canvas border border-border rounded px-2.5 py-1 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
            >
              <option value="all">All Entity Types</option>
              <option value="user">User / Identity</option>
              <option value="profile">Entity Profile</option>
              <option value="article">Article Wire</option>
              <option value="sitrep">Situation Report</option>
              <option value="system">Platform System</option>
            </select>
          </div>
        </div>

        <div className="text-text-muted">
          Showing <span className="font-semibold text-text-primary">{events.length}</span> of {total} records
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-card rounded-md border border-border overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-subtle-fill border-b border-border text-[11px] font-bold uppercase tracking-wider text-text-secondary">
                <th scope="col" className="p-3">Timestamp (IST)</th>
                <th scope="col" className="p-3">Analyst / User</th>
                <th scope="col" className="p-3">Classification</th>
                <th scope="col" className="p-3">Action Identifier</th>
                <th scope="col" className="p-3">Target Entity</th>
                <th scope="col" className="p-3">Provenance / IP</th>
                <th scope="col" className="p-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-text-muted">
                    Loading audit trail records...
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-text-muted">
                    No audit records match the selected filters.
                  </td>
                </tr>
              ) : (
                events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-subtle-fill/40 transition-colors">
                    <td className="p-3 whitespace-nowrap text-text-muted font-mono text-[11px]">
                      {ev.created_at ? formatISTDate(ev.created_at) : '—'}
                    </td>
                    <td className="p-3">
                      <div className="font-semibold text-text-primary">{ev.user_name}</div>
                      <div className="text-[10px] text-text-muted">{ev.user_email}</div>
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      {getActionBadge(ev.action)}
                    </td>
                    <td className="p-3 font-mono text-text-primary font-medium">
                      {ev.action}
                    </td>
                    <td className="p-3 text-text-secondary">
                      {ev.entity_type ? (
                        <span>
                          <strong className="text-text-primary">{ev.entity_type}</strong>
                          {ev.entity_id && <span className="font-mono ml-1 text-text-muted">#{ev.entity_id}</span>}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="p-3 text-text-muted font-mono text-[10px]">
                      {ev.ip_address || '127.0.0.1'}
                    </td>
                    <td className="p-3 text-right">
                      {Object.keys(ev.details || {}).length > 0 ? (
                        <button
                          type="button"
                          onClick={() => setSelectedDetails(ev.details)}
                          className="text-[11px] font-semibold text-primary-navy hover:underline focus:outline-none"
                        >
                          View Payload →
                        </button>
                      ) : (
                        <span className="text-text-muted text-[11px]">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details JSON Modal */}
      {selectedDetails && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-card rounded-lg border border-border shadow-2xl max-w-lg w-full p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="font-serif font-bold text-sm text-text-primary">
                Immutable Audit Payload
              </h3>
              <button
                type="button"
                onClick={() => setSelectedDetails(null)}
                className="text-text-muted hover:text-text-primary text-sm font-bold"
              >
                ✕
              </button>
            </div>
            <pre className="text-xs font-mono bg-canvas p-3 rounded border border-border max-h-72 overflow-auto text-text-secondary">
              {JSON.stringify(selectedDetails, null, 2)}
            </pre>
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedDetails(null)}
                className="px-3.5 py-1.5 text-xs font-semibold rounded bg-primary-navy text-white hover:bg-primary-navy-dark transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

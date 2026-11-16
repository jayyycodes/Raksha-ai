'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { fetchCases, createCase } from '@/lib/api/client';
import { CaseListItem } from '@/lib/api/types';
import { StatCard } from '@/components/shared/StatCard';
import { formatISTDate } from '@/lib/utils';

export default function CasesPage() {
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Form state
  const [newTitle, setNewTitle] = useState<string>('');
  const [newDescription, setNewDescription] = useState<string>('');
  const [newPriority, setNewPriority] = useState<string>('high');
  const [newClassification, setNewClassification] = useState<string>('restricted');
  const [newTags, setNewTags] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  const loadCases = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchCases({
        status: statusFilter,
        priority: priorityFilter,
        q: searchQuery.trim() || undefined,
      });
      setCases(data);
    } catch (err) {
      console.error('Failed to load cases:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, searchQuery]);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setSubmitting(true);
    try {
      const tags = newTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      const caseId = await createCase({
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
        priority: newPriority,
        classification: newClassification,
        tags,
      });
      if (caseId) {
        setShowCreateModal(false);
        setNewTitle('');
        setNewDescription('');
        setNewTags('');
        await loadCases();
      }
    } catch (err) {
      console.error('Failed to create case:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'critical':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-status-red/10 text-status-red border border-status-red/20">Critical</span>;
      case 'high':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-status-amber/10 text-status-amber border border-status-amber/20">High</span>;
      case 'medium':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-primary-navy/10 text-primary-navy border border-primary-navy/20">Medium</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-subtle-fill text-text-muted border border-border">Low</span>;
    }
  };

  const getStatusBadge = (s: string) => {
    switch (s) {
      case 'active':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-status-green/10 text-status-green border border-status-green/20">Active Ingest</span>;
      case 'in_review':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-accent-saffron/10 text-accent-saffron border border-accent-saffron/20">In Review</span>;
      case 'closed':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-subtle-fill text-text-muted border border-border">Closed</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-subtle-fill text-text-muted border border-border">{s}</span>;
    }
  };

  const activeCount = cases.filter((c) => c.status === 'active').length;
  const criticalCount = cases.filter((c) => c.priority === 'critical' || c.priority === 'high').length;
  const totalEvidence = cases.reduce((sum, c) => sum + (c.evidence_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-serif font-bold text-text-primary tracking-tight">
            Investigations & Intelligence Cases
          </h1>
          <p className="text-xs text-text-muted mt-1">
            Palantir-inspired thematic case folders grouping articles, entity networks, map pins, and working hypotheses.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded bg-primary-navy hover:bg-primary-navy-dark text-white text-xs font-semibold shadow-sm transition-colors"
        >
          <span>＋</span>
          <span>Open New Case</span>
        </button>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          label="Total Case Folders"
          value={cases.length}
          subtext="Active investigations"
          icon={<span>📁</span>}
        />
        <StatCard
          label="Active Operations"
          value={activeCount}
          subtext="Ongoing intelligence correlation"
          icon={<span>⚡</span>}
          accentColor="#2F7D4F"
        />
        <StatCard
          label="High/Critical Priority"
          value={criticalCount}
          subtext="Elevated threat posture"
          icon={<span>🚨</span>}
          accentColor="#C2570C"
        />
        <StatCard
          label="Pinned Evidence Items"
          value={totalEvidence}
          subtext="Articles, entities, map pins"
          icon={<span>🔗</span>}
          accentColor="#1F3A5F"
        />
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-card p-3 rounded-md border border-border flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="case-status-filter" className="text-[10px] font-bold uppercase text-text-muted">
              Status:
            </label>
            <select
              id="case-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-canvas border border-border rounded px-2.5 py-1 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="in_review">In Review</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="case-priority-filter" className="text-[10px] font-bold uppercase text-text-muted">
              Priority:
            </label>
            <select
              id="case-priority-filter"
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-canvas border border-border rounded px-2.5 py-1 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
            >
              <option value="all">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <input
              type="text"
              placeholder="Search cases..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-canvas border border-border rounded px-2.5 py-1 text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-primary-navy text-xs w-48"
            />
          </div>
        </div>

        <div className="text-text-muted">
          Showing <span className="font-semibold text-text-primary">{cases.length}</span> investigation dossiers
        </div>
      </div>

      {/* Cases Grid */}
      {loading ? (
        <div className="p-12 text-center text-text-muted bg-card rounded-md border border-border">
          Loading active investigation cases...
        </div>
      ) : cases.length === 0 ? (
        <div className="p-12 text-center text-text-muted bg-card rounded-md border border-border">
          No investigation cases found matching the current criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.map((c) => (
            <div
              key={c.id}
              className="bg-card rounded-md border border-border hover:border-text-secondary/40 transition-all p-4 flex flex-col justify-between shadow-xs"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[9px] font-mono uppercase font-bold px-1.5 py-0.5 rounded bg-subtle-fill text-text-muted border border-border">
                    {c.classification}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {getPriorityBadge(c.priority)}
                    {getStatusBadge(c.status)}
                  </div>
                </div>

                <div>
                  <Link
                    href={`/cases/${c.id}`}
                    className="font-serif font-bold text-sm text-text-primary hover:text-primary-navy hover:underline line-clamp-2"
                  >
                    {c.title}
                  </Link>
                  {c.description && (
                    <p className="text-xs text-text-muted mt-1 line-clamp-3 leading-relaxed">
                      {c.description}
                    </p>
                  )}
                </div>

                {c.tags && c.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {c.tags.slice(0, 4).map((tag, i) => (
                      <span
                        key={i}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-subtle-fill text-text-secondary border border-border"
                      >
                        #{tag}
                      </span>
                    ))}
                    {c.tags.length > 4 && (
                      <span className="text-[10px] text-text-muted self-center">
                        +{c.tags.length - 4}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-[11px] text-text-muted">
                <div className="flex items-center gap-2.5">
                  <span title="Pinned Evidence">📎 {c.evidence_count}</span>
                  <span title="Analyst Hypotheses">📝 {c.notes_count}</span>
                </div>
                <Link
                  href={`/cases/${c.id}`}
                  className="font-semibold text-primary-navy hover:underline flex items-center gap-1"
                >
                  <span>Dossier</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateCase}
            className="bg-card rounded-lg border border-border shadow-2xl max-w-lg w-full p-6 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="font-serif font-bold text-base text-text-primary">
                Open New Intelligence Case Folder
              </h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-text-muted hover:text-text-primary text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Case Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Northern Sector Surveillance & Radome Activity"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Investigation Description
                </label>
                <textarea
                  rows={3}
                  placeholder="Operational context, key targets, and analytical questions..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                    Priority Level
                  </label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
                    className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                    Classification
                  </label>
                  <select
                    value={newClassification}
                    onChange={(e) => setNewClassification(e.target.value)}
                    className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                  >
                    <option value="unclassified">Unclassified</option>
                    <option value="restricted">Restricted</option>
                    <option value="confidential">Confidential</option>
                    <option value="secret">Secret</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Thematic Tags (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. LAC, Airbase, Satellite, PLAAF"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-3 py-1.5 text-xs text-text-muted hover:text-text-primary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !newTitle.trim()}
                className="px-4 py-1.5 text-xs font-semibold rounded bg-primary-navy text-white hover:bg-primary-navy-dark disabled:opacity-60 transition-colors"
              >
                {submitting ? 'Creating Case...' : 'Open Case'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

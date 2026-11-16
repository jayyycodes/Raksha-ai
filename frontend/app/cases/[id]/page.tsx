'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  fetchCaseById,
  updateCase,
  addCaseItem,
  addCaseNote,
  exportCaseDossier,
} from '@/lib/api/client';
import { CaseDetailData } from '@/lib/api/types';
import { formatISTDate } from '@/lib/utils';

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = Number(params.id);

  const [data, setData] = useState<CaseDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [exporting, setExporting] = useState<boolean>(false);

  // Modals state
  const [showItemModal, setShowItemModal] = useState<boolean>(false);
  const [showNoteModal, setShowNoteModal] = useState<boolean>(false);

  // New Evidence Form
  const [itemType, setItemType] = useState<string>('article');
  const [itemId, setItemId] = useState<string>('');
  const [itemTitle, setItemTitle] = useState<string>('');
  const [itemNotes, setItemNotes] = useState<string>('');
  const [submittingItem, setSubmittingItem] = useState<boolean>(false);

  // New Note Form
  const [noteText, setNoteText] = useState<string>('');
  const [hypothesis, setHypothesis] = useState<string>('');
  const [submittingNote, setSubmittingNote] = useState<boolean>(false);

  const loadCase = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const res = await fetchCaseById(caseId);
      setData(res);
    } catch (err) {
      console.error('Failed to load case detail:', err);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    loadCase();
  }, [loadCase]);

  const handleStatusChange = async (newStatus: string) => {
    if (!data) return;
    const ok = await updateCase(caseId, { status: newStatus as any });
    if (ok) {
      setData((prev) => (prev ? { ...prev, case: { ...prev.case, status: newStatus as any } } : null));
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemId.trim()) return;
    setSubmittingItem(true);
    try {
      const ok = await addCaseItem(caseId, {
        item_type: itemType,
        item_id: itemId.trim(),
        title: itemTitle.trim() || undefined,
        analyst_notes: itemNotes.trim() || undefined,
      });
      if (ok) {
        setShowItemModal(false);
        setItemId('');
        setItemTitle('');
        setItemNotes('');
        await loadCase();
      }
    } catch (err) {
      console.error('Failed to attach item:', err);
    } finally {
      setSubmittingItem(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setSubmittingNote(true);
    try {
      const ok = await addCaseNote(caseId, {
        note_text: noteText.trim(),
        hypothesis: hypothesis.trim() || undefined,
      });
      if (ok) {
        setShowNoteModal(false);
        setNoteText('');
        setHypothesis('');
        await loadCase();
      }
    } catch (err) {
      console.error('Failed to add note:', err);
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const dossier = await exportCaseDossier(caseId);
      if (dossier) {
        const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `case_${caseId}_dossier_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to export dossier:', err);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-text-muted bg-card rounded-md border border-border">
        Loading case dossier #{caseId}...
      </div>
    );
  }

  if (!data || !data.case) {
    return (
      <div className="p-12 text-center text-text-muted bg-card rounded-md border border-border">
        Case dossier not found.{' '}
        <Link href="/cases" className="text-primary-navy font-semibold hover:underline">
          Return to Cases
        </Link>
      </div>
    );
  }

  const c = data.case;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <Link href="/cases" className="hover:text-primary-navy hover:underline">
            ← Cases
          </Link>
          <span>/</span>
          <span className="font-mono text-text-primary">CASE-{c.id}</span>
          <span className="px-1.5 py-0.2 rounded text-[9px] uppercase font-bold bg-subtle-fill text-text-muted border border-border">
            {c.classification}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Select */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-[10px] uppercase font-bold text-text-muted">Status:</span>
            <select
              value={c.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="bg-canvas border border-border rounded px-2 py-1 text-xs font-semibold text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
            >
              <option value="active">Active Ingest</option>
              <option value="in_review">In Review</option>
              <option value="closed">Closed / Archived</option>
            </select>
          </div>

          <button
            type="button"
            onClick={handleExport}
            disabled={exporting}
            className="px-3 py-1.5 rounded bg-card hover:bg-subtle-fill text-text-primary border border-border text-xs font-semibold shadow-xs transition-colors"
          >
            {exporting ? 'Exporting...' : 'Export Dossier ↗'}
          </button>
        </div>
      </div>

      {/* Case Header Dossier Box */}
      <div className="bg-card rounded-md border border-border p-5 space-y-4 shadow-xs">
        <div>
          <h1 className="text-xl font-serif font-bold text-text-primary tracking-tight">
            {c.title}
          </h1>
          {c.description && (
            <p className="text-xs text-text-secondary mt-1.5 leading-relaxed">
              {c.description}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs text-text-muted pt-2 border-t border-border">
          <div>
            <strong className="text-text-primary">Priority:</strong>{' '}
            <span className="uppercase font-semibold text-accent-saffron">{c.priority}</span>
          </div>
          <div>
            <strong className="text-text-primary">Workspace:</strong> {c.workspace_name || 'Shared'}
          </div>
          <div>
            <strong className="text-text-primary">Lead Analyst:</strong>{' '}
            {c.lead_analyst_name || 'Assigned Officer'}
          </div>
          <div>
            <strong className="text-text-primary">Last Updated:</strong>{' '}
            {formatISTDate(c.updated_at)}
          </div>
        </div>

        {c.tags && c.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {c.tags.map((tag, idx) => (
              <span
                key={idx}
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-subtle-fill text-text-secondary border border-border"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Two Column Layout: Evidence Stream vs Analyst Hypotheses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Pinned Evidence */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-2">
              <span>Attached Evidence Items</span>
              <span className="px-1.5 py-0.2 rounded-full bg-subtle-fill text-[10px] font-mono text-text-primary">
                {data.evidence_items.length}
              </span>
            </h2>

            <button
              type="button"
              onClick={() => setShowItemModal(true)}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-primary-navy hover:bg-primary-navy-dark text-white shadow-xs transition-colors"
            >
              ＋ Attach Evidence
            </button>
          </div>

          {data.evidence_items.length === 0 ? (
            <div className="p-8 text-center text-xs text-text-muted bg-card rounded-md border border-border">
              No evidence items attached to this case folder yet. Click &ldquo;Attach Evidence&rdquo; to pin articles or entities.
            </div>
          ) : (
            <div className="space-y-3">
              {data.evidence_items.map((item) => (
                <div
                  key={item.id}
                  className="bg-card p-3.5 rounded-md border border-border space-y-2 shadow-xs"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-subtle-fill text-primary-navy border border-border">
                      {item.item_type}
                    </span>
                    <span className="text-[10px] text-text-muted">
                      {formatISTDate(item.added_at)}
                    </span>
                  </div>

                  <div className="font-semibold text-xs text-text-primary">
                    {item.title}
                  </div>

                  {item.analyst_notes && (
                    <div className="text-[11px] text-text-secondary bg-subtle-fill/40 p-2 rounded border border-border/60">
                      <strong>Note:</strong> {item.analyst_notes}
                    </div>
                  )}

                  <div className="text-[10px] text-text-muted flex items-center justify-between pt-1">
                    <span>Added by: {item.added_by_name || 'Analyst'}</span>
                    {item.item_type === 'article' && (
                      <Link
                        href={`/articles/${item.item_id}`}
                        className="text-primary-navy font-semibold hover:underline"
                      >
                        Inspect Article →
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Working Hypotheses & Notes Timeline */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-2">
              <span>Analyst Working Hypotheses & Notes</span>
              <span className="px-1.5 py-0.2 rounded-full bg-subtle-fill text-[10px] font-mono text-text-primary">
                {data.notes.length}
              </span>
            </h2>

            <button
              type="button"
              onClick={() => setShowNoteModal(true)}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-card hover:bg-subtle-fill text-text-primary border border-border shadow-xs transition-colors"
            >
              ＋ Add Hypothesis
            </button>
          </div>

          {data.notes.length === 0 ? (
            <div className="p-8 text-center text-xs text-text-muted bg-card rounded-md border border-border">
              No hypotheses recorded yet. Document your working intelligence assessment.
            </div>
          ) : (
            <div className="space-y-3">
              {data.notes.map((n) => (
                <div
                  key={n.id}
                  className="bg-card p-3.5 rounded-md border border-border space-y-2 shadow-xs"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-xs text-text-primary">
                      {n.analyst_name || 'Lead Analyst'}
                    </span>
                    <span className="text-[10px] text-text-muted">
                      {formatISTDate(n.created_at)}
                    </span>
                  </div>

                  {n.hypothesis && (
                    <div className="text-xs font-semibold text-accent-saffron bg-accent-saffron-light p-2 rounded border border-accent-saffron/20">
                      💡 <strong>Hypothesis:</strong> {n.hypothesis}
                    </div>
                  )}

                  <p className="text-xs text-text-secondary leading-relaxed">
                    {n.note_text}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Attach Evidence Modal */}
      {showItemModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleAddItem}
            className="bg-card rounded-lg border border-border shadow-2xl max-w-md w-full p-6 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="font-serif font-bold text-sm text-text-primary">
                Attach Evidence Item to Case
              </h3>
              <button
                type="button"
                onClick={() => setShowItemModal(false)}
                className="text-text-muted hover:text-text-primary text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Evidence Type
                </label>
                <select
                  value={itemType}
                  onChange={(e) => setItemType(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                >
                  <option value="article">Article Wire</option>
                  <option value="entity">Named Entity</option>
                  <option value="event">Threaded Event</option>
                  <option value="incident">Map Incident</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Item ID / Unique Key *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 148 or PLA Western Theater Command"
                  value={itemId}
                  onChange={(e) => setItemId(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Display Title (Optional)
                </label>
                <input
                  type="text"
                  placeholder="Leave empty to auto-derive from source"
                  value={itemTitle}
                  onChange={(e) => setItemTitle(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Analyst Assessment / Notes
                </label>
                <textarea
                  rows={2}
                  placeholder="Why is this relevant to the case hypothesis?"
                  value={itemNotes}
                  onChange={(e) => setItemNotes(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setShowItemModal(false)}
                className="px-3 py-1.5 text-xs text-text-muted hover:text-text-primary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingItem || !itemId.trim()}
                className="px-4 py-1.5 text-xs font-semibold rounded bg-primary-navy text-white hover:bg-primary-navy-dark disabled:opacity-60 transition-colors"
              >
                {submittingItem ? 'Attaching...' : 'Attach Evidence'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Add Hypothesis / Note Modal */}
      {showNoteModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleAddNote}
            className="bg-card rounded-lg border border-border shadow-2xl max-w-md w-full p-6 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="font-serif font-bold text-sm text-text-primary">
                Record Analytical Hypothesis
              </h3>
              <button
                type="button"
                onClick={() => setShowNoteModal(false)}
                className="text-text-muted hover:text-text-primary text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Working Hypothesis (1 Line)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Asymmetrical forward deployment masks logistical rotation"
                  value={hypothesis}
                  onChange={(e) => setHypothesis(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase text-text-muted mb-1">
                  Analytical Working Note *
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Detailed factual synthesis, corroboration checks, and next indicators to watch..."
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  className="w-full bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-primary-navy"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setShowNoteModal(false)}
                className="px-3 py-1.5 text-xs text-text-muted hover:text-text-primary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingNote || !noteText.trim()}
                className="px-4 py-1.5 text-xs font-semibold rounded bg-primary-navy text-white hover:bg-primary-navy-dark disabled:opacity-60 transition-colors"
              >
                {submittingNote ? 'Saving...' : 'Save Note'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

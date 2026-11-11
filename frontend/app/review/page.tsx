'use client';

import React, { useEffect, useState } from 'react';
import { fetchReviewQueue, submitReviewAction } from '@/lib/api/client';
import { MergeSuggestionItem } from '@/lib/api/types';

export default function ReviewQueuePage() {
  const [suggestions, setSuggestions] = useState<MergeSuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<number | null>(null);

  async function loadData() {
    setLoading(true);
    const data = await fetchReviewQueue('pending');
    setSuggestions(data);
    setLoading(false);
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleAction(id: number, action: 'accept' | 'reject' | 'split') {
    setActingId(id);
    const ok = await submitReviewAction(id, action);
    if (ok) {
      // Remove from pending list
      setSuggestions((prev) => prev.filter((s) => s.id !== id));
    }
    setActingId(null);
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="font-serif font-bold text-2xl text-text-primary tracking-tight">
          Entity Disambiguation Review Queue
        </h1>
        <p className="text-xs text-text-muted mt-0.5">
          Human-in-the-loop analyst decisions for candidate aliases, name variants, and entity merges.
        </p>
      </div>

      {/* Review Queue List */}
      {!loading && suggestions.length > 0 ? (
        <div className="space-y-4">
          {suggestions.map((s) => (
            <div
              key={s.id}
              className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4"
            >
              {/* Top Row: Comparison */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-subtle-fill/40 rounded-lg border border-border">
                {/* Entity A */}
                <div className="flex-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted block mb-1">
                    Candidate Alias (Source)
                  </span>
                  <p className="font-serif font-bold text-base text-text-primary">{s.source_name}</p>
                  <span className="text-[11px] text-text-muted font-mono">{s.entity_type}</span>
                </div>

                {/* Similarity Pillar */}
                <div className="flex flex-col items-center justify-center px-4">
                  <span className="text-xs font-bold text-primary-navy">
                    {(s.similarity_score * 100).toFixed(0)}%
                  </span>
                  <span className="text-[9px] uppercase tracking-wider text-text-muted font-semibold">
                    Similarity
                  </span>
                </div>

                {/* Entity B */}
                <div className="flex-1 md:text-right">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted block mb-1">
                    Canonical Target Profile
                  </span>
                  <p className="font-serif font-bold text-base text-text-primary">{s.target_name}</p>
                  <span className="text-[11px] text-text-muted font-mono">{s.entity_type}</span>
                </div>
              </div>

              {/* Match Reason */}
              <div className="text-xs text-text-secondary leading-relaxed">
                <strong className="text-text-primary font-semibold">Algorithmic Evidence: </strong>
                {s.reason}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <span className="text-[11px] text-text-muted">
                  Action logs to immutable audit trail.
                </span>

                <div className="flex items-center gap-2">
                  <button
                    disabled={actingId === s.id}
                    onClick={() => handleAction(s.id, 'reject')}
                    className="px-3 py-1.5 rounded bg-subtle-fill hover:bg-border text-text-secondary text-xs font-semibold border border-border transition-colors disabled:opacity-50"
                  >
                    Keep Separate (Reject)
                  </button>

                  <button
                    disabled={actingId === s.id}
                    onClick={() => handleAction(s.id, 'accept')}
                    className="px-4 py-1.5 rounded bg-status-green text-white hover:bg-status-green-dark text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
                  >
                    {actingId === s.id ? 'Processing...' : 'Accept Merge'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="w-full py-16 bg-card border border-border rounded-lg flex flex-col items-center justify-center text-center p-6">
          <span className="text-3xl mb-2">⚖️</span>
          <p className="text-sm font-semibold text-text-primary">
            {loading ? 'Fetching pending candidate reviews...' : 'Review Queue Clear'}
          </p>
          <p className="text-xs text-text-muted mt-1 max-w-sm">
            All candidate entity pairs have been disambiguated. High-confidence pairs ($\ge 95\%$) are merged automatically, while ambiguous pairs await review here.
          </p>
        </div>
      )}
    </div>
  );
}


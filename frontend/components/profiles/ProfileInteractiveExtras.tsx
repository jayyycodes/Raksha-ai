'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import {
  addProfileNote,
  createWatchlist,
  fetchProfileNotes,
} from '@/lib/api/client';
import { ProfileNoteItem } from '@/lib/api/types';
import { formatISTDate } from '@/lib/utils';

const ProfileMiniMap = dynamic(
  () => import('./ProfileMiniMap').then((m) => m.ProfileMiniMap),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-56 rounded border border-border bg-subtle-fill flex items-center justify-center text-xs text-text-muted">
        Loading tactical sector map...
      </div>
    ),
  }
);

interface ProfileInteractiveExtrasProps {
  profileId: number;
  entityName: string;
  mentionCount: number;
  sourceCount: number;
  locations: Array<{ name: string; relationship: string }>;
}

export const ProfileInteractiveExtras: React.FC<ProfileInteractiveExtrasProps> = ({
  profileId,
  entityName,
  mentionCount,
  sourceCount,
  locations,
}) => {
  const [notes, setNotes] = useState<ProfileNoteItem[]>([]);
  const [noteInput, setNoteInput] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [watching, setWatching] = useState(false);
  const [showLineage, setShowLineage] = useState(false);

  useEffect(() => {
    fetchProfileNotes(profileId).then(setNotes);
  }, [profileId]);

  const handleSaveNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteInput.trim()) return;
    setSavingNote(true);
    const updated = await addProfileNote(profileId, noteInput.trim());
    setNotes(updated);
    setNoteInput('');
    setSavingNote(false);
  };

  const handleWatchEntity = async () => {
    setWatching(true);
    await createWatchlist({
      name: `Track: ${entityName}`,
      query_type: 'entity',
      query_value: entityName,
    });
  };

  return (
    <div className="space-y-6">
      {/* Lineage & Watch Actions Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-subtle-fill/50 border border-border rounded-lg p-3.5">
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <span className="font-semibold text-text-primary">Analyst Controls:</span>
          <button
            type="button"
            onClick={() => setShowLineage((v) => !v)}
            className="text-xs font-semibold px-2.5 py-1 rounded border border-border bg-card hover:bg-subtle-fill text-primary-navy transition-colors"
          >
            {showLineage ? 'Hide Lineage Panel' : 'Why is this here? (Lineage)'}
          </button>
        </div>

        <button
          type="button"
          onClick={handleWatchEntity}
          disabled={watching}
          className="text-xs font-semibold px-3 py-1.5 rounded bg-primary-navy text-white hover:bg-primary-navy-dark disabled:opacity-70 transition-colors"
        >
          {watching ? '✓ Added to Watchlist' : '🔔 Watch Entity Alerts'}
        </button>
      </div>

      {/* Lineage Drawer ("Why is this here?") */}
      {showLineage && (
        <div className="bg-card border border-primary-navy/30 rounded-lg p-4 space-y-2 text-xs shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="font-serif font-bold text-sm text-primary-navy">
              Provenance & Lineage Audit — {entityName}
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-muted">
              Candidate Rule: ≥3 mentions & ≥2 sources
            </span>
          </div>
          <p className="text-text-secondary leading-relaxed">
            This entity profile was promoted and consolidated from{' '}
            <strong className="text-text-primary">{mentionCount}</strong> extracted mentions across{' '}
            <strong className="text-text-primary">{sourceCount}</strong> independent monitored feeds using{' '}
            <code className="px-1 py-0.5 rounded bg-subtle-fill">ResolutionAgent:0.2.0</code> and official public baseline lists.
            All statements carry explicit source citations; zero unattributed labels are applied.
          </p>
        </div>
      )}

      {/* Map + Analyst Notes Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reported Locations Mini-Map */}
        <div className="bg-card border border-border rounded-lg p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="font-serif font-bold text-sm text-text-primary">
              Reported Locations Map
            </h3>
            <span className="text-[10px] text-text-muted">
              {locations.length} associated sector(s)
            </span>
          </div>
          <ProfileMiniMap locations={locations} entityName={entityName} />
        </div>

        {/* Analyst Notes */}
        <div className="bg-card border border-border rounded-lg p-4 space-y-3 shadow-sm flex flex-col justify-between">
          <div className="space-y-3">
            <h3 className="font-serif font-bold text-sm text-text-primary">
              Analyst Investigation Notes ({notes.length})
            </h3>

            <form onSubmit={handleSaveNote} className="flex gap-2">
              <input
                type="text"
                placeholder="Add analyst observation or corroboration note..."
                value={noteInput}
                onChange={(e) => setNoteInput(e.target.value)}
                className="flex-1 text-xs bg-canvas border border-border rounded px-3 py-1.5 text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
              />
              <button
                type="submit"
                disabled={savingNote}
                className="text-xs font-semibold px-3 py-1.5 rounded bg-primary-navy text-white hover:bg-primary-navy-dark disabled:opacity-60"
              >
                Save
              </button>
            </form>

            <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
              {notes.length > 0 ? (
                notes.map((n, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-subtle-fill/60 border border-border/60 text-xs space-y-1"
                  >
                    <p className="text-text-primary">{n.note}</p>
                    <span className="text-[10px] text-text-muted block">
                      {n.analyst} · {formatISTDate(n.created_at)}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-text-muted py-4 text-center">
                  No analyst notes attached to this profile yet.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


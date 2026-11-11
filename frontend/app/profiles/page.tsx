'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchProfiles } from '@/lib/api/client';
import { ProfileHeaderItem } from '@/lib/api/types';
import { RingMarker } from '@/components/shared/RingMarker';
import { formatISTDate } from '@/lib/utils';

export default function ProfilesDirectoryPage() {
  const [profiles, setProfiles] = useState<ProfileHeaderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await fetchProfiles({
        entity_type: selectedType,
        q: searchQuery || undefined,
      });
      setProfiles(res);
      setLoading(false);
    }
    loadData();
  }, [selectedType, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="font-serif font-bold text-2xl text-text-primary tracking-tight">
            Entity Profiles & Object Views
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Attributed intelligence dossiers on military units, defence leaders, adversary entities, and key strategic locations.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search profile or alias..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="text-xs bg-card border border-border rounded px-3 py-1.5 text-text-primary placeholder:text-text-muted w-48 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          />

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-xs bg-card border border-border rounded px-2.5 py-1.5 text-text-primary font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          >
            <option value="all">All Types</option>
            <option value="ORGANISATION">Organisations</option>
            <option value="PERSON">Persons</option>
            <option value="LOCATION">Locations</option>
            <option value="EQUIPMENT">Equipment</option>
          </select>
        </div>
      </div>

      {/* Profiles Grid */}
      {!loading && profiles.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map((p) => (
            <Link
              key={p.id}
              href={`/profiles/${p.id}`}
              className="bg-card border border-border rounded-lg p-5 hover:border-primary-navy hover:shadow-sm transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-subtle-fill text-text-secondary border border-border">
                    {p.entity_type}
                  </span>
                  <RingMarker ring={p.primary_ring} />
                </div>

                <h3 className="font-serif font-bold text-base text-text-primary group-hover:text-primary-navy transition-colors mb-1.5">
                  {p.name}
                </h3>

                {p.aliases && p.aliases.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1 mb-3">
                    <span className="text-[10px] text-text-muted font-medium">Aliases:</span>
                    {p.aliases.map((alias, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] px-1.5 py-0.2 rounded bg-canvas border border-border text-text-secondary font-mono"
                      >
                        {alias}
                      </span>
                    ))}
                  </div>
                )}

                <p className="text-xs text-text-muted line-clamp-2 leading-relaxed mb-4">
                  {p.description}
                </p>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-between text-[11px] text-text-muted">
                <span>
                  <strong className="text-text-primary font-semibold">{p.mention_count}</strong> mentions across{' '}
                  <strong className="text-text-primary font-semibold">{p.source_count}</strong> outlets
                </span>
                <span className="text-primary-navy font-semibold group-hover:translate-x-0.5 transition-transform">
                  View Dossier →
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="w-full py-16 bg-card border border-border rounded-lg flex flex-col items-center justify-center text-center p-6">
          <span className="text-2xl mb-2">👤</span>
          <p className="text-sm font-semibold text-text-primary">
            {loading ? 'Loading entity dossiers...' : 'No profiles found matching search.'}
          </p>
          <p className="text-xs text-text-muted mt-1 max-w-sm">
            Entities become established profiles when referenced in $\ge 3$ reports across at least 2 distinct intelligence feeds.
          </p>
        </div>
      )}
    </div>
  );
}


'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { fetchMapIncidents } from '@/lib/api/client';
import { MapIncident } from '@/lib/api/types';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';

// Dynamically import Leaflet map with SSR disabled
const IncidentMap = dynamic(
  () => import('@/components/map/IncidentMap').then((m) => m.IncidentMap),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[calc(100vh-140px)] rounded-lg bg-card border border-border p-8 flex flex-col items-center justify-center gap-3">
        <LoadingSkeleton className="w-16 h-16 rounded-full" />
        <span className="text-sm font-semibold text-text-secondary">Loading Geospatial Incident Map & Tactical Boundaries...</span>
      </div>
    ),
  }
);

export default function MapPage() {
  const [incidents, setIncidents] = useState<MapIncident[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRing, setSelectedRing] = useState<string>('all');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const data = await fetchMapIncidents({ ring: selectedRing });
      setIncidents(data);
      setLoading(false);
    }
    loadData();
  }, [selectedRing]);

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="font-serif font-bold text-2xl text-text-primary tracking-tight">
            Geospatial Incident Map
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Tactical border observation, flashpoint threat distribution & disengagement tracking across India & periphery.
          </p>
        </div>

        {/* Ring Filter Pill */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted font-medium">Filter Theatre Ring:</span>
          <select
            value={selectedRing}
            onChange={(e) => setSelectedRing(e.target.value)}
            className="text-xs bg-card border border-border rounded px-2.5 py-1.5 text-text-primary font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          >
            <option value="all">All Theatres ({incidents.length} pins)</option>
            <option value="1">Ring 1 · India Fronts</option>
            <option value="2">Ring 2 · Adversaries</option>
            <option value="3">Ring 3 · Regional Neighbours</option>
            <option value="4">Ring 4 · Global Corroboration</option>
          </select>
        </div>
      </div>

      {/* Incident Map Component */}
      {!loading && incidents.length > 0 ? (
        <IncidentMap incidents={incidents} />
      ) : (
        <div className="w-full h-[calc(100vh-140px)] rounded-lg bg-card border border-border flex items-center justify-center text-sm text-text-muted">
          {loading ? 'Fetching tactical coordinates...' : 'No incidents matching theatre filter.'}
        </div>
      )}
    </div>
  );
}


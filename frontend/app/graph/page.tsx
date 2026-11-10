'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { fetchGraphData } from '@/lib/api/client';
import { GraphData } from '@/lib/api/types';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';

// Dynamically import Cytoscape with SSR disabled
const EntityGraph = dynamic(
  () => import('@/components/graph/EntityGraph').then((m) => m.EntityGraph),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[calc(100vh-140px)] rounded-lg bg-card border border-border p-8 flex flex-col items-center justify-center gap-3">
        <LoadingSkeleton className="w-16 h-16 rounded-full" />
        <span className="text-sm font-semibold text-text-secondary">Rendering Entity Knowledge Graph & Force Layout...</span>
      </div>
    ),
  }
);

export default function GraphPage() {
  const [data, setData] = useState<GraphData>({ nodes: [], edges: [], total_nodes: 0, total_edges: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedRing, setSelectedRing] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await fetchGraphData({
        entity_type: selectedType,
        ring: selectedRing,
        q: searchQuery || undefined,
      });
      setData(res);
      setLoading(false);
    }
    loadData();
  }, [selectedType, selectedRing, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="font-serif font-bold text-2xl text-text-primary tracking-tight">
            Entity Knowledge Graph
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Palantir-style ontological link analysis connecting people, organisations, military units, and strategic locations.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search box */}
          <input
            type="text"
            placeholder="Search entity..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="text-xs bg-card border border-border rounded px-2.5 py-1.5 text-text-primary placeholder:text-text-muted w-36 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          />

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-xs bg-card border border-border rounded px-2.5 py-1.5 text-text-primary font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          >
            <option value="all">All Entity Types</option>
            <option value="ORGANISATION">Organisations</option>
            <option value="PERSON">Persons</option>
            <option value="LOCATION">Locations</option>
            <option value="EQUIPMENT">Equipment</option>
          </select>

          {/* Ring Filter */}
          <select
            value={selectedRing}
            onChange={(e) => setSelectedRing(e.target.value)}
            className="text-xs bg-card border border-border rounded px-2.5 py-1.5 text-text-primary font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          >
            <option value="all">All Rings</option>
            <option value="1">Ring 1 · India</option>
            <option value="2">Ring 2 · Adversaries</option>
            <option value="3">Ring 3 · Regional</option>
            <option value="4">Ring 4 · Global</option>
          </select>
        </div>
      </div>

      {/* Graph Visualizer */}
      {!loading && data.nodes.length > 0 ? (
        <EntityGraph data={data} />
      ) : (
        <div className="w-full h-[calc(100vh-140px)] rounded-lg bg-card border border-border flex items-center justify-center text-sm text-text-muted">
          {loading ? 'Calculating graph physics...' : 'No entities found matching filters.'}
        </div>
      )}
    </div>
  );
}

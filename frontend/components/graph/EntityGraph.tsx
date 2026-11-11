'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import cytoscape from 'cytoscape';
import { GraphData, GraphNodeItem } from '@/lib/api/types';
import { RingMarker } from '@/components/shared/RingMarker';

interface EntityGraphProps {
  data: GraphData;
}

const TYPE_COLORS: Record<string, string> = {
  PERSON: '#1F3A5F',       // Primary Navy
  ORGANISATION: '#C2570C', // Saffron Accent
  LOCATION: '#2F7D4F',     // Status Green
  EQUIPMENT: '#5B4B8A',    // Regional Purple
  EVENT: '#B7791F',        // Warning Amber
};

export const EntityGraph: React.FC<EntityGraphProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNodeItem | null>(null);

  useEffect(() => {
    if (!containerRef.current || !data.nodes.length) return;

    // Convert API nodes & edges to Cytoscape element definitions
    const elements: cytoscape.ElementDefinition[] = [
      ...data.nodes.map((n) => ({
        data: {
          id: n.id,
          label: n.label,
          type: n.entity_type,
          ring: n.primary_ring,
          mentions: n.mention_count,
          raw: n,
        },
      })),
      ...data.edges.map((e) => ({
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.link_type,
          confidence: e.confidence,
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#1A1F2B',
            'font-size': '10px',
            'font-family': 'IBM Plex Sans, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'background-color': (ele: any) => TYPE_COLORS[ele.data('type')] || '#7A8294',
            'width': (ele: any) => Math.min(42, Math.max(22, 16 + ele.data('mentions') * 0.4)),
            'height': (ele: any) => Math.min(42, Math.max(22, 16 + ele.data('mentions') * 0.4)),
            'border-width': 2,
            'border-color': '#FFFFFF',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': '#DDD8CC',
            'target-arrow-color': '#DDD8CC',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'color': '#7A8294',
            'text-rotation': 'autorotate',
            'text-background-opacity': 0.85,
            'text-background-color': '#FFFFFF',
            'text-background-padding': '2px',
          },
        },
        {
          selector: ':selected',
          style: {
            'border-width': 3,
            'border-color': '#C2570C',
            'line-color': '#C2570C',
            'target-arrow-color': '#C2570C',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeRepulsion: () => 450000,
        nodeOverlap: 20,
        idealEdgeLength: () => 100,
        edgeElasticity: () => 100,
        gravity: 80,
        numIter: 1000,
      },
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode(node.data('raw'));
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    // Ensure proper sizing and fit after DOM mount
    cy.ready(() => {
      cy.resize();
      cy.fit(undefined, 35);
    });

    const timer = setTimeout(() => {
      cy.resize();
      cy.fit(undefined, 35);
    }, 150);

    cyRef.current = cy;

    return () => {
      clearTimeout(timer);
      cy.destroy();
    };
  }, [data]);

  const resetView = () => {
    cyRef.current?.fit(undefined, 30);
  };

  return (
    <div className="relative w-full h-[calc(100vh-140px)] rounded-lg overflow-hidden border border-border flex bg-card">
      {/* Graph Viewport */}
      <div ref={containerRef} className="flex-1 h-full z-0 bg-[#FBF9F5]" />

      {/* Floating Toolbar Controls */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-card/90 backdrop-blur p-1.5 rounded border border-border shadow-sm">
        <button
          onClick={resetView}
          className="text-xs px-2.5 py-1 rounded bg-subtle-fill hover:bg-border font-medium text-text-primary transition-colors"
        >
          Reset View
        </button>
        <span className="text-[11px] text-text-muted px-2 border-l border-border">
          {data.total_nodes} entities · {data.total_edges} connections
        </span>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-card/90 backdrop-blur p-2.5 rounded border border-border shadow-sm flex items-center gap-3 text-[10px] font-semibold text-text-secondary">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            <span>{type}</span>
          </div>
        ))}
      </div>

      {/* Side Node Inspector Drawer */}
      {selectedNode && (
        <div className="w-80 bg-card border-l border-border p-5 flex flex-col justify-between overflow-y-auto z-10 shadow-lg">
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span
                className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded text-white"
                style={{ backgroundColor: TYPE_COLORS[selectedNode.entity_type] || '#7A8294' }}
              >
                {selectedNode.entity_type}
              </span>
              <RingMarker ring={selectedNode.primary_ring} />
            </div>

            <h3 className="font-serif font-bold text-lg text-text-primary mb-3">
              {selectedNode.label}
            </h3>

            <div className="space-y-2 text-xs text-text-secondary mb-4">
              <div className="flex justify-between py-1 border-b border-border/50">
                <span className="text-text-muted">Total Mentions:</span>
                <span className="font-semibold text-text-primary">{selectedNode.mention_count}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/50">
                <span className="text-text-muted">Unique Outlets:</span>
                <span className="font-semibold text-text-primary">{selectedNode.source_count}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/50">
                <span className="text-text-muted">Profile Status:</span>
                <span className="font-semibold text-text-primary">
                  {selectedNode.is_profile ? 'Established Profile' : 'Candidate Entity'}
                </span>
              </div>
            </div>

            <p className="text-xs text-text-muted leading-relaxed">
              Tracked across public intelligence syndication channels. Relationships derived from co-occurrence and link analysis.
            </p>
          </div>

          <div className="pt-4 border-t border-border flex flex-col gap-2">
            <Link
              href={`/profiles/${selectedNode.id.replace('node_', '')}`}
              className="w-full text-center py-2 px-3 rounded bg-primary-navy text-white text-xs font-semibold hover:bg-primary-navy-dark transition-colors"
            >
              Open Complete Entity Profile →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

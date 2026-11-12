'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
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

const RING_BORDER_COLORS: Record<number, string> = {
  1: '#1F3A5F', // Ring 1 · India
  2: '#C2570C', // Ring 2 · Adversaries
  3: '#2F7D4F', // Ring 3 · Regional
  4: '#5B4B8A', // Ring 4 · Global
};

export const EntityGraph: React.FC<EntityGraphProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNodeItem | null>(null);
  const [neighborList, setNeighborList] = useState<Array<{ id: string; label: string; relation: string; type: string }>>([]);
  const [activeLayout, setActiveLayout] = useState<'cose' | 'concentric'>('cose');

  const runLayout = useCallback((cyInstance: cytoscape.Core, layoutName: 'cose' | 'concentric') => {
    if (layoutName === 'concentric') {
      const concentricLayout = cyInstance.layout({
        name: 'concentric',
        animate: true,
        animationDuration: 500,
        concentric: (node: any) => {
          // Ring 1 innermost (value 4), Ring 4 outermost (value 1)
          const ring = node.data('ring') || 1;
          return 5 - ring;
        },
        levelWidth: () => 1,
        padding: 50,
        spacingFactor: 1.5,
        minNodeSpacing: 60,
      } as any);
      concentricLayout.run();
    } else {
      const coseLayout = cyInstance.layout({
        name: 'cose',
        animate: true,
        animationDuration: 600,
        nodeRepulsion: () => 1200000,
        idealEdgeLength: () => 140,
        edgeElasticity: () => 100,
        nodeOverlap: 40,
        gravity: 40,
        componentSpacing: 120,
        numIter: 1000,
        padding: 40,
      } as any);
      coseLayout.run();
    }
  }, []);

  const highlightNeighbors = useCallback((node: cytoscape.NodeSingular) => {
    const cy = cyRef.current;
    if (!cy) return;

    // Reset previous styles
    cy.elements().removeClass('dimmed highlighted selected-focus');

    // Focus target
    node.addClass('selected-focus');

    // 1-hop connected edges & neighbor nodes
    const connectedEdges = node.connectedEdges();
    const neighborNodes = connectedEdges.connectedNodes();

    connectedEdges.addClass('highlighted');
    neighborNodes.addClass('highlighted');

    // Dim unrelated
    const unrelated = cy.elements().not(node).not(connectedEdges).not(neighborNodes);
    unrelated.addClass('dimmed');

    // Compute neighbor details for inspector
    const neighbors: Array<{ id: string; label: string; relation: string; type: string }> = [];
    connectedEdges.forEach((edge) => {
      const source = edge.source();
      const target = edge.target();
      const other = source.id() === node.id() ? target : source;
      neighbors.push({
        id: other.id(),
        label: other.data('label'),
        relation: edge.data('label') || 'ASSOCIATED_WITH',
        type: other.data('type'),
      });
    });
    setNeighborList(neighbors);
  }, []);

  const clearHighlight = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass('dimmed highlighted selected-focus');
    setSelectedNode(null);
    setNeighborList([]);
  }, []);

  useEffect(() => {
    if (!containerRef.current || !data.nodes.length) return;

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
            'font-size': '11px',
            'font-weight': 600,
            'font-family': 'IBM Plex Sans, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': (ele: any) => TYPE_COLORS[ele.data('type')] || '#7A8294',
            'width': (ele: any) => Math.min(46, Math.max(26, 18 + ele.data('mentions') * 0.45)),
            'height': (ele: any) => Math.min(46, Math.max(26, 18 + ele.data('mentions') * 0.45)),
            'border-width': 2.5,
            'border-color': (ele: any) => RING_BORDER_COLORS[ele.data('ring')] || '#FFFFFF',
            'text-background-opacity': 0.92,
            'text-background-color': '#FFFFFF',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'transition-property': 'opacity, border-width, border-color',
            'transition-duration': 0.25,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.8,
            'line-color': '#CBD5E1',
            'target-arrow-color': '#94A3B8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8.5px',
            'font-weight': 600,
            'color': '#475569',
            'text-rotation': 'autorotate',
            'text-background-opacity': 0.95,
            'text-background-color': '#F8FAFC',
            'text-background-padding': '2px',
            'arrow-scale': 0.9,
            'transition-property': 'opacity, line-color, width',
            'transition-duration': 0.25,
          },
        },
        {
          selector: '.selected-focus',
          style: {
            'border-width': 4,
            'border-color': '#C2570C',
            'overlay-color': '#C2570C',
            'overlay-padding': 6,
            'overlay-opacity': 0.25,
            'z-index': 999,
          },
        },
        {
          selector: '.highlighted',
          style: {
            'opacity': 1,
            'line-color': '#C2570C',
            'target-arrow-color': '#C2570C',
            'width': 2.5,
            'z-index': 888,
          },
        },
        {
          selector: '.dimmed',
          style: {
            'opacity': 0.15,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeRepulsion: () => 1200000,
        nodeOverlap: 40,
        idealEdgeLength: () => 140,
        edgeElasticity: () => 100,
        gravity: 40,
        componentSpacing: 120,
        numIter: 1000,
      },
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode(node.data('raw'));
      highlightNeighbors(node);
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        clearHighlight();
      }
    });

    cy.ready(() => {
      cy.resize();
      cy.fit(undefined, 45);
    });

    const timer = setTimeout(() => {
      cy.resize();
      cy.fit(undefined, 45);
    }, 150);

    cyRef.current = cy;

    return () => {
      clearTimeout(timer);
      cy.destroy();
    };
  }, [data, highlightNeighbors, clearHighlight]);

  const handleSelectNeighbor = (neighborId: string) => {
    const cy = cyRef.current;
    if (!cy) return;
    const targetNode = cy.getElementById(neighborId);
    if (targetNode.length) {
      setSelectedNode(targetNode.data('raw'));
      highlightNeighbors(targetNode);
      cy.animate({
        center: { eles: targetNode },
        duration: 400,
      });
    }
  };

  const handleZoomIn = () => {
    const cy = cyRef.current;
    if (cy) cy.zoom({ level: cy.zoom() * 1.25, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  };

  const handleZoomOut = () => {
    const cy = cyRef.current;
    if (cy) cy.zoom({ level: cy.zoom() * 0.8, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  };

  const handleFit = () => {
    cyRef.current?.fit(undefined, 40);
  };

  const switchLayout = (layoutName: 'cose' | 'concentric') => {
    setActiveLayout(layoutName);
    if (cyRef.current) {
      runLayout(cyRef.current, layoutName);
    }
  };

  return (
    <div className="relative w-full h-[calc(100vh-140px)] rounded-lg overflow-hidden border border-border flex bg-card shadow-sm">
      {/* Graph Viewport */}
      <div ref={containerRef} className="flex-1 h-full z-0 bg-[#FBF9F5]" />

      {/* Floating Toolbar Controls (Top-Left) */}
      <div className="absolute top-4 left-4 z-10 flex flex-wrap items-center gap-2 bg-card/95 backdrop-blur px-3 py-2 rounded-md border border-border shadow-sm">
        {/* Layout Switcher */}
        <div className="flex items-center rounded border border-border overflow-hidden bg-subtle-fill text-[11px] font-medium">
          <button
            onClick={() => switchLayout('cose')}
            className={`px-2.5 py-1 transition-colors ${
              activeLayout === 'cose'
                ? 'bg-primary-navy text-white font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Force-Directed
          </button>
          <button
            onClick={() => switchLayout('concentric')}
            className={`px-2.5 py-1 transition-colors ${
              activeLayout === 'concentric'
                ? 'bg-primary-navy text-white font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Concentric Rings
          </button>
        </div>

        {/* Zoom & Fit buttons */}
        <div className="flex items-center gap-1 border-l border-border pl-2">
          <button
            onClick={handleZoomIn}
            title="Zoom In"
            className="w-7 h-7 flex items-center justify-center rounded bg-subtle-fill hover:bg-border text-xs font-bold text-text-primary transition-colors"
          >
            +
          </button>
          <button
            onClick={handleZoomOut}
            title="Zoom Out"
            className="w-7 h-7 flex items-center justify-center rounded bg-subtle-fill hover:bg-border text-xs font-bold text-text-primary transition-colors"
          >
            −
          </button>
          <button
            onClick={handleFit}
            title="Fit Canvas"
            className="px-2 h-7 flex items-center justify-center rounded bg-subtle-fill hover:bg-border text-[11px] font-medium text-text-primary transition-colors"
          >
            Fit
          </button>
        </div>

        {/* Counter Stats */}
        <span className="text-[11px] text-text-muted px-2 border-l border-border hidden sm:inline">
          {data.total_nodes} entities · {data.total_edges} connections
        </span>
      </div>

      {/* Legend (Bottom-Left) */}
      <div className="absolute bottom-4 left-4 z-10 bg-card/95 backdrop-blur p-2.5 rounded-md border border-border shadow-sm flex flex-col gap-1.5 text-[10px] text-text-secondary">
        <span className="font-semibold text-text-primary uppercase tracking-wider text-[9px]">Ontology Entity Types</span>
        <div className="flex items-center gap-3">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span className="font-medium">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Side Node Inspector Drawer */}
      {selectedNode && (
        <div className="w-88 bg-card border-l border-border p-5 flex flex-col justify-between overflow-y-auto z-10 shadow-xl animate-in slide-in-from-right duration-200">
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

            <h3 className="font-serif font-bold text-xl text-text-primary mb-1">
              {selectedNode.label}
            </h3>
            <p className="text-[11px] text-text-muted mb-4">
              Security Ring {selectedNode.primary_ring} Strategic Asset
            </p>

            <div className="space-y-2 text-xs text-text-secondary mb-4 bg-subtle-fill/50 p-3 rounded border border-border/50">
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-text-muted">Total Mentions:</span>
                <span className="font-semibold text-text-primary">{selectedNode.mention_count}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-text-muted">Unique Outlets:</span>
                <span className="font-semibold text-text-primary">{selectedNode.source_count}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-text-muted">Profile Status:</span>
                <span className="font-semibold text-text-primary">
                  {selectedNode.is_profile ? 'Established Profile' : 'Candidate Entity'}
                </span>
              </div>
            </div>

            {/* Connected Associates / 1-Hop Relations */}
            {neighborList.length > 0 && (
              <div className="mb-4">
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-text-primary mb-2">
                  Connected Links ({neighborList.length})
                </h4>
                <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto pr-1">
                  {neighborList.map((nbr, idx) => (
                    <button
                      key={`${nbr.id}-${idx}`}
                      onClick={() => handleSelectNeighbor(nbr.id)}
                      className="flex items-center justify-between p-2 rounded bg-subtle-fill hover:bg-border text-left transition-colors border border-border/60"
                    >
                      <div className="truncate mr-2">
                        <span className="text-xs font-semibold text-text-primary block truncate">
                          {nbr.label}
                        </span>
                        <span className="text-[9px] text-text-muted uppercase tracking-wide">
                          {nbr.relation.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: TYPE_COLORS[nbr.type] || '#7A8294' }}
                        title={nbr.type}
                      />
                    </button>
                  ))}
                </div>
              </div>
            )}

            <p className="text-[11px] text-text-muted leading-relaxed">
              Attributed strictly to public intelligence feeds. Ontological links generated from entity co-occurrence & analyst verification.
            </p>
          </div>

          <div className="pt-4 border-t border-border flex flex-col gap-2 mt-4">
            <Link
              href={`/profiles/${selectedNode.id.replace('node_', '')}`}
              className="w-full text-center py-2 px-3 rounded bg-primary-navy text-white text-xs font-semibold hover:bg-primary-navy-dark transition-colors shadow-sm"
            >
              Open Complete Entity Profile →
            </Link>
            <button
              onClick={clearHighlight}
              className="w-full text-center py-1.5 text-xs text-text-muted hover:text-text-primary transition-colors"
            >
              Deselect & Clear Focus
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

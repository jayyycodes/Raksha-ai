'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MapIncident } from '@/lib/api/types';
import { ThreatLevel } from '@/components/shared/ThreatLevel';
import { RingMarker } from '@/components/shared/RingMarker';
import 'leaflet/dist/leaflet.css';

interface IncidentMapProps {
  incidents: MapIncident[];
}

export const IncidentMap: React.FC<IncidentMapProps> = ({ incidents }) => {
  const [selected, setSelected] = useState<MapIncident | null>(incidents[0] || null);

  useEffect(() => {
    // Dynamic import to guarantee client-side only execution
    let mapInstance: any = null;

    import('leaflet').then((L) => {
      const container = document.getElementById('raksha-leaflet-map');
      if (!container) return;

      // Clean up previous map instance if hot-reloaded
      if ((container as any)._leaflet_id) {
        return;
      }

      // Center around broader South Asia / Indo-Pacific geopolitical theatre
      const map = L.map('raksha-leaflet-map', {
        center: [23.5, 78.5],
        zoom: 4.5,
        zoomControl: true,
      });
      mapInstance = map;

      // OpenStreetMap public cartographic tiles (free, no API key required)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(map);

      // Line of Actual Control (LAC - Eastern Ladakh general schematic line)
      const lacCoordinates: [number, number][] = [
        [35.30, 77.90],
        [34.80, 78.15],
        [34.25, 78.33], // Galwan
        [33.72, 78.80], // Pangong Tso
        [32.70, 79.43], // Demchok
      ];
      L.polyline(lacCoordinates, {
        color: '#C2570C',
        weight: 3,
        dashArray: '6, 6',
        opacity: 0.85,
      }).addTo(map).bindTooltip('Line of Actual Control (Schematic)', { permanent: false });

      // Line of Control (LoC - J&K schematic line)
      const locCoordinates: [number, number][] = [
        [34.80, 74.20],
        [34.30, 74.10],
        [33.80, 74.15],
        [33.37, 74.30], // Poonch / Rajouri
        [32.80, 74.80],
      ];
      L.polyline(locCoordinates, {
        color: '#9B2C2C',
        weight: 3,
        dashArray: '4, 4',
        opacity: 0.85,
      }).addTo(map).bindTooltip('Line of Control (Schematic)', { permanent: false });

      // Plot incidents as custom color-coded HTML DivIcons
      incidents.forEach((inc) => {
        const color = inc.threat_level >= 8 ? '#B42318' : (inc.threat_level >= 4 ? '#B7791F' : '#2F7D4F');
        
        const customIcon = L.divIcon({
          className: 'raksha-map-pin',
          html: `
            <div style="
              width: 22px;
              height: 22px;
              background-color: ${color};
              color: white;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 11px;
              font-weight: 800;
              box-shadow: 0 2px 6px rgba(0,0,0,0.35);
              border: 2px solid #FFFFFF;
              cursor: pointer;
            ">
              ${inc.threat_level}
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const marker = L.marker([inc.latitude, inc.longitude], { icon: customIcon }).addTo(map);
        marker.on('click', () => {
          setSelected(inc);
        });
      });
    });

    return () => {
      if (mapInstance) {
        mapInstance.remove();
      }
    };
  }, [incidents]);

  return (
    <div className="relative w-full h-[calc(100vh-140px)] rounded-lg overflow-hidden border border-border flex">
      {/* Map Canvas */}
      <div id="raksha-leaflet-map" className="flex-1 h-full z-0 bg-canvas" />

      {/* Side Inspector Drawer */}
      {selected && (
        <div className="w-96 bg-card border-l border-border p-5 flex flex-col justify-between overflow-y-auto z-10 shadow-lg">
          <div>
            <div className="flex items-center justify-between gap-2 mb-3">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-subtle-fill text-text-secondary border border-border">
                {selected.region} · {selected.location_name}
              </span>
              <ThreatLevel level={selected.threat_category} num={selected.threat_level} />
            </div>

            <h3 className="font-serif font-bold text-base text-text-primary leading-snug mb-3">
              {selected.title}
            </h3>

            <div className="flex items-center gap-2 mb-4">
              <RingMarker ring={selected.ring} />
              <span className="text-xs text-text-muted">via {selected.source_name || 'OSINT Wire'}</span>
            </div>

            <div className="p-3 bg-subtle-fill/50 rounded border border-border text-xs text-text-secondary mb-3 leading-relaxed">
              <p className="font-semibold text-text-primary mb-1">Geospatial Coordinates:</p>
              <p className="font-mono text-[11px] text-primary-navy">
                Lat: {selected.latitude.toFixed(4)}° N, Lon: {selected.longitude.toFixed(4)}° E
              </p>
            </div>

            {/* Intelligence Summary Excerpt */}
            {selected.summary && (
              <div className="mb-4">
                <p className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-1">
                  Intelligence Summary:
                </p>
                <div className="p-3 bg-canvas rounded border border-border text-xs text-text-secondary leading-relaxed">
                  {selected.summary}
                </div>
              </div>
            )}

            {/* Linked Event Cluster Link */}
            {selected.event_id && (
              <div className="p-3 bg-card rounded border border-accent-saffron/40 flex flex-col gap-1.5 mb-4 shadow-sm">
                <span className="text-[10px] font-bold uppercase tracking-wider text-accent-saffron flex items-center gap-1">
                  <span>⚡</span> Linked Event Timeline
                </span>
                <p className="text-xs font-serif font-bold text-text-primary leading-tight">
                  {selected.event_title || `Event #${selected.event_id}`}
                </p>
                <Link
                  href={`/events/${selected.event_id}`}
                  className="text-[11px] font-semibold text-primary-navy hover:underline inline-flex items-center gap-1 mt-1"
                >
                  <span>View Event Timeline & Trajectory →</span>
                </Link>
              </div>
            )}

            {/* Related Entities & Actors */}
            {selected.related_entities && selected.related_entities.length > 0 && (
              <div className="mb-4">
                <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted mb-1.5">
                  Linked Entities & Actors:
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {selected.related_entities.map((ent) => (
                    <Link
                      key={ent.id}
                      href={`/profiles/${ent.id}`}
                      className="px-2 py-0.5 rounded text-[11px] font-medium bg-canvas border border-border hover:border-primary-navy text-text-primary hover:text-primary-navy transition-colors inline-flex items-center gap-1"
                      title={`View ${ent.type} profile`}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-status-green" />
                      <span>{ent.name}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-border flex flex-col gap-2">
            {selected.article_id && (
              <Link
                href={`/articles/${selected.article_id}`}
                className="w-full text-center py-2 px-3 rounded bg-primary-navy text-white text-xs font-semibold hover:bg-primary-navy-dark transition-colors"
              >
                Inspect Article & Provenance →
              </Link>
            )}
            <Link
              href={`/graph?q=${encodeURIComponent(selected.location_name)}`}
              className="w-full text-center py-2 px-3 rounded bg-subtle-fill text-text-primary text-xs font-medium hover:bg-border transition-colors flex items-center justify-center gap-1.5"
            >
              <span>Explore in Entity Graph →</span>
            </Link>
            {selected.url && (
              <a
                href={selected.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full text-center py-1.5 px-3 rounded text-text-muted text-[11px] hover:text-text-primary transition-colors flex items-center justify-center gap-1"
              >
                <span>Read Original Wire</span>
                <span className="text-xs">↗</span>
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

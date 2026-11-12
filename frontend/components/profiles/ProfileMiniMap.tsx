'use client';

import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface ProfileMiniMapProps {
  locations: Array<{ name: string; relationship: string }>;
  entityName: string;
}

const KNOWN_COORDS: Array<{ keywords: string[]; lat: number; lon: number }> = [
  { keywords: ['ladakh', 'galwan', 'eastern ladakh'], lat: 34.25, lon: 78.33 },
  { keywords: ['depsang'], lat: 35.25, lon: 77.95 },
  { keywords: ['demchok'], lat: 32.7, lon: 79.43 },
  { keywords: ['line of actual control', 'lac'], lat: 34.15, lon: 78.65 },
  { keywords: ['pangong'], lat: 33.72, lon: 78.75 },
  { keywords: ['kashmir', 'loc', 'line of control', 'rajouri', 'uri'], lat: 33.85, lon: 74.35 },
  { keywords: ['rawalpindi'], lat: 33.6, lon: 73.04 },
  { keywords: ['tawang', 'arunachal'], lat: 27.58, lon: 91.86 },
  { keywords: ['new delhi', 'indian army', 'drdo', 'indian air force'], lat: 28.61, lon: 77.21 },
];

export const ProfileMiniMap: React.FC<ProfileMiniMapProps> = ({ locations, entityName }) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;
    if (instanceRef.current) {
      instanceRef.current.remove();
      instanceRef.current = null;
    }

    const resolvedPins: Array<{ label: string; lat: number; lon: number; rel: string }> = [];
    for (const loc of locations) {
      const lower = loc.name.toLowerCase();
      const match = KNOWN_COORDS.find((c) => c.keywords.some((k) => lower.includes(k)));
      if (match) {
        resolvedPins.push({ label: loc.name, lat: match.lat, lon: match.lon, rel: loc.relationship });
      }
    }

    if (resolvedPins.length === 0) {
      const fallback = KNOWN_COORDS.find((c) =>
        c.keywords.some((k) => entityName.toLowerCase().includes(k))
      );
      if (fallback) {
        resolvedPins.push({ label: entityName, lat: fallback.lat, lon: fallback.lon, rel: 'PRIMARY_BASE' });
      } else {
        resolvedPins.push({ label: 'India / Theatre Monitor', lat: 32.5, lon: 77.5, rel: 'THEATRE_MONITORED' });
      }
    }

    const map = L.map(mapRef.current, {
      center: [resolvedPins[0].lat, resolvedPins[0].lon],
      zoom: 5,
      zoomControl: true,
      scrollWheelZoom: false,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 14,
    }).addTo(map);

    const bounds: L.LatLngTuple[] = [];
    resolvedPins.forEach((pin) => {
      bounds.push([pin.lat, pin.lon]);
      L.circleMarker([pin.lat, pin.lon], {
        radius: 7,
        fillColor: '#1F3A5F',
        color: '#FFFFFF',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9,
      })
        .bindPopup(`<strong>${pin.label}</strong><br/><span style="font-size:11px">${pin.rel}</span>`)
        .addTo(map);
    });

    if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [24, 24], maxZoom: 7 });
    }

    instanceRef.current = map;
    return () => {
      map.remove();
      instanceRef.current = null;
    };
  }, [locations, entityName]);

  return <div ref={mapRef} className="w-full h-56 rounded border border-border z-0" />;
};


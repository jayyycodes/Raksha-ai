'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchEvents } from '@/lib/api/client';
import { EventListItem } from '@/lib/api/types';
import { EventTypeTag } from '@/components/shared/EventTypeTag';
import { ThreatLevel } from '@/components/shared/ThreatLevel';
import { formatISTDate } from '@/lib/utils';

export default function EventsPage() {
  const [events, setEvents] = useState<EventListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [regionFilter, setRegionFilter] = useState('all');

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await fetchEvents({ status: statusFilter, region: regionFilter });
      setEvents(res);
      setLoading(false);
    }
    load();
  }, [statusFilter, regionFilter]);

  return (
    <div className="space-y-5">
      {/* Header & Filters */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="font-serif font-bold text-2xl text-text-primary tracking-tight">
            Threaded Event Timelines
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Multi-month situation threads linking related reports using 768-dim semantic similarity and shared entities.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs bg-card border border-border rounded px-2.5 py-1.5 text-text-primary font-medium"
          >
            <option value="all">All Statuses</option>
            <option value="ongoing">Ongoing</option>
            <option value="monitoring">Monitoring</option>
            <option value="resolved">Resolved</option>
          </select>

          <select
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
            className="text-xs bg-card border border-border rounded px-2.5 py-1.5 text-text-primary font-medium"
          >
            <option value="all">All Regions</option>
            <option value="LAC-Ladakh">LAC-Ladakh</option>
            <option value="LAC-Arunachal">LAC-Arunachal</option>
            <option value="LoC-Kashmir">LoC-Kashmir</option>
            <option value="Indian-Ocean">Indian-Ocean</option>
            <option value="Cyber">Cyber</option>
            <option value="Global-Strategic">Global-Strategic</option>
          </select>
        </div>
      </div>

      {/* Events List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-text-muted bg-card border border-border rounded-lg">
          Loading event threads...
        </div>
      ) : events.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {events.map((ev) => {
            const threatNum = Math.round(ev.threat_level || 4);
            const threatCat = threatNum >= 8 ? 'high' : threatNum >= 4 ? 'medium' : 'low';
            return (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="bg-card border border-border rounded-lg p-5 hover:border-primary-navy/60 hover:shadow-sm transition-all flex flex-col justify-between gap-3 group"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-subtle-fill text-primary-navy border border-border">
                        {ev.region}
                      </span>
                      <EventTypeTag eventType={ev.event_type} />
                    </div>
                    <ThreatLevel level={threatCat} num={threatNum} />
                  </div>

                  <h3 className="font-serif font-bold text-base text-text-primary group-hover:text-primary-navy transition-colors">
                    {ev.title}
                  </h3>

                  <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                    {ev.summary}
                  </p>
                </div>

                <div className="pt-3 border-t border-border/60 flex items-center justify-between text-[11px] text-text-muted">
                  <span>
                    <strong className="text-text-primary">{ev.article_count}</strong> linked article(s)
                  </span>
                  <span>Updated {formatISTDate(ev.last_updated_at)}</span>
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <div className="p-12 text-center text-xs text-text-muted bg-card border border-border rounded-lg">
          No ongoing event threads matched your filters.
        </div>
      )}
    </div>
  );
}


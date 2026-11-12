'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { fetchEventById } from '@/lib/api/client';
import { EventDetailData } from '@/lib/api/types';
import { EventTypeTag } from '@/components/shared/EventTypeTag';
import { RingMarker } from '@/components/shared/RingMarker';
import { ThreatLevel } from '@/components/shared/ThreatLevel';
import { formatISTDate } from '@/lib/utils';

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const eventId = parseInt(params?.id || '', 10);
  const [data, setData] = useState<EventDetailData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isNaN(eventId)) return;
    fetchEventById(eventId).then((res) => {
      setData(res);
      setLoading(false);
    });
  }, [eventId]);

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-text-muted bg-card border border-border rounded-lg">
        Loading event thread & explainable provenance...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-12 text-center space-y-3 bg-card border border-border rounded-lg">
        <p className="text-sm text-text-secondary">Event thread not found.</p>
        <Link href="/events" className="text-xs text-primary-navy font-semibold hover:underline">
          ← Back to Events
        </Link>
      </div>
    );
  }

  const { event, timeline, entities, threat_trajectory } = data;
  const threatNum = Math.round(event.threat_level || 4);
  const threatCat = threatNum >= 8 ? 'high' : threatNum >= 4 ? 'medium' : 'low';

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <Link
          href="/events"
          className="text-xs font-semibold text-text-muted hover:text-primary-navy transition-colors inline-flex items-center gap-1.5"
        >
          <span>← Back to Event Timelines</span>
        </Link>
      </div>

      {/* Header */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-primary-navy text-white">
              {event.region}
            </span>
            <EventTypeTag eventType={event.event_type} />
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary">
              Status: {event.status}
            </span>
          </div>
          <ThreatLevel level={threatCat} num={threatNum} />
        </div>

        <h1 className="font-serif font-black text-2xl text-text-primary tracking-tight">
          {event.title}
        </h1>

        <p className="text-xs text-text-secondary leading-relaxed">
          {event.summary}
        </p>

        <div className="flex flex-wrap items-center gap-4 text-[11px] text-text-muted pt-2 border-t border-border/60">
          <span>First Observed: <strong className="text-text-secondary">{formatISTDate(event.first_seen_at)}</strong></span>
          <span>Last Updated: <strong className="text-text-secondary">{formatISTDate(event.last_updated_at)}</strong></span>
          <span>Threaded Articles: <strong className="text-text-primary">{event.article_count}</strong></span>
        </div>
      </div>

      {/* Threat Trajectory + Linked Entities Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-5 shadow-sm">
          <h2 className="font-serif font-bold text-sm text-text-primary mb-3">
            Incident Threat Trajectory Over Time
          </h2>
          <div className="w-full h-48">
            {threat_trajectory.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={threat_trajectory} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E0D5" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis domain={[0, 10]} tick={{ fontSize: 10, fill: '#64748B' }} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="threat_level"
                    name="Article Threat Score"
                    stroke="#C2570C"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#1F3A5F' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-text-muted">
                No trajectory points recorded yet.
              </div>
            )}
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-3">
          <h2 className="font-serif font-bold text-sm text-text-primary">
            Linked Entities ({entities.length})
          </h2>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {entities.length > 0 ? (
              entities.map((ent, idx) => (
                <div
                  key={`${ent.name}-${idx}`}
                  className="flex items-center justify-between p-2 rounded bg-subtle-fill/60 border border-border/60 text-xs"
                >
                  <div className="truncate mr-2">
                    {ent.profile_id ? (
                      <Link
                        href={`/profiles/${ent.profile_id}`}
                        className="font-semibold text-primary-navy hover:underline"
                      >
                        {ent.name}
                      </Link>
                    ) : (
                      <span className="font-semibold text-text-primary">{ent.name}</span>
                    )}
                    <span className="text-[10px] text-text-muted block">{ent.entity_type}</span>
                  </div>
                  <span className="text-[10px] font-mono text-text-secondary shrink-0">
                    {ent.mentions}×
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-text-muted">No named entities indexed on this thread yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Chronological Article Timeline & Threading Provenance */}
      <div className="bg-card border border-border rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-serif font-bold text-base text-text-primary">
            Chronological Thread Timeline & Link Provenance ({timeline.length})
          </h2>
          <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Explainable Threading
          </span>
        </div>

        <div className="relative border-l-2 border-border ml-3 pl-5 space-y-6">
          {timeline.map((item) => (
            <div key={item.article_id} className="relative space-y-1.5">
              <div className="absolute -left-[27px] top-1.5 w-3 h-3 rounded-full bg-accent-saffron border-2 border-card" />

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[10px] font-mono font-semibold text-text-muted">
                  {formatISTDate(item.published_at)}
                </span>
                <RingMarker ring={item.ring} />
                {item.is_seed && (
                  <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-primary-navy text-white">
                    Seed Report
                  </span>
                )}
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary">
                  Method: {item.link_method} · {(item.confidence * 100).toFixed(0)}% match
                </span>
              </div>

              <Link
                href={`/articles/${item.article_id}`}
                className="font-serif font-bold text-sm text-text-primary hover:text-primary-navy transition-colors block"
              >
                {item.title}
              </Link>

              <p className="text-[11px] text-text-secondary bg-subtle-fill/40 px-2.5 py-1.5 rounded border border-border/50">
                <strong className="text-text-primary">Why linked:</strong> {item.explanation}
              </p>

              <div className="flex items-center gap-3 text-[11px] text-text-muted">
                <span>Source: <strong className="text-text-secondary">{item.source_name}</strong></span>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-navy hover:underline"
                >
                  Original Wire ↗
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


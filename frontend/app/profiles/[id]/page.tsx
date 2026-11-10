import React from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { fetchProfileById } from '@/lib/api/client';
import { RingMarker } from '@/components/shared/RingMarker';
import { ThreatLevel } from '@/components/shared/ThreatLevel';
import { EventTypeTag } from '@/components/shared/EventTypeTag';
import { formatISTDate } from '@/lib/utils';

export default async function ProfileDetailPage({ params }: { params: { id: string } }) {
  const profileId = parseInt(params.id, 10);
  if (isNaN(profileId)) notFound();

  const data = await fetchProfileById(profileId);
  if (!data) notFound();

  const { header, facts, timeline, associates } = data;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Back Link */}
      <div>
        <Link
          href="/profiles"
          className="text-xs font-semibold text-text-muted hover:text-primary-navy transition-colors inline-flex items-center gap-1.5"
        >
          <span>← Back to Profiles Directory</span>
        </Link>
      </div>

      {/* Header Card */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-primary-navy text-white">
                {header.entity_type}
              </span>
              <RingMarker ring={header.primary_ring} />
              <span className="text-xs text-text-muted">
                Tracked across {header.source_count} sources ({header.mention_count} total mentions)
              </span>
            </div>

            <h1 className="font-serif font-black text-2xl text-text-primary tracking-tight mb-2">
              {header.name}
            </h1>

            {header.aliases && header.aliases.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 mb-3">
                <span className="text-xs text-text-muted font-medium">Known Aliases / Designations:</span>
                {header.aliases.map((alias, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-0.5 rounded bg-subtle-fill border border-border text-text-secondary font-mono font-medium"
                  >
                    {alias}
                  </span>
                ))}
              </div>
            )}

            <p className="text-xs text-text-secondary leading-relaxed max-w-2xl">
              {header.description}
            </p>
          </div>

          <div className="flex md:flex-col gap-2 shrink-0">
            <Link
              href={`/graph?q=${encodeURIComponent(header.name)}`}
              className="text-xs font-semibold px-3 py-2 rounded bg-subtle-fill hover:bg-border text-text-primary border border-border transition-colors text-center"
            >
              Explore in Graph View 🕸️
            </Link>
          </div>
        </div>
      </div>

      {/* Grid: Attributed Facts & Associates */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Facts Table (2 cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-serif font-bold text-base text-text-primary">
              Attributed Facts & Claims ({facts.length})
            </h2>
            <span className="text-[10px] text-text-muted uppercase tracking-wider font-bold">
              Provenance Verified
            </span>
          </div>

          <div className="bg-card border border-border rounded-lg overflow-hidden divide-y divide-border/60">
            {facts.length > 0 ? (
              facts.map((fact) => (
                <div key={fact.id} className="p-4 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-subtle-fill text-text-secondary border border-border">
                      Claim Status: {fact.claim_status.replace('_', ' ')}
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Confidence: {(fact.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <p className="text-xs text-text-primary font-medium leading-relaxed">
                    {fact.fact}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-text-muted pt-1">
                    <span>Source: <strong className="text-text-secondary">{fact.source_name}</strong></span>
                    {fact.article_id && (
                      <Link
                        href={`/articles/${fact.article_id}`}
                        className="text-primary-navy hover:underline font-semibold"
                      >
                        Inspect Source Article →
                      </Link>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-xs text-text-muted">
                No verified profile statements logged yet.
              </div>
            )}
          </div>
        </div>

        {/* Network Associates (1 col) */}
        <div className="space-y-3">
          <h2 className="font-serif font-bold text-base text-text-primary">
            Network Associates ({associates.length})
          </h2>

          <div className="bg-card border border-border rounded-lg p-3 space-y-2">
            {associates.length > 0 ? (
              associates.map((assoc) => (
                <Link
                  key={assoc.id}
                  href={`/profiles/${assoc.id}`}
                  className="p-2.5 rounded bg-subtle-fill/50 hover:bg-subtle-fill border border-border flex items-center justify-between text-xs transition-colors block group"
                >
                  <div>
                    <span className="font-semibold text-text-primary group-hover:text-primary-navy">
                      {assoc.name}
                    </span>
                    <span className="text-[10px] text-text-muted block mt-0.5">
                      Relationship: {assoc.relationship.replace('_', ' ')}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-text-muted">
                    {(assoc.confidence * 100).toFixed(0)}%
                  </span>
                </Link>
              ))
            ) : (
              <div className="p-4 text-center text-xs text-text-muted">
                No immediate network links extracted.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chronological Timeline */}
      <div className="space-y-3">
        <h2 className="font-serif font-bold text-base text-text-primary">
          Chronological Activity Timeline ({timeline.length})
        </h2>

        <div className="bg-card border border-border rounded-lg p-5">
          {timeline.length > 0 ? (
            <div className="relative border-l-2 border-border ml-3 pl-5 space-y-5">
              {timeline.map((event, idx) => (
                <div key={idx} className="relative group">
                  {/* Bullet */}
                  <div className="absolute -left-[27px] top-1 w-3 h-3 rounded-full bg-primary-navy border-2 border-card shadow-sm" />

                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono font-semibold text-text-muted">
                      {formatISTDate(event.date)}
                    </span>
                    <EventTypeTag eventType={event.event_type} />
                    <ThreatLevel level={event.threat_level >= 8 ? 'high' : event.threat_level >= 4 ? 'medium' : 'low'} num={event.threat_level} />
                  </div>

                  <Link
                    href={`/articles/${event.article_id}`}
                    className="font-serif font-semibold text-xs text-text-primary hover:text-primary-navy transition-colors block"
                  >
                    {event.title}
                  </Link>

                  <span className="text-[11px] text-text-muted block mt-0.5">
                    Attributed via {event.source_name}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center text-xs text-text-muted">
              No historical incident timeline recorded for this entity.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

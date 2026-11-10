'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchLatestSitRep } from '@/lib/api/client';
import { SitRepData } from '@/lib/api/types';
import { RingMarker } from '@/components/shared/RingMarker';
import { ThreatLevel } from '@/components/shared/ThreatLevel';

export default function SitRepPage() {
  const [data, setData] = useState<SitRepData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await fetchLatestSitRep();
      setData(res);
      setLoading(false);
    }
    loadData();
  }, []);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header & Export Action */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-primary-navy text-white">
              Daily Brief
            </span>
            <span className="text-xs text-text-muted font-mono">
              Date: {data?.report_date || 'Current Cycle'}
            </span>
          </div>
          <h1 className="font-serif font-black text-2xl text-text-primary tracking-tight">
            National Security Situation Report (SitRep)
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Grounded intelligence brief synthesized from 40 open-source monitoring wires. Every claim carries an attributed source citation.
          </p>
        </div>

        <button
          onClick={handlePrint}
          className="text-xs font-semibold px-4 py-2 rounded bg-card hover:bg-subtle-fill border border-border text-text-primary shadow-sm transition-colors flex items-center justify-center gap-2 print:hidden"
        >
          <span>🖨️ Export / Print PDF</span>
        </button>
      </div>

      {/* Main Document Body */}
      {!loading && data ? (
        <div className="bg-card border border-border rounded-lg p-8 shadow-sm space-y-6">
          {/* Executive Summary */}
          <div className="p-4 bg-subtle-fill/40 rounded-lg border border-border">
            <h2 className="text-[11px] font-bold uppercase tracking-wider text-text-muted mb-2">
              Executive Summary
            </h2>
            <p className="font-serif text-sm text-text-primary leading-relaxed">
              {data.executive_summary}
            </p>
          </div>

          {/* Regional Theatre Assessments */}
          <div className="space-y-4">
            <h2 className="font-serif font-bold text-lg text-text-primary">
              Regional Operational Theatres
            </h2>

            <div className="space-y-3">
              {data.theatre_assessments.map((theatre, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-lg border border-border bg-card space-y-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-serif font-bold text-sm text-text-primary">
                      {theatre.theatre}
                    </h3>
                    <ThreatLevel
                      level={theatre.threat_level >= 8 ? 'high' : theatre.threat_level >= 4 ? 'medium' : 'low'}
                      num={theatre.threat_level}
                    />
                  </div>

                  <span className="text-[10px] font-bold uppercase tracking-wider text-primary-navy block">
                    Operational Status: {theatre.status}
                  </span>

                  <p className="text-xs text-text-secondary leading-relaxed font-sans">
                    {theatre.summary}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Top Threat Indicators */}
          <div className="space-y-3 pt-2">
            <h2 className="font-serif font-bold text-base text-text-primary">
              Critical Watchpoint Indicators
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {data.top_threats.map((t, idx) => (
                <div key={idx} className="p-3 bg-canvas rounded border border-border">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-text-primary">{t.theatre}</span>
                    <span className="text-xs font-mono font-bold text-primary-navy">
                      {t.score.toFixed(1)}/10
                    </span>
                  </div>
                  <span className="text-[10px] uppercase font-bold text-text-muted block">
                    Trend: {t.trend.toUpperCase()}
                  </span>
                  <p className="text-[11px] text-text-secondary mt-1 line-clamp-2">
                    {t.primary_concern}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Source Citations Index */}
          <div className="pt-6 border-t border-border space-y-3">
            <h2 className="font-serif font-bold text-base text-text-primary">
              Grounded Source Citations ({data.citations.length})
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {data.citations.map((c) => (
                <Link
                  key={c.citation_id}
                  href={`/articles/${c.article_id}`}
                  className="p-2.5 rounded bg-subtle-fill/40 hover:bg-subtle-fill border border-border flex items-start gap-2.5 transition-colors group"
                >
                  <span className="font-mono font-bold text-xs text-primary-navy shrink-0">
                    {c.citation_id}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-text-primary group-hover:text-primary-navy line-clamp-1">
                      {c.title}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[10px] text-text-muted">{c.source_name}</span>
                      <RingMarker ring={c.ring} />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="w-full py-16 bg-card border border-border rounded-lg flex flex-col items-center justify-center text-center p-6">
          <span className="text-3xl mb-2">📑</span>
          <p className="text-sm font-semibold text-text-primary">
            {loading ? 'Synthesizing grounded daily brief...' : 'No SitRep generated for today.'}
          </p>
        </div>
      )}
    </div>
  );
}

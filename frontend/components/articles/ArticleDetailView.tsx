import React from 'react';
import Link from 'next/link';
import { Article } from '@/lib/api/types';
import { RingMarker } from '@/components/shared/RingMarker';
import { ThreatLevel } from '@/components/shared/ThreatLevel';
import { SentimentLabel } from '@/components/shared/SentimentLabel';
import { EventTypeTag } from '@/components/shared/EventTypeTag';
import { LanguageTag } from '@/components/shared/LanguageTag';
import { formatIST, formatConfidence } from '@/lib/utils';

export const ArticleDetailView: React.FC<{ article: Article }> = ({ article }) => {
  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto">
      {/* Navigation Breadcrumb */}
      <div>
        <Link
          href="/articles"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-navy hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
        >
          ← Back to Article Feed
        </Link>
      </div>

      {/* Main Content Card */}
      <article className="bg-card rounded-md border border-border p-6 lg:p-8 shadow-sm flex flex-col gap-6">
        {/* Top Badges & Meta */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
          <div className="flex items-center gap-2.5 flex-wrap">
            <RingMarker ring={article.ring} />
            <span className="font-serif font-bold text-sm text-text-primary">{article.source_name}</span>
            <span className="text-text-muted">•</span>
            <LanguageTag language={article.language} translated={article.translated} />
          </div>

          <div className="text-xs text-text-muted">
            Published: <span className="text-text-primary font-medium">{formatIST(article.published_at)}</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-xl lg:text-2xl font-serif font-bold text-text-primary leading-tight">
          {article.title}
        </h1>

        {/* Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-subtle-fill/60 p-3.5 rounded border border-border">
          <div className="flex flex-wrap items-center gap-2">
            <EventTypeTag eventType={article.event_type} />
            <ThreatLevel level={article.threat_level} num={article.threat_level_num} />
            <SentimentLabel sentiment={article.sentiment} />
          </div>

          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-primary-navy hover:bg-primary-navy-dark text-white shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          >
            <span>Read Original Publisher Article</span>
            <span aria-hidden="true">↗</span>
          </a>
        </div>

        {/* Content Excerpt Section */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-text-muted">
              Reported Summary Excerpt
            </h2>
            <span className="text-[11px] text-text-muted italic">
              Copyright-safe snippet excerpted from public feed
            </span>
          </div>
          <div className="bg-canvas p-5 rounded border border-border text-sm text-text-primary leading-relaxed font-sans">
            {article.summary}
          </div>
        </div>

        {/* Translation Panel (if non-English or translated) */}
        {article.translated && article.translated_text && (
          <div className="flex flex-col gap-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-accent-saffron">
              Automated English Translation
            </h2>
            <div className="bg-[#FEF3EB]/40 p-4 rounded border border-accent-saffron/20 text-xs text-text-primary leading-relaxed">
              <p className="font-semibold text-text-secondary text-[11px] mb-1">
                Translated from {article.original_language?.toUpperCase() || 'Source Language'} via Helsinki-NLP:
              </p>
              {article.translated_text}
            </div>
          </div>
        )}

        {/* Provenance & Lineage Box */}
        <section aria-labelledby="provenance-heading" className="border-t border-border pt-6 mt-2">
          <h2 id="provenance-heading" className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-3 flex items-center gap-1.5">
            <span>🛡️</span>
            <span>Provenance & Algorithmic Lineage</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-subtle-fill/40 p-4 rounded border border-border text-xs">
            <div>
              <span className="block text-[10px] uppercase font-semibold text-text-muted">Inference Model</span>
              <span className="font-mono text-text-primary">{article.model_version || 'threat_classifier_v0:0.1.0'}</span>
            </div>

            <div>
              <span className="block text-[10px] uppercase font-semibold text-text-muted">Classification Method</span>
              <span className="font-mono text-text-primary">{article.method || 'rule_keyword_event_v0'}</span>
            </div>

            <div>
              <span className="block text-[10px] uppercase font-semibold text-text-muted">Model Confidence</span>
              <span className="font-semibold text-status-green">{formatConfidence(article.confidence)}</span>
            </div>

            <div>
              <span className="block text-[10px] uppercase font-semibold text-text-muted">Extraction Time (IST)</span>
              <span className="text-text-primary">{formatIST(article.analysed_at || article.published_at)}</span>
            </div>
          </div>

          <div className="mt-3 p-3 bg-canvas rounded border border-border text-[11px] text-text-muted flex items-start gap-2">
            <span className="font-bold text-accent-saffron">ℹ</span>
            <p>
              <strong>Open-Source Attribution Notice:</strong> This assessment was derived automatically from public syndication feeds. Claims represent reported accounts from the attributed publisher.
            </p>
          </div>
        </section>
      </article>
    </div>
  );
};


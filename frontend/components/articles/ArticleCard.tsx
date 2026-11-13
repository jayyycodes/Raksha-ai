import React from 'react';
import Link from 'next/link';
import { Article } from '@/lib/api/types';
import { RingMarker } from '@/components/shared/RingMarker';
import { ThreatLevel } from '@/components/shared/ThreatLevel';
import { SentimentLabel } from '@/components/shared/SentimentLabel';
import { EventTypeTag } from '@/components/shared/EventTypeTag';
import { LanguageTag } from '@/components/shared/LanguageTag';
import { formatRelativeTime, formatIST } from '@/lib/utils';

export const ArticleCard: React.FC<{ article: Article }> = ({ article }) => {
  return (
    <article className="bg-card rounded-md border border-border hover:border-text-muted/60 transition-all shadow-sm hover:shadow p-5 flex flex-col gap-3 group">
      {/* Top Metadata Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <RingMarker ring={article.ring} />
          <span className="font-semibold text-text-primary">{article.source_name}</span>
          <span className="text-text-muted">•</span>
          <LanguageTag language={article.language} translated={article.translated} />
        </div>
        <time
          dateTime={article.published_at}
          title={formatIST(article.published_at)}
          className="text-text-muted text-[11px]"
        >
          {formatRelativeTime(article.published_at)}
        </time>
      </div>

      {/* Headline */}
      <h2 className="text-base lg:text-lg font-serif font-bold text-text-primary leading-snug group-hover:text-primary-navy transition-colors">
        <Link
          href={`/articles/${article.id}`}
          className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy rounded"
        >
          {article.title}
        </Link>
      </h2>

      {/* Summary Excerpt */}
      <p className="text-xs lg:text-sm text-text-secondary leading-relaxed line-clamp-3">
        {article.summary}
      </p>

      {/* Strategic Bilateral Impact for India */}
      {(article.positive_impact_in || article.negative_impact_in) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs bg-bg-light/60 p-2.5 rounded border border-border/70 my-0.5">
          {article.positive_impact_in && (
            <div className="flex items-start gap-1.5">
              <span className="text-status-green font-bold text-xs shrink-0 mt-0.5" title="India Advantage">🟢</span>
              <div>
                <span className="font-semibold text-text-primary text-[11px] block">India Advantage:</span>
                <span className="text-text-secondary text-[11px] leading-tight block">{article.positive_impact_in}</span>
              </div>
            </div>
          )}
          {article.negative_impact_in && (
            <div className="flex items-start gap-1.5">
              <span className="text-status-red font-bold text-xs shrink-0 mt-0.5" title="Threat Factor">🔴</span>
              <div>
                <span className="font-semibold text-text-primary text-[11px] block">Threat Factor:</span>
                <span className="text-text-secondary text-[11px] leading-tight block">{article.negative_impact_in}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analysis Badges Footer */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-border/60 mt-1">
        <div className="flex flex-wrap items-center gap-2">
          <EventTypeTag eventType={article.event_type} />
          <ThreatLevel level={article.threat_level} num={article.threat_level_num} />
          <SentimentLabel sentiment={article.sentiment} />
        </div>

        <div className="flex items-center gap-3 text-xs">
          <Link
            href={`/articles/${article.id}`}
            className="font-semibold text-primary-navy hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
          >
            Object View →
          </Link>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-text-muted hover:text-text-primary inline-flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-navy"
            title="Open canonical source article in new tab"
          >
            <span>Source</span>
            <span aria-hidden="true">↗</span>
          </a>
        </div>
      </div>
    </article>
  );
};


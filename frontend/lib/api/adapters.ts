import { Article, SourceHealth, SystemStats, ThreatCategory, SentimentType, RingId, SourceStatusType } from './types';

/**
 * Adapter mapping backend raw JSON into clean UI domain models.
 * If backend fields change, only this file requires adjustment.
 */

export function mapThreatLevel(level: number | string | null | undefined): { category: ThreatCategory; num: number } {
  const num = typeof level === 'number' ? level : parseInt(String(level || '1'), 10) || 1;
  let category: ThreatCategory = 'low';
  if (num >= 8) category = 'high';
  else if (num >= 4) category = 'medium';
  else category = 'low';
  return { category, num };
}

export function mapSentiment(sentiment: string | null | undefined): SentimentType {
  const s = String(sentiment || '').toLowerCase();
  if (s.includes('neg') || s === 'negative' || s === 'alarming') return 'negative';
  if (s.includes('pos') || s === 'positive') return 'positive';
  return 'neutral';
}

export function mapRing(ring: number | string | null | undefined): RingId {
  const r = Number(ring);
  if (r === 2) return 2;
  if (r === 3) return 3;
  if (r === 4) return 4;
  return 1;
}

export function mapSourceStatus(status: string | null | undefined): SourceStatusType {
  const st = String(status || '').toLowerCase();
  if (st === 'failed' || st === 'error') return 'failed';
  if (st === 'stale') return 'stale';
  if (st === 'empty') return 'empty';
  return 'ok';
}

export function adaptArticle(raw: any): Article {
  const threat = mapThreatLevel(raw.threat_level);
  const lang = String(raw.language || 'en').toLowerCase();
  const isTranslated = Boolean(raw.translated_text && lang !== 'en');

  return {
    id: Number(raw.id),
    title: raw.title || 'Untitled Report',
    summary: raw.content || raw.summary || raw.translated_text || 'No summary excerpt available for this article.',
    url: raw.url || '#',
    source_name: raw.source_name || raw.source?.name || 'Open Source Wire',
    ring: mapRing(raw.ring || raw.source?.ring),
    language: lang,
    translated: isTranslated,
    original_language: isTranslated ? lang : undefined,
    published_at: raw.published_at || new Date().toISOString(),
    event_type: raw.event_type || 'general',
    sentiment: mapSentiment(raw.sentiment),
    threat_level: threat.category,
    threat_level_num: threat.num,
    confidence: typeof raw.confidence === 'number' ? raw.confidence : 0.85,
    model_version: raw.model_version || undefined,
    method: raw.method || undefined,
    analysed_at: raw.analyzed_at || raw.created_at || undefined,
    source_ids: Array.isArray(raw.source_ids) ? raw.source_ids : [],
    translated_text: raw.translated_text || undefined,
  };
}

export function adaptSourceHealth(raw: any): SourceHealth {
  return {
    id: Number(raw.id || raw.source_id),
    name: raw.name || raw.source_name || 'Monitored Source',
    ring: mapRing(raw.ring),
    language: String(raw.language || 'en').toLowerCase(),
    status: mapSourceStatus(raw.status),
    last_collected_at: raw.last_fetched || raw.last_collected_at || null,
    last_success_at: raw.last_success || raw.last_success_at || null,
    articles_today: Number(raw.articles_today || 0),
    total_articles: Number(raw.total_articles || raw.article_count || 0),
    last_error: raw.last_error || null,
    retries: Number(raw.retries || 0),
    next_run_at: raw.next_run_at || null,
    source_url: raw.url || raw.source_url || '#',
    rss_url: raw.rss_url || null,
    country: raw.country || null,
  };
}

export function adaptStats(raw: any): SystemStats {
  return {
    total_articles: Number(raw.total_articles || 0),
    todays_articles: Number(raw.todays_articles || 0),
    processed_articles: Number(raw.processed_articles || 0),
    last_scrape_at: raw.last_scrape_at || null,
    per_ring: raw.per_ring || { '1': 0, '2': 0, '3': 0, '4': 0 },
    per_source: Array.isArray(raw.per_source) ? raw.per_source : [],
    event_type_breakdown: raw.event_type_breakdown || {},
  };
}


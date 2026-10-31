export type ThreatCategory = 'low' | 'medium' | 'high';
export type SentimentType = 'negative' | 'neutral' | 'positive';
export type SourceStatusType = 'ok' | 'stale' | 'failed' | 'empty';
export type RingId = 1 | 2 | 3 | 4;

export interface Article {
  id: number;
  title: string;
  summary: string;
  url: string;
  source_name: string;
  ring: RingId;
  language: string;
  translated: boolean;
  original_language?: string;
  published_at: string;
  event_type: string;
  sentiment: SentimentType;
  threat_level: ThreatCategory;
  threat_level_num: number; // 1-10
  confidence: number;
  model_version?: string;
  method?: string;
  analysed_at?: string;
  source_ids?: number[];
  translated_text?: string;
}

export interface ArticleListResponse {
  total: number;
  page: number;
  size: number;
  articles: Article[];
}

export interface SourceHealth {
  id: number;
  name: string;
  ring: RingId;
  language: string;
  status: SourceStatusType;
  last_collected_at: string | null;
  last_success_at: string | null;
  articles_today: number;
  total_articles: number;
  last_error?: string | null;
  retries?: number;
  next_run_at?: string | null;
  source_url: string;
  rss_url?: string | null;
  country?: string | null;
}

export interface SystemStats {
  total_articles: number;
  todays_articles: number;
  processed_articles: number;
  last_scrape_at: string | null;
  per_ring: Record<string, number>;
  per_source: Array<{ id: number; name: string; count: number }>;
  event_type_breakdown: Record<string, number>;
}

export interface ArticleFilterParams {
  ring?: string;
  event_type?: string;
  language?: string;
  from?: string;
  to?: string;
  q?: string;
  sort?: 'newest' | 'oldest' | 'threat';
  page?: number;
  page_size?: number;
}

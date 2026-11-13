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
  latest_batch_articles?: number;
  processed_articles: number;
  total_sources?: number;
  active_sources?: number;
  sources_with_data?: number;
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

// ── Stage 2 Intelligence Models ─────────────────────────────────

export interface MapIncident {
  id: number;
  title: string;
  event_type: string;
  threat_level: number;
  threat_category: ThreatCategory;
  ring: RingId;
  latitude: number;
  longitude: number;
  location_name: string;
  region: string;
  article_id?: number;
  source_name?: string;
  url?: string;
  occurred_at: string;
}

export interface GraphNodeItem {
  id: string;
  label: string;
  entity_type: 'PERSON' | 'ORGANISATION' | 'LOCATION' | 'EQUIPMENT' | 'EVENT' | string;
  primary_ring: RingId;
  mention_count: number;
  source_count: number;
  is_profile: boolean;
  metadata?: Record<string, any>;
}

export interface GraphEdgeItem {
  id: string;
  source: string;
  target: string;
  link_type: string;
  confidence: number;
  article_id?: number;
  method?: string;
}

export interface GraphData {
  nodes: GraphNodeItem[];
  edges: GraphEdgeItem[];
  total_nodes: number;
  total_edges: number;
}

export interface ProfileHeaderItem {
  id: number;
  name: string;
  entity_type: string;
  aliases: string[];
  primary_ring: RingId;
  mention_count: number;
  source_count: number;
  is_profile: boolean;
  description?: string;
  first_seen_at: string;
  last_seen_at: string;
}

export interface ProfileFactItem {
  id: number;
  fact: string;
  claim_status: 'reported' | 'official_designation' | 'analyst_verified';
  article_id?: number;
  source_name?: string;
  confidence: number;
  created_at: string;
}

export interface ProfileTimelineItem {
  date: string;
  title: string;
  event_type: string;
  threat_level: number;
  article_id: number;
  source_name: string;
}

export interface ProfileDetailData {
  header: ProfileHeaderItem;
  facts: ProfileFactItem[];
  timeline: ProfileTimelineItem[];
  associates: Array<{ id: number; name: string; entity_type: string; relationship: string; confidence: number }>;
  locations: Array<{ name: string; relationship: string }>;
}

export interface MergeSuggestionItem {
  id: number;
  source_node_id: number;
  source_name: string;
  target_node_id: number;
  target_name: string;
  entity_type: string;
  similarity_score: number;
  reason: string;
  status: 'pending' | 'accepted' | 'rejected';
  reviewed_by?: string;
  reviewed_at?: string;
  created_at: string;
}

export interface SitRepCitationItem {
  citation_id: string;
  article_id: number;
  title: string;
  source_name: string;
  ring: RingId;
  threat_level: number;
}

export interface TheatreAssessmentItem {
  theatre: string;
  status: string;
  summary: string;
  threat_level: number;
}

export interface TopThreatItem {
  theatre: string;
  trend: 'rising' | 'stable' | 'falling';
  score: number;
  primary_concern: string;
}

export interface SitRepData {
  report_date: string;
  executive_summary: string;
  theatre_assessments: TheatreAssessmentItem[];
  top_threats: TopThreatItem[];
  article_count: number;
  citations: SitRepCitationItem[];
  generated_at: string;
}

export interface EventListItem {
  id: number;
  title: string;
  region: string;
  event_type: string;
  status: string;
  threat_level: number;
  first_seen_at: string;
  last_updated_at: string;
  article_count: number;
  summary: string;
}

export interface EventTimelineArticle {
  article_id: number;
  title: string;
  url: string;
  published_at: string;
  source_name: string;
  ring: RingId;
  threat_level: number;
  sentiment: string;
  link_method: string;
  confidence: number;
  is_seed: boolean;
  explanation: string;
}

export interface EventDetailData {
  event: EventListItem;
  timeline: EventTimelineArticle[];
  entities: Array<{ entity_type: string; name: string; mentions: number; profile_id?: number | null }>;
  threat_trajectory: Array<{ date: string; threat_level: number; title: string }>;
}

export interface ThreatRegionScore {
  region: string;
  score: number;
  trend: 'rising' | 'stable' | 'falling' | string;
  article_count: number;
  calculated_at: string;
}

export interface ThreatHistoryPoint {
  date: string;
  score: number;
  article_count: number;
  trend: string;
}

export interface AlertItem {
  id: number;
  alert_type: string;
  region: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical' | string;
  is_read: boolean;
  triggered_at: string;
  watchlist_id?: number | null;
  source_article_ids: number[];
}

export interface WatchlistItem {
  id: number;
  name: string;
  query_type: 'entity' | 'region' | 'keyword';
  query_value: string;
  is_active: boolean;
  created_at: string;
  alert_count: number;
  last_triggered_at?: string | null;
  recent_matches: Array<{
    article_id: number;
    title: string;
    source_name: string;
    published_at: string;
  }>;
}

export interface UnifiedSearchResponse {
  query: string;
  total_matches: number;
  articles: Array<{
    id: number;
    title: string;
    url: string;
    published_at: string;
    source_name: string;
    ring: RingId;
    event_type: string;
    threat_level: number;
  }>;
  entities: Array<{
    id: number;
    name: string;
    entity_type: string;
    primary_ring: RingId;
    mention_count: number;
    is_profile: boolean;
  }>;
  events: Array<{
    id: number;
    title: string;
    region: string;
    event_type: string;
    status: string;
    threat_level: number;
    article_count: number;
    last_updated_at: string;
  }>;
}

export interface ProfileNoteItem {
  note: string;
  analyst: string;
  created_at: string;
}


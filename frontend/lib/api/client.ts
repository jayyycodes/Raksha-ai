import { Article, ArticleFilterParams, ArticleListResponse, SourceHealth, SystemStats } from './types';
import { adaptArticle, adaptSourceHealth, adaptStats } from './adapters';
import { MOCK_ARTICLES, MOCK_SOURCES_HEALTH, MOCK_STATS, MOCK_GRAPH_DATA } from './mock-data';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

export async function fetchStats(): Promise<SystemStats> {
  if (USE_MOCK) {
    return MOCK_STATS;
  }
  try {
    const res = await fetch(`${BASE_URL}/api/stats`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return adaptStats(data);
  } catch (err) {
    console.warn('API error, falling back to mock stats:', err);
    return MOCK_STATS;
  }
}

export async function fetchArticles(params?: ArticleFilterParams): Promise<ArticleListResponse> {
  if (USE_MOCK) {
    let filtered = [...MOCK_ARTICLES];
    if (params?.ring && params.ring !== 'all') {
      const ringNum = parseInt(params.ring, 10);
      filtered = filtered.filter((a) => a.ring === ringNum);
    }
    if (params?.event_type && params.event_type !== 'all') {
      filtered = filtered.filter((a) => a.event_type.toLowerCase() === params.event_type?.toLowerCase());
    }
    if (params?.language && params.language !== 'all') {
      filtered = filtered.filter((a) => a.language.toLowerCase() === params.language?.toLowerCase());
    }
    if (params?.q) {
      const query = params.q.toLowerCase();
      filtered = filtered.filter(
        (a) => a.title.toLowerCase().includes(query) || a.summary.toLowerCase().includes(query)
      );
    }
    if (params?.sort === 'oldest') {
      filtered.sort((a, b) => new Date(a.published_at).getTime() - new Date(b.published_at).getTime());
    } else if (params?.sort === 'threat') {
      filtered.sort((a, b) => b.threat_level_num - a.threat_level_num);
    } else {
      // Default newest
      filtered.sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());
    }

    const page = params?.page || 1;
    const pageSize = params?.page_size || 10;
    const total = filtered.length;
    const offset = (page - 1) * pageSize;
    const sliced = filtered.slice(offset, offset + pageSize);

    return {
      total,
      page,
      size: pageSize,
      articles: sliced,
    };
  }

  try {
    const url = new URL(`${BASE_URL}/api/articles`);
    if (params?.ring && params.ring !== 'all') url.searchParams.set('ring', params.ring);
    if (params?.event_type && params.event_type !== 'all') url.searchParams.set('event_type', params.event_type);
    if (params?.from) url.searchParams.set('date_from', params.from);
    if (params?.page) url.searchParams.set('page', String(params.page));
    if (params?.page_size) url.searchParams.set('size', String(params.page_size));

    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const articles: Article[] = (data.articles || []).map(adaptArticle);
    return {
      total: data.total ?? articles.length,
      page: data.page ?? 1,
      size: data.size ?? 20,
      articles,
    };
  } catch (err) {
    console.warn('API error, falling back to mock articles:', err);
    return {
      total: MOCK_ARTICLES.length,
      page: 1,
      size: 10,
      articles: MOCK_ARTICLES,
    };
  }
}

export async function fetchArticleById(id: number): Promise<Article | null> {
  if (USE_MOCK) {
    const found = MOCK_ARTICLES.find((a) => a.id === id);
    return found || null;
  }

  try {
    const res = await fetch(`${BASE_URL}/api/articles/${id}`, { cache: 'no-store' });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return adaptArticle(data);
  } catch (err) {
    console.warn(`API error fetching article ${id}, fallback to mock:`, err);
    return MOCK_ARTICLES.find((a) => a.id === id) || null;
  }
}

export async function fetchSourcesHealth(): Promise<SourceHealth[]> {
  if (USE_MOCK) {
    return MOCK_SOURCES_HEALTH;
  }

  try {
    // Try health endpoint first, fallback to sources
    let res = await fetch(`${BASE_URL}/api/sources/health`, { cache: 'no-store' });
    if (!res.ok) {
      res = await fetch(`${BASE_URL}/api/sources`, { cache: 'no-store' });
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (Array.isArray(data)) {
      return data.map(adaptSourceHealth);
    }
    return MOCK_SOURCES_HEALTH;
  } catch (err) {
    console.warn('API error fetching sources health, falling back to mock:', err);
    return MOCK_SOURCES_HEALTH;
  }
}

// ── Stage 2 Client Methods ──────────────────────────────────────

export async function fetchMapIncidents(params?: { ring?: string; threat_min?: number }): Promise<import('./types').MapIncident[]> {
  try {
    const url = new URL(`${BASE_URL}/api/map/incidents`);
    if (params?.ring && params.ring !== 'all') url.searchParams.set('ring', params.ring);
    if (params?.threat_min) url.searchParams.set('threat_level_min', String(params.threat_min));

    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.incidents || [];
  } catch (err) {
    console.warn('API error fetching map incidents:', err);
    return [];
  }
}

export async function fetchGraphData(params?: { ring?: string; entity_type?: string; q?: string }): Promise<import('./types').GraphData> {
  if (USE_MOCK) {
    return MOCK_GRAPH_DATA;
  }
  try {
    const url = new URL(`${BASE_URL}/api/graph`);
    if (params?.ring && params.ring !== 'all') url.searchParams.set('ring', params.ring);
    if (params?.entity_type && params.entity_type !== 'all') url.searchParams.set('entity_type', params.entity_type);
    if (params?.q) url.searchParams.set('q', params.q);

    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.nodes && data.nodes.length > 0) {
      return data;
    }
    return MOCK_GRAPH_DATA;
  } catch (err) {
    console.warn('API error fetching graph data, falling back to initial strategic graph:', err);
    return MOCK_GRAPH_DATA;
  }
}

export async function fetchProfiles(params?: { entity_type?: string; ring?: string; q?: string }): Promise<import('./types').ProfileHeaderItem[]> {
  try {
    const url = new URL(`${BASE_URL}/api/profiles`);
    if (params?.entity_type && params.entity_type !== 'all') url.searchParams.set('entity_type', params.entity_type);
    if (params?.ring && params.ring !== 'all') url.searchParams.set('ring', params.ring);
    if (params?.q) url.searchParams.set('q', params.q);

    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API error fetching profiles:', err);
    return [];
  }
}

export async function fetchProfileById(id: number): Promise<import('./types').ProfileDetailData | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/profiles/${id}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API error fetching profile ${id}:`, err);
    return null;
  }
}

export async function fetchReviewQueue(status: string = 'pending'): Promise<import('./types').MergeSuggestionItem[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/review?status=${status}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.suggestions || [];
  } catch (err) {
    console.warn('API error fetching review queue:', err);
    return [];
  }
}

export async function submitReviewAction(id: number, action: 'accept' | 'reject' | 'split'): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/review/${id}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, analyst_name: 'lead_analyst' }),
    });
    return res.ok;
  } catch (err) {
    console.error('API error submitting review action:', err);
    return false;
  }
}

export async function fetchLatestSitRep(): Promise<import('./types').SitRepData | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/sitreps/latest`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API error fetching latest sitrep:', err);
    return null;
  }
}

export async function fetchEvents(params?: { status?: string; region?: string; event_type?: string }): Promise<import('./types').EventListItem[]> {
  try {
    const url = new URL(`${BASE_URL}/api/events`);
    if (params?.status && params.status !== 'all') url.searchParams.set('status', params.status);
    if (params?.region && params.region !== 'all') url.searchParams.set('region', params.region);
    if (params?.event_type && params.event_type !== 'all') url.searchParams.set('event_type', params.event_type);
    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.events || [];
  } catch (err) {
    console.warn('API error fetching events:', err);
    return [];
  }
}

export async function fetchEventById(id: number): Promise<import('./types').EventDetailData | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/events/${id}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API error fetching event ${id}:`, err);
    return null;
  }
}

export async function fetchThreats(): Promise<import('./types').ThreatRegionScore[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/threats`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.regions || [];
  } catch (err) {
    console.warn('API error fetching threat scores:', err);
    return [];
  }
}

export async function fetchThreatHistory(region: string, days: number = 30): Promise<import('./types').ThreatHistoryPoint[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/threats/${encodeURIComponent(region)}?days=${days}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.history || [];
  } catch (err) {
    console.warn(`API error fetching history for ${region}:`, err);
    return [];
  }
}

export async function fetchAlerts(params?: { unread_only?: boolean; severity?: string }): Promise<{ alerts: import('./types').AlertItem[]; unread_count: number }> {
  try {
    const url = new URL(`${BASE_URL}/api/alerts`);
    if (params?.unread_only) url.searchParams.set('unread_only', 'true');
    if (params?.severity && params.severity !== 'all') url.searchParams.set('severity', params.severity);
    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return { alerts: data.alerts || [], unread_count: data.unread_count || 0 };
  } catch (err) {
    console.warn('API error fetching alerts:', err);
    return { alerts: [], unread_count: 0 };
  }
}

export async function markAlertRead(id: number): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/alerts/${id}/read`, { method: 'POST' });
    return res.ok;
  } catch (err) {
    console.error('Error marking alert read:', err);
    return false;
  }
}

export async function triggerAnomalyScan(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/alerts/scan`, { method: 'POST' });
    return res.ok;
  } catch (err) {
    console.error('Error scanning anomalies:', err);
    return false;
  }
}

export async function fetchWatchlists(): Promise<import('./types').WatchlistItem[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/watchlists`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.watchlists || [];
  } catch (err) {
    console.warn('API error fetching watchlists:', err);
    return [];
  }
}

export async function createWatchlist(payload: { name: string; query_type: 'entity' | 'region' | 'keyword'; query_value: string }): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/watchlists`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.ok;
  } catch (err) {
    console.error('Error creating watchlist:', err);
    return false;
  }
}

export async function toggleWatchlist(id: number, is_active: boolean): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/watchlists/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active }),
    });
    return res.ok;
  } catch (err) {
    console.error('Error toggling watchlist:', err);
    return false;
  }
}

export async function deleteWatchlist(id: number): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/watchlists/${id}`, { method: 'DELETE' });
    return res.ok;
  } catch (err) {
    console.error('Error deleting watchlist:', err);
    return false;
  }
}

export async function fetchUnifiedSearch(query: string): Promise<import('./types').UnifiedSearchResponse | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/search?q=${encodeURIComponent(query)}&limit=6`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Unified search error:', err);
    return null;
  }
}

export async function fetchProfileNotes(profileId: number): Promise<import('./types').ProfileNoteItem[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/profiles/${profileId}/notes`, { cache: 'no-store' });
    if (!res.ok) return [];
    const data = await res.json();
    return data.notes || [];
  } catch {
    return [];
  }
}

export async function addProfileNote(profileId: number, note: string): Promise<import('./types').ProfileNoteItem[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/profiles/${profileId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note, analyst_name: 'lead_analyst' }),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.notes || [];
  } catch {
    return [];
  }
}


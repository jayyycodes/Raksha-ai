import { Article, ArticleFilterParams, ArticleListResponse, SourceHealth, SystemStats } from './types';
import { adaptArticle, adaptSourceHealth, adaptStats } from './adapters';
import { MOCK_ARTICLES, MOCK_SOURCES_HEALTH, MOCK_STATS } from './mock-data';

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

import React, { Suspense } from 'react';
import { fetchArticles, fetchStats } from '@/lib/api/client';
import { StatCard } from '@/components/shared/StatCard';
import { ArticleCard } from '@/components/articles/ArticleCard';
import { ArticleFilters } from '@/components/articles/ArticleFilters';
import { Pagination } from '@/components/shared/Pagination';
import { EmptyState } from '@/components/shared/EmptyState';
import { ArticleCardSkeleton } from '@/components/shared/LoadingSkeleton';

interface ArticlePageProps {
  searchParams: {
    ring?: string;
    event_type?: string;
    language?: string;
    from?: string;
    to?: string;
    q?: string;
    sort?: 'newest' | 'oldest' | 'threat';
    page?: string;
  };
}

async function ArticleListContent({ searchParams }: ArticlePageProps) {
  const page = parseInt(searchParams.page || '1', 10);
  const data = await fetchArticles({
    ring: searchParams.ring,
    event_type: searchParams.event_type,
    language: searchParams.language,
    from: searchParams.from,
    to: searchParams.to,
    q: searchParams.q,
    sort: searchParams.sort,
    page,
    page_size: 10,
  });

  if (data.articles.length === 0) {
    return (
      <EmptyState
        title="No intelligence records match filters"
        description="Try adjusting your ring selection, classification criteria, or keyword query to broaden search results."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between text-xs text-text-muted px-1">
        <span>
          Displaying <strong className="text-text-primary">{data.articles.length}</strong> reports on page {data.page}
        </span>
        <span>
          Total matched: <strong className="text-text-primary">{data.total}</strong>
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {data.articles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>

      <Pagination
        currentPage={data.page}
        totalItems={data.total}
        pageSize={data.size}
      />
    </div>
  );
}

export default async function ArticlesPage({ searchParams }: ArticlePageProps) {
  const stats = await fetchStats();

  return (
    <div className="flex flex-col gap-6">
      {/* Overview Stat Cards */}
      <section aria-labelledby="overview-stats-heading">
        <h2 id="overview-stats-heading" className="sr-only">
          Platform Overview Statistics
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <StatCard
            label="Total Extracted"
            value={stats.total_articles}
            subtext="across 15 sources"
            icon={<span>📰</span>}
          />
          <StatCard
            label="Received Today"
            value={stats.todays_articles}
            subtext="last 24 hours"
            icon={<span>⏱️</span>}
            accentColor="#C2570C"
          />
          <StatCard
            label="NLP Processed"
            value={stats.processed_articles}
            subtext="100% categorized"
            icon={<span>⚡</span>}
            accentColor="#2F7D4F"
          />
          <StatCard
            label="Geopolitical Rings"
            value="4 Rings"
            subtext="India · Adv · Reg · Global"
            icon={<span>🌐</span>}
            accentColor="#1F3A5F"
          />
        </div>
      </section>

      {/* Filter Bar Component */}
      <section aria-labelledby="filters-heading">
        <h2 id="filters-heading" className="sr-only">
          Filter Articles
        </h2>
        <Suspense fallback={<div className="h-28 bg-card rounded border border-border animate-pulse mb-6" />}>
          <ArticleFilters />
        </Suspense>
      </section>

      {/* Article List with Suspense Loading State */}
      <section aria-labelledby="feed-heading">
        <h2 id="feed-heading" className="text-xs font-bold uppercase tracking-wider text-text-muted mb-3 flex items-center justify-between">
          <span>Continuous Open-Source Stream</span>
          <span className="text-[11px] font-normal normal-case">Updated every 4 hours</span>
        </h2>
        <Suspense fallback={<ArticleCardSkeleton count={4} />}>
          <ArticleListContent searchParams={searchParams} />
        </Suspense>
      </section>
    </div>
  );
}


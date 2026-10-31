import React, { Suspense } from 'react';
import { fetchSourcesHealth } from '@/lib/api/client';
import { StatCard } from '@/components/shared/StatCard';
import { SourceTable } from '@/components/sources/SourceTable';
import { TableRowSkeleton } from '@/components/shared/LoadingSkeleton';

async function SourceContent() {
  const sources = await fetchSourcesHealth();

  const total = sources.length;
  const okCount = sources.filter((s) => s.status === 'ok').length;
  const staleCount = sources.filter((s) => s.status === 'stale').length;
  const failedCount = sources.filter((s) => s.status === 'failed').length;

  return (
    <div className="flex flex-col gap-6">
      {/* Health Overview Metric Cards */}
      <section aria-labelledby="source-stats-heading">
        <h2 id="source-stats-heading" className="sr-only">
          Source Health Overview
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <StatCard
            label="Monitored Outlets"
            value={total}
            subtext="Ring 1 to 4 coverage"
            icon={<span>📡</span>}
          />
          <StatCard
            label="Operational Feeds"
            value={okCount}
            subtext={`${Math.round((okCount / Math.max(1, total)) * 100)}% uptime`}
            icon={<span>🟢</span>}
            accentColor="#2F7D4F"
          />
          <StatCard
            label="Stale Feeds"
            value={staleCount}
            subtext="no updates > 4 hours"
            icon={<span>🟡</span>}
            accentColor="#B7791F"
          />
          <StatCard
            label="Failing / Retrying"
            value={failedCount}
            subtext="requires proxy rotation"
            icon={<span>🔴</span>}
            accentColor="#B42318"
          />
        </div>
      </section>

      {/* Main Table Section */}
      <section aria-labelledby="sources-table-heading">
        <div className="flex items-center justify-between mb-3 px-1">
          <h2 id="sources-table-heading" className="text-xs font-bold uppercase tracking-wider text-text-muted">
            All Monitored Sources & Feed Freshness
          </h2>
          <span className="text-[11px] text-text-muted">
            Polled on 4-hour cadence via APScheduler
          </span>
        </div>

        <SourceTable sources={sources} />
      </section>
    </div>
  );
}

export default function SourcesPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 bg-card rounded-md border border-border animate-pulse text-center text-xs text-text-muted">
          Loading source health directory...
        </div>
      }
    >
      <SourceContent />
    </Suspense>
  );
}


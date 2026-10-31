import React from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { fetchArticleById } from '@/lib/api/client';
import { ArticleDetailView } from '@/components/articles/ArticleDetailView';
import { EmptyState } from '@/components/shared/EmptyState';

interface ArticleDetailPageProps {
  params: {
    id: string;
  };
}

export default async function ArticleDetailPage({ params }: ArticleDetailPageProps) {
  const articleId = parseInt(params.id, 10);
  if (isNaN(articleId)) {
    notFound();
  }

  const article = await fetchArticleById(articleId);

  if (!article) {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <EmptyState
          title="Article Not Found"
          description={`No intelligence record was found corresponding to ID #${params.id}.`}
        />
        <div className="text-center mt-4">
          <Link
            href="/articles"
            className="text-xs font-semibold text-primary-navy hover:underline"
          >
            ← Return to Article Feed
          </Link>
        </div>
      </div>
    );
  }

  return <ArticleDetailView article={article} />;
}


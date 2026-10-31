import React from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'No intelligence articles match your currently active filters.',
  actionText,
  onAction,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center bg-card rounded-md border border-dashed border-border my-6',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-subtle-fill flex items-center justify-center text-text-muted mb-3 text-xl">
        🔍
      </div>
      <h3 className="text-base font-serif font-bold text-text-primary mb-1">{title}</h3>
      <p className="text-sm text-text-secondary max-w-md mb-4">{description}</p>
      {actionText && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-primary-navy text-white hover:bg-primary-navy-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-navy"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};


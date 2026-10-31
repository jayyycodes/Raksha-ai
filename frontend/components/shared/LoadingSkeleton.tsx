import React from 'react';
import { cn } from '@/lib/utils';

export const ArticleCardSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-card rounded-md border border-border p-5 animate-pulse flex flex-col gap-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-24 h-5 bg-subtle-fill rounded" />
              <div className="w-20 h-5 bg-subtle-fill rounded" />
            </div>
            <div className="w-28 h-4 bg-subtle-fill rounded" />
          </div>
          <div className="w-3/4 h-6 bg-subtle-fill rounded mt-1" />
          <div className="w-full h-12 bg-subtle-fill rounded" />
          <div className="flex items-center gap-3 pt-2 border-t border-border/50">
            <div className="w-20 h-5 bg-subtle-fill rounded" />
            <div className="w-16 h-5 bg-subtle-fill rounded" />
            <div className="w-24 h-5 bg-subtle-fill rounded ml-auto" />
          </div>
        </div>
      ))}
    </div>
  );
};

export const TableRowSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i} className="animate-pulse border-b border-border">
          <td className="p-3.5"><div className="w-32 h-4 bg-subtle-fill rounded" /></td>
          <td className="p-3.5"><div className="w-24 h-5 bg-subtle-fill rounded" /></td>
          <td className="p-3.5"><div className="w-12 h-4 bg-subtle-fill rounded" /></td>
          <td className="p-3.5"><div className="w-20 h-5 bg-subtle-fill rounded" /></td>
          <td className="p-3.5"><div className="w-28 h-4 bg-subtle-fill rounded" /></td>
          <td className="p-3.5"><div className="w-12 h-4 bg-subtle-fill rounded" /></td>
          <td className="p-3.5"><div className="w-16 h-4 bg-subtle-fill rounded" /></td>
        </tr>
      ))}
    </>
  );
};


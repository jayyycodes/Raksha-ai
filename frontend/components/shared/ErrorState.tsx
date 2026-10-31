import React from 'react';
import { cn } from '@/lib/utils';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load intelligence data',
  message = 'An unexpected error occurred while communicating with the platform API.',
  onRetry,
  className,
}) => {
  return (
    <div
      role="alert"
      className={cn(
        'p-6 bg-[#FEECEB] border border-[#F8C8C5] rounded-md text-center max-w-lg mx-auto my-8',
        className
      )}
    >
      <div className="w-10 h-10 rounded-full bg-[#F9D4D4] text-[#8C1B13] flex items-center justify-center mx-auto mb-3 font-bold text-lg">
        !
      </div>
      <h3 className="text-base font-serif font-bold text-[#8C1B13] mb-1">{title}</h3>
      <p className="text-xs text-[#5C1A16] mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-[#8C1B13] text-white hover:bg-[#6E140E] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#8C1B13]"
        >
          ↻ Retry Connection
        </button>
      )}
    </div>
  );
};

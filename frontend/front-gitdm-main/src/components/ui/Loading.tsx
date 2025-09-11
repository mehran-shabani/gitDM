import { cn } from '../../lib/utils';

interface LoadingProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Loading({ className, size = 'md' }: LoadingProps) {
  return (
    <div
      className={cn('flex items-center justify-center', className)}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="در حال بارگذاری"
    >
      <div
        className={cn(
          'animate-spin rounded-full border-2 border-gray-900 dark:border-gray-100 border-t-transparent',
          {
            'h-4 w-4': size === 'sm',
            'h-8 w-8': size === 'md',
            'h-12 w-12': size === 'lg',
          }
        )}
      />
      <span className="sr-only">در حال بارگذاری…</span>
    </div>
  );
}
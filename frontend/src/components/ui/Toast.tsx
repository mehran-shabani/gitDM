import { useEffect, useState, useRef } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastProps {
  toast: Toast;
  onClose: (id: string) => void;
}

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const styles = {
  success: 'bg-green-50 text-green-800 border-green-200',
  error: 'bg-red-50 text-red-800 border-red-200',
  warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  info: 'bg-blue-50 text-blue-800 border-blue-200',
};

const iconStyles = {
  success: 'text-green-400',
  error: 'text-red-400',
  warning: 'text-yellow-400',
  info: 'text-blue-400',
};

export function ToastItem({ toast, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const dismissTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const remainingTimeRef = useRef(5000);
  const startTimeRef = useRef<number | null>(null);
  const Icon = icons[toast.type];

  useEffect(() => {
    // Reset timers when toast.id changes
    remainingTimeRef.current = 5000;
    startTimeRef.current = null;
    if (dismissTimerRef.current) {
      clearTimeout(dismissTimerRef.current);
      dismissTimerRef.current = null;
    }

    // Trigger enter animation
    const showTimer = setTimeout(() => setIsVisible(true), 10);

    // Start auto-dismiss timer
    const startDismissTimer = () => {
      startTimeRef.current = Date.now();
      dismissTimerRef.current = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose(toast.id), 300);
      }, remainingTimeRef.current);
    };

    startDismissTimer();

    return () => {
      clearTimeout(showTimer);
      if (dismissTimerRef.current) {
        clearTimeout(dismissTimerRef.current);
      }
    };
  }, [toast.id, onClose]);

  const handlePause = () => {
    if (!isPaused && dismissTimerRef.current) {
      clearTimeout(dismissTimerRef.current);
      if (startTimeRef.current) {
        const elapsed = Date.now() - startTimeRef.current;
        remainingTimeRef.current = Math.max(remainingTimeRef.current - elapsed, 1000); // Keep at least 1 second
      }
      setIsPaused(true);
    }
  };

  const handleResume = () => {
    if (isPaused) {
      startTimeRef.current = Date.now();
      dismissTimerRef.current = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose(toast.id), 300);
      }, remainingTimeRef.current);
      setIsPaused(false);
    }
  };

  const handleClose = () => {
    if (dismissTimerRef.current) {
      clearTimeout(dismissTimerRef.current);
    }
    setIsVisible(false);
    setTimeout(() => onClose(toast.id), 300);
  };

  return (
    <div
      className={cn(
        'pointer-events-auto w-full max-w-sm rounded-lg border shadow-lg transition-all duration-300',
        styles[toast.type],
        isVisible
          ? 'translate-x-0 opacity-100'
          : 'translate-x-full opacity-0'
      )}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
      aria-hidden={!isVisible ? 'true' : 'false'}
      tabIndex={isVisible ? 0 : -1}
      onMouseEnter={handlePause}
      onMouseLeave={handleResume}
      onFocus={handlePause}
      onBlur={handleResume}
    >
      <div className="flex items-start p-4">
        <Icon className={cn('h-5 w-5 flex-shrink-0', iconStyles[toast.type])} />
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium">{toast.title}</p>
          {toast.message && (
            <p className="mt-1 text-sm opacity-90">{toast.message}</p>
          )}
        </div>
        <button
          type="button"
          onClick={handleClose}
          className="ml-4 inline-flex rounded-md hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          aria-label="Close notification"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
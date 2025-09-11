import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { AxiosError } from 'axios';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(...inputs));
}

export function getErrorMessage(error: unknown, fallback = 'An unexpected error occurred'): string {
  try {
    // Axios-style nested messages
    const axiosErr = error as AxiosError<any> | undefined;
    const data = axiosErr?.response?.data as any;
    const fromData =
      (typeof data === 'string' && data) ||
      data?.detail ||
      data?.message ||
      data?.error;

    if (fromData && typeof fromData === 'string') return fromData;

    const msg = (error as Error | undefined)?.message;
    if (msg) return msg;
  } catch {
    // fall through to fallback
  }
  return fallback;
}
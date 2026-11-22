import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import type { ApiError } from '../types/factcheck';

interface ErrorMessageProps {
  error: ApiError | null;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ error, onRetry }) => {
  if (!error) return null;

  return (
    <div className="bg-rose-950/40 border border-rose-900/60 rounded-2xl p-6 shadow-xl space-y-4 animate-in fade-in">
      <div className="flex items-start gap-3.5">
        <div className="p-2 rounded-xl bg-rose-900/40 text-rose-400 border border-rose-800/60 flex-shrink-0">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-bold text-rose-200">
            Fact-Checking Request Failed
          </h4>
          <p className="text-xs sm:text-sm text-rose-300/90 leading-relaxed">
            {error.message}
          </p>
          {error.status && (
            <div className="text-[11px] font-mono text-rose-400/80 pt-1">
              HTTP Status: {error.status}
            </div>
          )}
        </div>
      </div>

      {onRetry && (
        <div className="pt-2 border-t border-rose-900/40 flex justify-end">
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-900/60 hover:bg-rose-800/70 text-rose-200 text-xs font-semibold border border-rose-700/50 transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      )}
    </div>
  );
};

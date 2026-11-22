import React from 'react';
import { ExternalLink, Globe, Award, Calendar } from 'lucide-react';
import type { SourceItem } from '../types/factcheck';

interface SourcesListProps {
  sources: SourceItem[];
}

export const SourcesList: React.FC<SourcesListProps> = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return (
      <div className="text-xs text-slate-500 italic p-4 bg-slate-900/40 rounded-xl border border-slate-800">
        No external source citations available for this claim.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
          Verified Sources ({sources.length})
        </h4>
        <span className="text-[11px] text-slate-500">
          Evaluated for institutional credibility and domain reputation
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sources.map((source, idx) => (
          <div
            key={idx}
            className="bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-xl p-4 flex flex-col justify-between gap-3 shadow-sm transition"
          >
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 text-slate-200 font-semibold text-sm truncate">
                  <Globe className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                  <span className="truncate">{source.name || source.domain}</span>
                </div>
                {source.quality_score !== null && source.quality_score !== undefined && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-950 border border-indigo-700/60 text-indigo-300">
                    <Award className="w-3 h-3 text-amber-400" />
                    <span>Quality: {Math.round(source.quality_score)}</span>
                  </span>
                )}
              </div>

              <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                <span className="truncate">{source.domain}</span>
                {source.publication_date && (
                  <span className="inline-flex items-center gap-1 text-[10px] text-slate-500">
                    <Calendar className="w-3 h-3" />
                    {source.publication_date}
                  </span>
                )}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-end">
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition"
              >
                <span>Visit Source</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

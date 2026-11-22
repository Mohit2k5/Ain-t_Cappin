import React from 'react';
import { ExternalLink, Check, X, Info, HelpCircle } from 'lucide-react';
import type { EvidenceItem, EvidenceRelationship } from '../types/factcheck';

interface EvidenceCardProps {
  evidence: EvidenceItem;
  index: number;
}

interface RelationshipBadge {
  label: string;
  bg: string;
  border: string;
  text: string;
  icon: React.ElementType;
}

const RELATIONSHIP_CONFIGS: Record<EvidenceRelationship, RelationshipBadge> = {
  supports: {
    label: 'Supports Claim',
    bg: 'bg-emerald-950/70',
    border: 'border-emerald-600/50',
    text: 'text-emerald-300',
    icon: Check,
  },
  contradicts: {
    label: 'Contradicts Claim',
    bg: 'bg-rose-950/70',
    border: 'border-rose-600/50',
    text: 'text-rose-300',
    icon: X,
  },
  contextual: {
    label: 'Contextual Nuance',
    bg: 'bg-blue-950/70',
    border: 'border-blue-600/50',
    text: 'text-blue-300',
    icon: Info,
  },
  neutral: {
    label: 'Neutral',
    bg: 'bg-slate-800/70',
    border: 'border-slate-700/50',
    text: 'text-slate-300',
    icon: HelpCircle,
  },
  insufficient: {
    label: 'Insufficient',
    bg: 'bg-amber-950/70',
    border: 'border-amber-700/50',
    text: 'text-amber-300',
    icon: HelpCircle,
  },
};

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence, index }) => {
  const badgeConfig =
    RELATIONSHIP_CONFIGS[evidence.relationship] || RELATIONSHIP_CONFIGS.neutral;
  const Icon = badgeConfig.icon;
  const relevancePct = Math.round(evidence.relevance * 100);

  return (
    <div className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-lg space-y-3.5 transition duration-200">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-500">#{index + 1}</span>
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-semibold ${badgeConfig.bg} ${badgeConfig.border} ${badgeConfig.text}`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{badgeConfig.label}</span>
          </span>
        </div>

        {/* Relevance Bar */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-mono text-[11px]">Relevance:</span>
          <div className="w-16 sm:w-20 bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-indigo-500 h-full rounded-full"
              style={{ width: `${relevancePct}%` }}
            />
          </div>
          <span className="font-mono text-slate-300 text-[11px] font-semibold">
            {relevancePct}%
          </span>
        </div>
      </div>

      {/* Extracted Passage */}
      <blockquote className="text-slate-200 text-xs sm:text-sm leading-relaxed border-l-2 border-indigo-500/40 pl-3 italic bg-slate-950/40 p-2.5 rounded-r-lg">
        "{evidence.text}"
      </blockquote>

      {/* Source Citation */}
      <div className="flex items-center justify-between pt-1 text-xs">
        <span className="text-slate-400 truncate max-w-[200px] sm:max-w-xs font-medium">
          Source: <span className="text-slate-300">{evidence.source}</span>
        </span>
        {evidence.url ? (
          <a
            href={evidence.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition"
          >
            <span>View Citation</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        ) : (
          <span className="text-slate-500 italic">No URL provided</span>
        )}
      </div>
    </div>
  );
};

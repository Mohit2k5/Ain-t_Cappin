import React from 'react';
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  Clock,
  AlertOctagon,
  Info,
} from 'lucide-react';
import type { VerdictType } from '../types/factcheck';

interface VerdictCardProps {
  verdict: VerdictType;
  claim: string;
  explanation: string;
  limitations?: string[];
}

interface VerdictConfig {
  label: string;
  badgeBg: string;
  badgeBorder: string;
  badgeText: string;
  cardBorder: string;
  icon: React.ElementType;
  tagline: string;
}

const VERDICT_CONFIGS: Record<VerdictType, VerdictConfig> = {
  True: {
    label: 'Verified True',
    badgeBg: 'bg-emerald-950/80',
    badgeBorder: 'border-emerald-500/60',
    badgeText: 'text-emerald-400',
    cardBorder: 'border-emerald-500/40',
    icon: CheckCircle2,
    tagline: 'Directly supported by credible empirical evidence and consensus sources.',
  },
  False: {
    label: 'False / Debunked',
    badgeBg: 'bg-rose-950/80',
    badgeBorder: 'border-rose-500/60',
    badgeText: 'text-rose-400',
    cardBorder: 'border-rose-500/40',
    icon: XCircle,
    tagline: 'Contradicted by authoritative evidence, verified facts, or institutional data.',
  },
  'Partially True': {
    label: 'Partially True',
    badgeBg: 'bg-amber-950/80',
    badgeBorder: 'border-amber-500/60',
    badgeText: 'text-amber-300',
    cardBorder: 'border-amber-500/40',
    icon: AlertTriangle,
    tagline: 'Contains factual elements alongside unverified, exaggerated, or missing nuances.',
  },
  Misleading: {
    label: 'Misleading Context',
    badgeBg: 'bg-orange-950/80',
    badgeBorder: 'border-orange-500/60',
    badgeText: 'text-orange-400',
    cardBorder: 'border-orange-500/40',
    icon: AlertOctagon,
    tagline: 'Technically contains isolated facts presented out of context to distort the truth.',
  },
  Unverified: {
    label: 'Unverified',
    badgeBg: 'bg-slate-800/80',
    badgeBorder: 'border-slate-600/60',
    badgeText: 'text-slate-300',
    cardBorder: 'border-slate-700/50',
    icon: HelpCircle,
    tagline: 'Insufficient credible evidence found across retrieved sources to establish certainty.',
  },
  Outdated: {
    label: 'Outdated Information',
    badgeBg: 'bg-purple-950/80',
    badgeBorder: 'border-purple-500/60',
    badgeText: 'text-purple-300',
    cardBorder: 'border-purple-500/40',
    icon: Clock,
    tagline: 'Previously accurate or relevant, but superseded by newer developments or data.',
  },
};

export const VerdictCard: React.FC<VerdictCardProps> = ({
  verdict,
  claim,
  explanation,
  limitations = [],
}) => {
  const config = VERDICT_CONFIGS[verdict] || VERDICT_CONFIGS.Unverified;
  const Icon = config.icon;

  return (
    <div
      className={`bg-slate-900/95 border ${config.cardBorder} rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-md space-y-6 transition duration-200`}
    >
      {/* Top Banner / Verdict Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
            Final Verdict Assessment
          </span>
          <div className="flex items-center gap-3">
            <div
              className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border ${config.badgeBg} ${config.badgeBorder} ${config.badgeText} text-sm font-bold shadow-md`}
            >
              <Icon className="w-4 h-4" />
              <span>{config.label}</span>
            </div>
            <span className="text-xs text-slate-400 hidden md:inline">
              {config.tagline}
            </span>
          </div>
        </div>
      </div>

      {/* Claim Recap */}
      <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
        <div className="text-[11px] font-mono uppercase text-slate-400 mb-1">
          Evaluated Claim:
        </div>
        <blockquote className="text-slate-200 font-medium text-base sm:text-lg italic">
          "{claim}"
        </blockquote>
      </div>

      {/* Detailed Grounded Explanation */}
      <div className="space-y-2">
        <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
          Evidence-Grounded Explanation
        </h4>
        <p className="text-slate-200 text-sm sm:text-base leading-relaxed whitespace-pre-line bg-slate-950/40 p-4 rounded-xl border border-slate-800/50">
          {explanation}
        </p>
      </div>

      {/* Limitations and Caveats */}
      {limitations.length > 0 && (
        <div className="bg-amber-950/30 border border-amber-900/50 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold uppercase tracking-wider">
            <Info className="w-4 h-4 text-amber-400" />
            <span>Limitations & Verification Caveats</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-xs text-amber-200/90 pl-1">
            {limitations.map((limitation, idx) => (
              <li key={idx}>{limitation}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

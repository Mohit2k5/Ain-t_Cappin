import React from 'react';
import { Gauge, CheckCircle, HelpCircle } from 'lucide-react';
import type { ConfidenceDetail, AssessmentAgreement } from '../types/factcheck';

interface ConfidenceIndicatorProps {
  confidence: ConfidenceDetail;
  agreement: AssessmentAgreement;
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  confidence,
  agreement,
}) => {
  const score = Math.round(confidence.score);

  // Confidence color band
  const getBandStyles = (level: string) => {
    switch (level) {
      case 'High':
        return {
          textColor: 'text-emerald-400',
          barColor: 'bg-emerald-500',
          badgeBg: 'bg-emerald-950/70 border-emerald-500/50',
        };
      case 'Moderate':
        return {
          textColor: 'text-amber-400',
          barColor: 'bg-amber-500',
          badgeBg: 'bg-amber-950/70 border-amber-500/50',
        };
      case 'Low':
        return {
          textColor: 'text-orange-400',
          barColor: 'bg-orange-500',
          badgeBg: 'bg-orange-950/70 border-orange-500/50',
        };
      default:
        return {
          textColor: 'text-rose-400',
          barColor: 'bg-rose-500',
          badgeBg: 'bg-rose-950/70 border-rose-500/50',
        };
    }
  };

  const styles = getBandStyles(confidence.level);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Gauge className="w-5 h-5 text-indigo-400" />
          <h4 className="text-sm font-semibold text-slate-200">
            Confidence & Consensus Metrics
          </h4>
        </div>
        <div
          className={`text-xs font-mono font-bold px-3 py-1 rounded-full border ${styles.badgeBg} ${styles.textColor}`}
        >
          {confidence.level} Confidence ({score}%)
        </div>
      </div>

      {/* Visual Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-slate-400 font-mono">
          <span>Overall Confidence Calibration</span>
          <span className={`font-bold ${styles.textColor}`}>{score} / 100</span>
        </div>
        <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${styles.barColor}`}
            style={{ width: `${Math.max(score, 5)}%` }}
          />
        </div>
      </div>

      {/* Grid of Key Diagnostic Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
        {/* Self-Consistency Agreement */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Perspective Agreement:</span>
            <span className="font-mono text-emerald-400 font-bold">
              {Math.round(agreement.percentage)}%
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-slate-300">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>
              {agreement.agreeing} of {agreement.total} independent analytical perspectives in agreement
            </span>
          </div>
        </div>

        {/* Grounding Explanation */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
            <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
            <span>Confidence Formula (R, S, A, M):</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-snug">
            {confidence.reason}
          </p>
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Search, Database, Scale, ShieldCheck, CheckCircle2 } from 'lucide-react';

const PIPELINE_STAGES = [
  {
    id: 1,
    title: 'Claim Analysis & Decomposition',
    description: 'Normalizing text, extracting entities, classifying category, generating targeted queries',
    icon: Search,
  },
  {
    id: 2,
    title: 'Live Evidence Web Retrieval',
    description: 'Gathering documents from web search providers, cleaning HTML, evaluating source reputation',
    icon: Database,
  },
  {
    id: 3,
    title: 'FAISS Vector RAG & Ranking',
    description: 'Chunking text into passages, generating embeddings, executing cosine similarity retrieval',
    icon: Database,
  },
  {
    id: 4,
    title: 'Multi-Perspective Cross-Checking',
    description: 'Testing empirical grounding, falsification analysis, and institutional consensus',
    icon: Scale,
  },
  {
    id: 5,
    title: 'Confidence Calibration & Verdict Synthesis',
    description: 'Calculating multi-factor confidence formula (R, S, A, M) and producing explainable verdict',
    icon: ShieldCheck,
  },
];

export const FactCheckLoading: React.FC = () => {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStage((prev) => (prev < PIPELINE_STAGES.length - 1 ? prev + 1 : prev));
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900/90 border border-indigo-500/30 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-indigo-950/40 backdrop-blur-md space-y-6 animate-in fade-in duration-300">
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/70 border border-indigo-800 text-indigo-300 text-xs font-mono uppercase tracking-wider animate-pulse">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
          RAG Fact-Checking Pipeline In Progress
        </div>
        <h3 className="text-xl font-bold text-white tracking-tight">
          Retrieving & Verifying Evidence
        </h3>
        <p className="text-slate-400 text-xs max-w-md mx-auto">
          Searching real-time sources, extracting document context, and running vector similarity checks without pretrained hallucinations.
        </p>
      </div>

      <div className="space-y-3 pt-2 max-w-xl mx-auto">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isDone = idx < activeStage;
          const isCurrent = idx === activeStage;
          const Icon = stage.icon;

          return (
            <div
              key={stage.id}
              className={`flex items-start gap-3.5 p-3.5 rounded-xl border transition-all duration-300 ${
                isCurrent
                  ? 'bg-indigo-950/50 border-indigo-500/60 shadow-lg shadow-indigo-950/50'
                  : isDone
                  ? 'bg-slate-950/60 border-slate-800/80 opacity-90'
                  : 'bg-slate-950/30 border-slate-900/60 opacity-40'
              }`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {isDone ? (
                  <div className="w-7 h-7 rounded-full bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                ) : isCurrent ? (
                  <div className="w-7 h-7 rounded-full bg-indigo-900/80 border border-indigo-400 flex items-center justify-center text-indigo-300 animate-pulse">
                    <Icon className="w-4 h-4 animate-spin" />
                  </div>
                ) : (
                  <div className="w-7 h-7 rounded-full bg-slate-800/50 border border-slate-700/40 flex items-center justify-center text-slate-500">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4
                    className={`text-sm font-semibold tracking-tight ${
                      isCurrent ? 'text-indigo-200' : isDone ? 'text-slate-300' : 'text-slate-500'
                    }`}
                  >
                    {stage.title}
                  </h4>
                  {isCurrent && (
                    <span className="text-[10px] font-mono text-indigo-400 bg-indigo-900/60 px-2 py-0.5 rounded-full border border-indigo-700/60 animate-pulse">
                      Processing...
                    </span>
                  )}
                  {isDone && (
                    <span className="text-[10px] font-mono text-emerald-400">Complete</span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{stage.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

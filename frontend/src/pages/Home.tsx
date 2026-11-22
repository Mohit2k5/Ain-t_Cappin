import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  RefreshCw,
  Search,
  Database,
  Scale,
  RotateCcw,
  BookOpen,
} from 'lucide-react';
import { checkHealth, factCheckClaim } from '../services/api';
import type { FactCheckResponse, ApiError } from '../types/factcheck';

import { ClaimInput } from '../components/ClaimInput';
import { FactCheckLoading } from '../components/FactCheckLoading';
import { VerdictCard } from '../components/VerdictCard';
import { EvidenceCard } from '../components/EvidenceCard';
import { SourcesList } from '../components/SourcesList';
import { ConfidenceIndicator } from '../components/ConfidenceIndicator';
import { ErrorMessage } from '../components/ErrorMessage';
import { ProcessingMetadataView } from '../components/ProcessingMetadataView';

const CURRENT_YEAR = new Date().getFullYear();

export const Home: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [isLoading, setIsLoading] = useState(false);
  const [lastSubmittedClaim, setLastSubmittedClaim] = useState<string>('');
  const [result, setResult] = useState<FactCheckResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setBackendStatus('connected'))
      .catch(() => setBackendStatus('disconnected'));
  }, []);

  const handleFactCheck = async (claimText: string) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setLastSubmittedClaim(claimText);

    try {
      const response = await factCheckClaim({ claim: claimText });
      setResult(response);
    } catch (err: unknown) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setLastSubmittedClaim('');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Sticky Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600/20 p-2 rounded-xl border border-indigo-500/30 text-indigo-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                Ain't Cappin
              </span>
              <span className="ml-2 text-xs font-mono uppercase px-2 py-0.5 rounded-full bg-slate-800 text-indigo-400 border border-slate-700">
                FAISS RAG v1.0
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            <span className="text-slate-400 hidden sm:inline">Backend API:</span>
            {backendStatus === 'checking' && (
              <span className="inline-flex items-center text-amber-400">
                <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> Checking
              </span>
            )}
            {backendStatus === 'connected' && (
              <span className="inline-flex items-center text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-1.5" /> Online
              </span>
            )}
            {backendStatus === 'disconnected' && (
              <span className="inline-flex items-center text-rose-400">
                <span className="w-2 h-2 rounded-full bg-rose-500 mr-1.5" /> Offline
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-4xl w-full mx-auto px-4 py-8 sm:py-12 flex-1 space-y-8">
        {/* Hero Title Section */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/60 border border-indigo-800/50 text-indigo-300 text-xs font-semibold tracking-wide uppercase">
            Retrieve &bull; Ground &bull; Verify
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Stop Guessing. <span className="text-indigo-400">Verify Evidence.</span>
          </h1>
          <p className="text-slate-400 text-xs sm:text-sm max-w-xl mx-auto leading-relaxed">
            Retrieves live web documents, indexes passages in FAISS vector space, cross-checks multiple analytical angles, and computes calibrated confidence scores.
          </p>
        </div>

        {/* Input Box (always accessible unless showing results where user can reset or check new claim) */}
        <section aria-label="Claim Submission">
          <ClaimInput onSubmit={handleFactCheck} isLoading={isLoading} />
        </section>

        {/* Pipeline Execution Animation */}
        {isLoading && (
          <section aria-label="Verification in Progress">
            <FactCheckLoading />
          </section>
        )}

        {/* Error Notification */}
        {error && (
          <section aria-label="Error Status">
            <ErrorMessage
              error={error}
              onRetry={lastSubmittedClaim ? () => handleFactCheck(lastSubmittedClaim) : undefined}
            />
          </section>
        )}

        {/* Full Verification Results View */}
        {result && !isLoading && (
          <section aria-label="Fact Check Results" className="space-y-6 animate-in fade-in duration-300">
            {/* Header Action Bar */}
            <div className="flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-bold text-slate-100 flex items-center gap-2">
                <span>Verification Results</span>
              </h2>
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 px-3 py-1.5 rounded-lg bg-indigo-950/50 border border-indigo-800/60 transition cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Verify Another Claim</span>
              </button>
            </div>

            {/* Final Verdict Card */}
            <VerdictCard
              verdict={result.verdict}
              claim={result.claim}
              explanation={result.explanation}
              limitations={result.limitations}
            />

            {/* Calibrated Confidence & Agreement Indicator */}
            <ConfidenceIndicator
              confidence={result.confidence}
              agreement={result.assessment_agreement}
            />

            {/* Evidence Passages Retrieved via FAISS RAG */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs uppercase font-semibold text-slate-400 tracking-wider flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" />
                  <span>Grounding Evidence Passages ({result.evidence.length})</span>
                </h3>
                <span className="text-[11px] text-slate-500 font-mono">
                  Ranked by FAISS vector similarity
                </span>
              </div>

              {result.evidence.length > 0 ? (
                <div className="space-y-3">
                  {result.evidence.map((item, idx) => (
                    <EvidenceCard key={idx} evidence={item} index={idx} />
                  ))}
                </div>
              ) : (
                <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-800 text-xs text-slate-500 italic">
                  No distinct evidence passages were extracted for this claim.
                </div>
              )}
            </div>

            {/* Citations & Source Credibility List */}
            <SourcesList sources={result.sources} />

            {/* Collapsible Telemetry & Metadata */}
            <ProcessingMetadataView metadata={result.processing_metadata} />
          </section>
        )}

        {/* Feature Explanation Cards (Shown when idle or at bottom) */}
        {!result && !isLoading && (
          <section className="space-y-4 pt-4">
            <h3 className="text-center text-xs font-semibold text-slate-500 uppercase tracking-widest">
              Core Architectural Guarantees
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-slate-900/40 border border-slate-800/60 p-4 rounded-xl space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-950 flex items-center justify-center text-indigo-400 border border-indigo-900">
                  <Search className="w-4 h-4" />
                </div>
                <h4 className="font-semibold text-slate-200 text-sm">Real-Time Web Search</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Queries web search engines to retrieve live, current documents without relying on frozen parametric training cutoff dates.
                </p>
              </div>

              <div className="bg-slate-900/40 border border-slate-800/60 p-4 rounded-xl space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-950 flex items-center justify-center text-indigo-400 border border-indigo-900">
                  <Database className="w-4 h-4" />
                </div>
                <h4 className="font-semibold text-slate-200 text-sm">Vector RAG Grounding</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Chunks articles, embeds with sentence-transformers, and executes in-memory FAISS similarity retrieval to isolate facts.
                </p>
              </div>

              <div className="bg-slate-900/40 border border-slate-800/60 p-4 rounded-xl space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-950 flex items-center justify-center text-indigo-400 border border-indigo-900">
                  <Scale className="w-4 h-4" />
                </div>
                <h4 className="font-semibold text-slate-200 text-sm">Self-Consistency Scored</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Evaluates empirical grounding, falsification, and consensus to produce calibrated confidence and zero-hallucination citations.
                </p>
              </div>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>&copy; {CURRENT_YEAR} Ain't Cappin &bull; AI Fact-Checking</span>
          <span className="text-slate-400 font-mono">React 19 + TypeScript + FastAPI + FAISS</span>
        </div>
      </footer>
    </div>
  );
};

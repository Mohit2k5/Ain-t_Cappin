import React, { useState } from 'react';
import { ArrowRight, Sparkles, X, AlertCircle } from 'lucide-react';

interface ClaimInputProps {
  onSubmit: (claim: string) => void;
  isLoading: boolean;
}

const SAMPLE_CLAIMS = [
  {
    category: 'Science',
    text: 'NASA scientists confirmed evidence of liquid water flowing on modern Mars.',
  },
  {
    category: 'Health',
    text: 'Drinking baking soda mixed with lemon water permanently cures cancer.',
  },
  {
    category: 'Finance',
    text: 'The Federal Reserve raised interest rates to combat rising consumer inflation.',
  },
  {
    category: 'General',
    text: 'The Great Wall of China is clearly visible from low Earth orbit with the naked eye.',
  },
];

export const ClaimInput: React.FC<ClaimInputProps> = ({ onSubmit, isLoading }) => {
  const [claim, setClaim] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = claim.trim();
    if (trimmed.length < 3) {
      setValidationError('Claim must contain at least 3 characters.');
      return;
    }
    if (trimmed.length > 1000) {
      setValidationError('Claim cannot exceed 1000 characters.');
      return;
    }
    setValidationError(null);
    onSubmit(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };

  const handleSelectSample = (sampleText: string) => {
    setClaim(sampleText);
    setValidationError(null);
  };

  const handleClear = () => {
    setClaim('');
    setValidationError(null);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 sm:p-7 shadow-2xl shadow-indigo-950/30 backdrop-blur-md space-y-5">
      <div className="flex items-center justify-between">
        <label htmlFor="claim-textarea" className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>Enter Claim or Social Media Statement</span>
        </label>
        {claim.length > 0 && !isLoading && (
          <button
            type="button"
            onClick={handleClear}
            className="text-xs text-slate-400 hover:text-slate-200 inline-flex items-center gap-1 transition"
          >
            <X className="w-3.5 h-3.5" /> Clear
          </button>
        )}
      </div>

      <div className="relative">
        <textarea
          id="claim-textarea"
          rows={3}
          value={claim}
          disabled={isLoading}
          onChange={(e) => {
            setClaim(e.target.value);
            if (validationError) setValidationError(null);
          }}
          onKeyDown={handleKeyDown}
          placeholder="e.g. Health officials announced a new vaccine requirement for all international travelers..."
          className={`w-full bg-slate-950 border rounded-xl p-4 text-slate-100 placeholder-slate-500 focus:outline-none transition duration-200 resize-none text-base leading-relaxed ${
            validationError
              ? 'border-rose-500/80 focus:ring-2 focus:ring-rose-500/40'
              : 'border-slate-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30'
          } ${isLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
        />
        <div className="absolute right-3 bottom-3 text-xs font-mono text-slate-500 pointer-events-none">
          {claim.length}/1000
        </div>
      </div>

      {validationError && (
        <div className="flex items-center gap-2 text-rose-400 text-xs bg-rose-950/40 border border-rose-900/50 rounded-lg p-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-1">
        <div className="text-xs text-slate-400 hidden sm:block">
          Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">Enter</kbd> to submit
        </div>
        <button
          type="button"
          disabled={isLoading || claim.trim().length < 3}
          onClick={() => handleSubmit()}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-7 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/30 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          <span>{isLoading ? 'Verifying Claim...' : 'Fact-Check Claim'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Quick Sample Claims */}
      <div className="pt-4 border-t border-slate-800/80">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2.5">
          Or try a sample claim:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {SAMPLE_CLAIMS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isLoading}
              onClick={() => handleSelectSample(sample.text)}
              className="text-left text-xs bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white p-2.5 rounded-lg border border-slate-700/60 transition group flex items-start gap-2 disabled:opacity-50"
            >
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-700 text-indigo-300 border border-slate-600 flex-shrink-0">
                {sample.category}
              </span>
              <span className="line-clamp-2 text-slate-300 group-hover:text-indigo-200">
                "{sample.text}"
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

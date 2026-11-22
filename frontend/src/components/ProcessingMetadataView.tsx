import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Cpu, Hash, Layers } from 'lucide-react';
import type { ProcessingMetadata } from '../types/factcheck';

interface ProcessingMetadataViewProps {
  metadata?: ProcessingMetadata;
}

export const ProcessingMetadataView: React.FC<ProcessingMetadataViewProps> = ({ metadata }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!metadata || Object.keys(metadata).length === 0) return null;

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-850/50 transition cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-400" />
          <span>Execution Telemetry & Pipeline Metadata</span>
        </div>
        <div className="flex items-center gap-1">
          <span>{isOpen ? 'Hide Details' : 'Show Details'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-5 border-t border-slate-800/80 bg-slate-950/60 space-y-4 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {metadata.category && (
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block font-mono">Category</span>
                <span className="font-semibold text-slate-200">{metadata.category}</span>
              </div>
            )}
            {metadata.total_documents_processed !== undefined && (
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block font-mono">Docs Scraped</span>
                <span className="font-semibold text-slate-200">{metadata.total_documents_processed}</span>
              </div>
            )}
            {metadata.total_chunks_indexed !== undefined && (
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block font-mono">Chunks Indexed</span>
                <span className="font-semibold text-slate-200">{metadata.total_chunks_indexed}</span>
              </div>
            )}
            {metadata.processing_time_ms !== undefined && (
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block font-mono">Pipeline Latency</span>
                <span className="font-semibold text-slate-200">{metadata.processing_time_ms} ms</span>
              </div>
            )}
          </div>

          {metadata.entities && metadata.entities.length > 0 && (
            <div>
              <span className="text-[11px] font-mono text-slate-400 block mb-1.5 flex items-center gap-1">
                <Hash className="w-3 h-3 text-indigo-400" /> Extracted Entities:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {metadata.entities.map((entity, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px] font-mono border border-slate-700/60"
                  >
                    {entity}
                  </span>
                ))}
              </div>
            </div>
          )}

          {metadata.search_queries && metadata.search_queries.length > 0 && (
            <div>
              <span className="text-[11px] font-mono text-slate-400 block mb-1.5 flex items-center gap-1">
                <Layers className="w-3 h-3 text-indigo-400" /> Generated Search Queries:
              </span>
              <ul className="list-disc list-inside space-y-1 text-slate-300 font-mono text-[11px]">
                {metadata.search_queries.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 font-mono pt-2 border-t border-slate-800/60">
            {metadata.embedding_model && <span>Embedding: {metadata.embedding_model}</span>}
            {metadata.llm_model && <span>Synthesizer: {metadata.llm_model}</span>}
          </div>
        </div>
      )}
    </div>
  );
};

export type VerdictType =
  | 'True'
  | 'False'
  | 'Partially True'
  | 'Misleading'
  | 'Unverified'
  | 'Outdated';

export type ConfidenceBand = 'High' | 'Moderate' | 'Low' | 'Very Low';

export type EvidenceRelationship =
  | 'supports'
  | 'contradicts'
  | 'contextual'
  | 'neutral'
  | 'insufficient';

export interface EvidenceItem {
  text: string;
  source: string;
  url: string;
  relationship: EvidenceRelationship;
  relevance: number; // 0.0 - 1.0
}

export interface SourceItem {
  name: string;
  domain: string;
  url: string;
  publication_date?: string | null;
  quality_score?: number | null; // 0 - 100
}

export interface ConfidenceDetail {
  level: ConfidenceBand;
  score: number; // 0 - 100
  reason: string;
}

export interface AssessmentAgreement {
  agreeing: number;
  total: number;
  percentage: number; // 0 - 100
}

export interface FactCheckRequest {
  claim: string;
  language?: string;
  context?: string;
}

export interface ProcessingMetadata {
  category?: string;
  entities?: string[];
  search_queries?: string[];
  total_sources_found?: number;
  total_documents_processed?: number;
  total_chunks_indexed?: number;
  retrieved_passages_count?: number;
  embedding_model?: string;
  llm_model?: string;
  processing_time_ms?: number;
  [key: string]: unknown;
}

export interface FactCheckResponse {
  claim: string;
  verdict: VerdictType;
  explanation: string;
  evidence: EvidenceItem[];
  sources: SourceItem[];
  confidence: ConfidenceDetail;
  assessment_agreement: AssessmentAgreement;
  limitations: string[];
  processing_metadata?: ProcessingMetadata;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment?: string;
}

export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

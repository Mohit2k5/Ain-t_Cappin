from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_url: str = Field(..., description="Originating document URL")
    document_title: str = Field(..., description="Document title")
    domain: str = Field(..., description="Source domain name")
    text: str = Field(..., description="Text content of the passage chunk")
    chunk_index: int = Field(0, description="Sequential index within the document")
    character_length: int = Field(0, description="Character count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags")


class RetrievedPassage(BaseModel):
    chunk: DocumentChunk = Field(..., description="Retrieved passage chunk")
    score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0.0 to 1.0)")
    perspective: str = Field("neutral", description="Retrieval perspective: neutral, supporting, refuting")


class RAGContext(BaseModel):
    claim: str = Field(..., description="Original user claim")
    passages: List[RetrievedPassage] = Field(default_factory=list, description="Retrieved top passages")
    formatted_context: str = Field(..., description="Assembled grounded context for LLM prompt")
    unique_sources: List[str] = Field(default_factory=list, description="List of unique source URLs")


class GroundedAssessment(BaseModel):
    claim: str = Field(..., description="The verified claim")
    preliminary_verdict: str = Field(..., description="Evidence-grounded preliminary verdict")
    reasoning: str = Field(..., description="Evidence analysis summary")
    supporting_citations: List[str] = Field(default_factory=list, description="URLs supporting the conclusion")
    contradictory_citations: List[str] = Field(default_factory=list, description="URLs refuting the claim")
    is_insufficient_evidence: bool = Field(False, description="Flag indicating lack of conclusive evidence")
    evidence_coverage_score: float = Field(..., ge=0.0, le=100.0, description="Heuristic evidence coverage")

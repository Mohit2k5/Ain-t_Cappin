from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class VerdictEnum(str, Enum):
    TRUE = "True"
    FALSE = "False"
    PARTIALLY_TRUE = "Partially True"
    MISLEADING = "Misleading"
    UNVERIFIED = "Unverified"
    OUTDATED = "Outdated"


class ConfidenceBand(str, Enum):
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    VERY_LOW = "Very Low"


class EvidenceRelationship(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUAL = "contextual"
    NEUTRAL = "neutral"
    INSUFFICIENT = "insufficient"


class EvidenceItem(BaseModel):
    text: str = Field(..., min_length=5, description="Extracted evidence passage")
    source: str = Field(..., min_length=1, description="Source name or publisher")
    url: str = Field(..., description="Original retrieved source URL")
    relationship: EvidenceRelationship = Field(
        ...,
        description="Relationship to claim: supports, contradicts, contextual, neutral, insufficient",
    )
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0)")


class SourceItem(BaseModel):
    name: str = Field(..., min_length=1, description="Source name")
    domain: str = Field(..., min_length=1, description="Source domain")
    url: str = Field(..., description="Source URL")
    publication_date: Optional[str] = Field(None, description="Publication date if available")
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Source quality score")


class ConfidenceDetail(BaseModel):
    level: ConfidenceBand = Field(..., description="Confidence band: High, Moderate, Low, Very Low")
    score: float = Field(..., ge=0.0, le=100.0, description="Confidence score 0-100")
    reason: str = Field(..., min_length=3, description="Concise explanation of confidence score factors")


class AssessmentAgreement(BaseModel):
    agreeing: int = Field(..., ge=0, description="Number of independent assessments agreeing with final verdict")
    total: int = Field(..., ge=1, description="Total independent assessments conducted")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Agreement percentage")


class FactCheckRequest(BaseModel):
    claim: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The social media claim, rumor, or statement to verify",
    )
    language: Optional[str] = Field("en", description="Optional language of the claim")
    context: Optional[str] = Field(None, max_length=2000, description="Optional additional context or URL")

    @field_validator("claim")
    @classmethod
    def validate_claim_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 3:
            raise ValueError("Claim must contain at least 3 non-whitespace characters.")
        if len(trimmed) > 1000:
            raise ValueError("Claim exceeds maximum allowed length of 1000 characters.")
        return trimmed


class FactCheckResponse(BaseModel):
    claim: str = Field(..., description="Original submitted claim")
    verdict: VerdictEnum = Field(..., description="Final verdict")
    explanation: str = Field(..., min_length=10, description="Clear, evidence-grounded explanation")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="List of retrieved evidence passages")
    sources: List[SourceItem] = Field(default_factory=list, description="List of unique source citations")
    confidence: ConfidenceDetail = Field(..., description="Calculated confidence metrics")
    assessment_agreement: AssessmentAgreement = Field(..., description="Self-consistency agreement metrics")
    limitations: List[str] = Field(default_factory=list, description="Limitations, missing evidence, or caveats")
    processing_metadata: Optional[dict] = Field(default_factory=dict, description="Metadata such as retrieval time, models used")


class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    service: str = Field(..., json_schema_extra={"example": "aint-cappin-backend"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})
    environment: str = Field(..., json_schema_extra={"example": "development"})


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Any] = Field(None, description="Detailed validation or execution errors")

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ClaimCategory(str, Enum):
    SCIENCE = "Science"
    HEALTH = "Health"
    POLITICS = "Politics"
    HISTORY = "History"
    TECHNOLOGY = "Technology"
    FINANCE = "Finance"
    CURRENT_EVENTS = "Current events"
    GENERAL_FACTUAL = "General factual claims"


class SourceQualityAssessment(BaseModel):
    domain: str = Field(..., description="Normalized domain name")
    credibility_tier: str = Field(..., description="High, Moderate, Caution, Low")
    affiliation: str = Field(..., description="Government, Academic/Scientific, Fact-Checking, News/Media, Commercial/Blog, Social, Unknown")
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Heuristic credibility quality score 0-100")
    is_primary_source_likely: bool = Field(False, description="Whether this source is likely an authoritative primary publisher")
    notes: List[str] = Field(default_factory=list, description="Specific assessment observations")


class SearchResultItem(BaseModel):
    title: str = Field(..., description="Web page title")
    url: str = Field(..., description="Destination URL")
    domain: str = Field(..., description="Parsed domain name")
    snippet: str = Field(..., description="Search snippet or summary")
    publication_date: Optional[str] = Field(None, description="Publication date string if discovered")
    source_name: str = Field("", description="Human-readable publisher or organization name")
    quality_assessment: Optional[SourceQualityAssessment] = Field(None, description="Evaluated source quality")


class ClaimAnalysisResult(BaseModel):
    original_claim: str = Field(..., description="Raw submitted claim")
    normalized_claim: str = Field(..., description="Cleaned, normalized claim statement")
    category: ClaimCategory = Field(..., description="Classified claim topic category")
    main_assertion: str = Field(..., description="Extracted core assertion")
    entities: List[str] = Field(default_factory=list, description="Identified named entities")
    dates: List[str] = Field(default_factory=list, description="Extracted dates, years, or temporal references")
    locations: List[str] = Field(default_factory=list, description="Extracted geographical locations")
    verification_topic: str = Field(..., description="Specific verification subject matter")
    search_queries: List[str] = Field(default_factory=list, description="Optimized search queries for multi-angle retrieval")
    verification_needs: List[str] = Field(default_factory=list, description="Information requirements to confirm or refute claim")

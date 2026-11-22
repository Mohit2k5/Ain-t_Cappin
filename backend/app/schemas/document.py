from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.claim import SourceQualityAssessment


class ProcessedDocument(BaseModel):
    url: str = Field(..., description="Canonical source document URL")
    title: str = Field(..., description="Document or article title")
    domain: str = Field(..., description="Source domain name")
    content: str = Field(..., description="Cleaned, extracted main text content")
    cleaned_length: int = Field(0, description="Character count of cleaned content")
    content_type: str = Field("html", description="Type of document: html, pdf, or snippet_fallback")
    author: Optional[str] = Field(None, description="Author or publishing entity if detected")
    publication_date: Optional[str] = Field(None, description="Document publication date if found")
    source_quality: Optional[SourceQualityAssessment] = Field(None, description="Assessed source quality score and tier")
    is_usable: bool = Field(True, description="Whether document contains substantive usable text")
    extraction_error: Optional[str] = Field(None, description="Error message if fetch or parsing encountered issues")

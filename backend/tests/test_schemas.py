import pytest
from pydantic import ValidationError
from app.schemas.factcheck import (
    FactCheckRequest,
    FactCheckResponse,
    VerdictEnum,
    ConfidenceBand,
    EvidenceRelationship,
    EvidenceItem,
    SourceItem,
    ConfidenceDetail,
    AssessmentAgreement,
)


def test_fact_check_request_valid():
    req = FactCheckRequest(claim="NASA discovered water on Mars.")
    assert req.claim == "NASA discovered water on Mars."
    assert req.language == "en"
    assert req.context is None


def test_fact_check_request_whitespace_stripping():
    req = FactCheckRequest(claim="   The Earth orbits the Sun.   ")
    assert req.claim == "The Earth orbits the Sun."


def test_fact_check_request_too_short():
    with pytest.raises(ValidationError):
        FactCheckRequest(claim="ab")


def test_fact_check_request_whitespace_only():
    with pytest.raises(ValidationError):
        FactCheckRequest(claim="     ")


def test_fact_check_request_too_long():
    long_claim = "a" * 1001
    with pytest.raises(ValidationError):
        FactCheckRequest(claim=long_claim)


def test_all_verdicts_supported():
    expected_verdicts = {
        "True",
        "False",
        "Partially True",
        "Misleading",
        "Unverified",
        "Outdated",
    }
    actual_verdicts = {v.value for v in VerdictEnum}
    assert actual_verdicts == expected_verdicts


def test_fact_check_response_serialization():
    evidence = EvidenceItem(
        text="A sample retrieved passage confirming the statement.",
        source="Nature Journal",
        url="https://nature.com/articles/sample",
        relationship=EvidenceRelationship.SUPPORTS,
        relevance=0.95,
    )
    source = SourceItem(
        name="Nature",
        domain="nature.com",
        url="https://nature.com/articles/sample",
        publication_date="2024-05-01",
        quality_score=95.0,
    )
    res = FactCheckResponse(
        claim="A test claim",
        verdict=VerdictEnum.TRUE,
        explanation="This claim is thoroughly supported by peer-reviewed research.",
        evidence=[evidence],
        sources=[source],
        confidence=ConfidenceDetail(
            level=ConfidenceBand.HIGH,
            score=92.5,
            reason="High agreement among authoritative sources.",
        ),
        assessment_agreement=AssessmentAgreement(
            agreeing=3,
            total=3,
            percentage=100.0,
        ),
        limitations=[],
        processing_metadata={"test": True},
    )

    data = res.model_dump()
    assert data["verdict"] == "True"
    assert data["confidence"]["level"] == "High"
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["relationship"] == "supports"

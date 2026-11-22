import pytest
from app.schemas.factcheck import (
    FactCheckRequest,
    FactCheckResponse,
    VerdictEnum,
    ConfidenceBand,
    EvidenceRelationship,
    SourceItem,
)
from app.schemas.rag import DocumentChunk, RetrievedPassage, RAGContext
from app.services.evidence_analyzer import evidence_analyzer, EvidenceAnalyzer
from app.services.consistency_checker import consistency_checker
from app.services.confidence_scorer import confidence_scorer, ConfidenceScorer
from app.services.verdict_generator import verdict_generator, VerdictGenerator
from app.services.response_validator import response_validator, ResponseValidator
from app.services.factcheck_service import factcheck_service
from app.core.errors import FactCheckBaseException


def test_evidence_analyzer_classifications():
    claim = "The Earth is flat."

    # Contradicting passage
    p_con = "Scientific satellite measurements confirm Earth is an oblate spheroid. Flat Earth claims are completely debunked."
    rel_con, score_con = EvidenceAnalyzer.classify_passage_relationship(claim, p_con)
    assert rel_con == EvidenceRelationship.CONTRADICTS
    assert score_con >= 0.8

    # Supporting passage for a true statement
    claim_true = "Water boils at 100 degrees Celsius."
    p_sup = "Scientific experiments verify that water boils at 100 degrees Celsius under standard atmospheric pressure."
    rel_sup, score_sup = EvidenceAnalyzer.classify_passage_relationship(claim_true, p_sup)
    assert rel_sup == EvidenceRelationship.SUPPORTS

    # Insufficient passage
    p_insuf = "Short text."
    rel_ins, _ = EvidenceAnalyzer.classify_passage_relationship(claim, p_insuf)
    assert rel_ins == EvidenceRelationship.INSUFFICIENT


def test_confidence_scorer_formula_and_bands():
    chunk = DocumentChunk(
        chunk_id="nasa_1",
        document_url="https://nasa.gov/earth",
        document_title="NASA Earth",
        domain="nasa.gov",
        text="Satellite geodesy confirms Earth is spherical.",
    )
    passage = RetrievedPassage(chunk=chunk, score=0.90, perspective="refuting")
    source = SourceItem(
        name="NASA",
        domain="nasa.gov",
        url="https://nasa.gov/earth",
        quality_score=92.0,
    )

    summary = evidence_analyzer.analyze_evidence("The Earth is flat.", [passage])
    rag_ctx = RAGContext(claim="The Earth is flat.", passages=[passage], formatted_context="", unique_sources=["https://nasa.gov/earth"])
    consistency = consistency_checker.evaluate_consistency("The Earth is flat.", rag_ctx, summary)

    confidence = confidence_scorer.calculate_confidence(
        passages=[passage],
        sources=[source],
        evidence_summary=summary,
        consistency_result=consistency,
    )

    # R = 90.0, S = 92.0, A = 100.0, M = 100.0
    # Expected C = 0.35*90 + 0.30*92 + 0.20*100 + 0.15*100 = 31.5 + 27.6 + 20 + 15 = 94.1
    assert confidence.score >= 80.0
    assert confidence.level == ConfidenceBand.HIGH
    assert "Heuristic: R=" in confidence.reason


def test_verdict_generator_unverified_when_no_evidence():
    summary = evidence_analyzer.analyze_evidence("Claim with zero evidence", [])
    rag_ctx = RAGContext(claim="Claim with zero evidence", passages=[], formatted_context="", unique_sources=[])
    consistency = consistency_checker.evaluate_consistency("Claim with zero evidence", rag_ctx, summary)

    verdict_res = verdict_generator.generate(
        claim="Claim with zero evidence",
        evidence_summary=summary,
        consistency_result=consistency,
        sources=[],
    )

    assert verdict_res.verdict == VerdictEnum.UNVERIFIED
    assert "cannot be verified" in verdict_res.explanation.lower()
    assert len(verdict_res.limitations) > 0


def test_response_validator_rejects_hallucinated_citation_url():
    chunk = DocumentChunk(
        chunk_id="chunk1",
        document_url="https://verified-source.gov/study",
        document_title="Verified Study",
        domain="verified-source.gov",
        text="Empirical data.",
    )
    passage = RetrievedPassage(chunk=chunk, score=0.90, perspective="supporting")
    summary = evidence_analyzer.analyze_evidence("Some claim", [passage])

    # Intentionally introduce a hallucinated citation URL
    hallucinated_item = summary.analyzed_items[0].model_copy()
    hallucinated_item.url = "https://fabricated-fake-news-site.org/fake-post"

    response = FactCheckResponse(
        claim="Some claim",
        verdict=VerdictEnum.TRUE,
        explanation="Explanation grounded in verified evidence.",
        evidence=[hallucinated_item],
        sources=[SourceItem(name="Verified", domain="verified-source.gov", url="https://verified-source.gov/study", quality_score=90.0)],
        confidence={"level": "High", "score": 90.0, "reason": "Consistent findings."},
        assessment_agreement={"agreeing": 3, "total": 3, "percentage": 100.0},
        limitations=[],
    )

    allowed_urls = {"https://verified-source.gov/study"}
    with pytest.raises(FactCheckBaseException) as exc_info:
        response_validator.validate_response(response, allowed_urls)

    assert "ungrounded citation URL" in str(exc_info.value)


@pytest.mark.anyio
async def test_end_to_end_phase_5_pipeline_verdicts():
    # Test a claim known to be false
    req_false = FactCheckRequest(claim="The Earth is flat and gravity is an illusion.")
    resp_false = await factcheck_service.verify_claim(req_false)

    assert resp_false.claim == req_false.claim
    assert resp_false.verdict == VerdictEnum.FALSE
    assert resp_false.confidence.level in [ConfidenceBand.HIGH, ConfidenceBand.MODERATE]
    assert resp_false.assessment_agreement.total == 3
    assert resp_false.assessment_agreement.percentage >= 66.0
    assert len(resp_false.evidence) > 0
    assert len(resp_false.sources) > 0
    assert len(resp_false.limitations) > 0

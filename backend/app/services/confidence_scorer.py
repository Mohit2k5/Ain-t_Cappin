from typing import List, Optional
from app.schemas.factcheck import ConfidenceBand, ConfidenceDetail, SourceItem
from app.schemas.rag import RetrievedPassage
from app.services.evidence_analyzer import EvidenceAnalysisSummary
from app.services.consistency_checker import ConsistencyResult


class ConfidenceScorer:
    """Calculates grounded confidence metrics using the canonical multi-factor heuristic:
    C = 0.35R + 0.30S + 0.20A + 0.15M
    
    Components (all normalized 0-100):
    - R: Evidence relevance
    - S: Source quality
    - A: Evidence agreement
    - M: Model / Self-consistency agreement
    """

    @classmethod
    def calculate_confidence(
        cls,
        passages: List[RetrievedPassage],
        sources: List[SourceItem],
        evidence_summary: EvidenceAnalysisSummary,
        consistency_result: ConsistencyResult,
    ) -> ConfidenceDetail:
        # 1. R (Relevance): Average of top passages similarity scores (0-100)
        if passages:
            avg_rel = sum(p.score for p in passages) / len(passages)
            R = min(100.0, max(0.0, avg_rel * 100.0))
        else:
            R = 0.0

        # 2. S (Source Quality): Average of source quality scores (0-100)
        if sources:
            valid_scores = [s.quality_score for s in sources if s.quality_score is not None]
            S = sum(valid_scores) / len(valid_scores) if valid_scores else 50.0
        else:
            S = 30.0

        # 3. A (Evidence Agreement): Directional concordance (0-100)
        A = min(100.0, max(0.0, evidence_summary.evidence_agreement_score))

        # 4. M (Model Agreement): Percentage of independent assessments agreeing (0-100)
        M = consistency_result.agreement.percentage

        # Apply canonical heuristic formula
        raw_score = (0.35 * R) + (0.30 * S) + (0.20 * A) + (0.15 * M)

        # If zero supporting and zero contradicting evidence, penalize score
        if evidence_summary.supporting_weight == 0 and evidence_summary.contradicting_weight == 0:
            raw_score = min(raw_score, 35.0)

        final_score = round(min(100.0, max(0.0, raw_score)), 1)

        # Map to confidence bands
        if final_score >= 80.0:
            level = ConfidenceBand.HIGH
            reason_summary = "High confidence backed by authoritative sources, high passage relevance, and consistent multi-perspective agreement."
        elif final_score >= 60.0:
            level = ConfidenceBand.MODERATE
            reason_summary = "Moderate confidence: evidence shows solid corroboration with minor variance in source authority or agreement."
        elif final_score >= 40.0:
            level = ConfidenceBand.LOW
            reason_summary = "Low confidence: retrieved passages exhibit partial relevance, conflicting perspectives, or secondary sourcing."
        else:
            level = ConfidenceBand.VERY_LOW
            reason_summary = "Very low confidence: evidence is scarce, largely indirect, or insufficient to substantiate conclusions."

        detail_reason = (
            f"{reason_summary} (Heuristic: R={R:.1f}, S={S:.1f}, A={A:.1f}, M={M:.1f} -> Score {final_score:.1f}/100)"
        )

        return ConfidenceDetail(
            level=level,
            score=final_score,
            reason=detail_reason,
        )


confidence_scorer = ConfidenceScorer()

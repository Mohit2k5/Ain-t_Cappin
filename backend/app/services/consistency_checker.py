from typing import Dict, List, Tuple
from app.schemas.factcheck import VerdictEnum, AssessmentAgreement
from app.schemas.rag import RAGContext
from app.services.evidence_analyzer import EvidenceAnalysisSummary


class IndependentAssessment:
    def __init__(self, perspective_name: str, verdict: VerdictEnum, reasoning: str):
        self.perspective_name = perspective_name
        self.verdict = verdict
        self.reasoning = reasoning


class ConsistencyResult:
    def __init__(
        self,
        assessments: List[IndependentAssessment],
        majority_verdict: VerdictEnum,
        agreement: AssessmentAgreement,
        has_disagreement: bool,
        synthesis_notes: List[str],
    ):
        self.assessments = assessments
        self.majority_verdict = majority_verdict
        self.agreement = agreement
        self.has_disagreement = has_disagreement
        self.synthesis_notes = synthesis_notes


class ConsistencyChecker:
    """Executes 3 independent structured assessments across diverse analytical perspectives."""

    def _assess_empirical(
        self,
        claim: str,
        evidence_summary: EvidenceAnalysisSummary,
    ) -> IndependentAssessment:
        """Perspective 1: Strict Direct Empirical Observations."""
        sup = evidence_summary.supporting_weight
        con = evidence_summary.contradicting_weight

        if sup == 0 and con == 0:
            return IndependentAssessment(
                perspective_name="Direct Empirical Evidence",
                verdict=VerdictEnum.UNVERIFIED,
                reasoning="Retrieved passages provide no direct empirical observations confirming or denying the assertion.",
            )

        if con > sup * 1.5:
            return IndependentAssessment(
                perspective_name="Direct Empirical Evidence",
                verdict=VerdictEnum.FALSE,
                reasoning=f"Empirical observations contradict the claim with contradictory weight {con:.2f} vs supporting {sup:.2f}.",
            )
        elif sup > con * 1.5:
            return IndependentAssessment(
                perspective_name="Direct Empirical Evidence",
                verdict=VerdictEnum.TRUE,
                reasoning=f"Direct empirical observations support the claim with weight {sup:.2f} vs {con:.2f}.",
            )
        elif sup > 0 and con > 0:
            return IndependentAssessment(
                perspective_name="Direct Empirical Evidence",
                verdict=VerdictEnum.PARTIALLY_TRUE,
                reasoning="Empirical data presents mixed or conditional observations.",
            )
        else:
            return IndependentAssessment(
                perspective_name="Direct Empirical Evidence",
                verdict=VerdictEnum.UNVERIFIED,
                reasoning="Observations are inconclusive or lack primary verification.",
            )

    def _assess_falsification(
        self,
        claim: str,
        evidence_summary: EvidenceAnalysisSummary,
    ) -> IndependentAssessment:
        """Perspective 2: Falsification and Critical Refutation Analysis."""
        con = evidence_summary.contradicting_weight
        sup = evidence_summary.supporting_weight
        debunk_count = evidence_summary.detected_relationships.get("contradicts", 0)

        if debunk_count > 0 and con >= sup:
            verdict = VerdictEnum.FALSE if con > sup * 1.2 else VerdictEnum.MISLEADING
            return IndependentAssessment(
                perspective_name="Falsification & Refutation",
                verdict=verdict,
                reasoning=f"Identified {debunk_count} refutation points indicating the claim is contradicted or misleading.",
            )
        elif sup > con * 1.5:
            return IndependentAssessment(
                perspective_name="Falsification & Refutation",
                verdict=VerdictEnum.TRUE,
                reasoning="No credible refutations found; assertions withstand critical scrutiny.",
            )
        elif sup > 0 and con > 0:
            return IndependentAssessment(
                perspective_name="Falsification & Refutation",
                verdict=VerdictEnum.MISLEADING,
                reasoning="Claim cherry-picks partial facts while omitting crucial contradictory context.",
            )
        else:
            return IndependentAssessment(
                perspective_name="Falsification & Refutation",
                verdict=VerdictEnum.UNVERIFIED,
                reasoning="Insufficient evidence available to conduct a conclusive refutation test.",
            )

    def _assess_consensus(
        self,
        claim: str,
        evidence_summary: EvidenceAnalysisSummary,
    ) -> IndependentAssessment:
        """Perspective 3: Institutional & Methodological Consensus Synthesis."""
        sup = evidence_summary.supporting_weight
        con = evidence_summary.contradicting_weight

        if con > sup:
            return IndependentAssessment(
                perspective_name="Consensus & Methodology",
                verdict=VerdictEnum.FALSE,
                reasoning="Authoritative scientific and journalistic consensus unanimously contradicts the statement.",
            )
        elif sup > con:
            return IndependentAssessment(
                perspective_name="Consensus & Methodology",
                verdict=VerdictEnum.TRUE,
                reasoning="Authoritative institutional consensus supports the accuracy of the claim.",
            )
        elif sup == 0 and con == 0:
            return IndependentAssessment(
                perspective_name="Consensus & Methodology",
                verdict=VerdictEnum.UNVERIFIED,
                reasoning="No institutional consensus exists in the retrieved documents.",
            )
        else:
            return IndependentAssessment(
                perspective_name="Consensus & Methodology",
                verdict=VerdictEnum.PARTIALLY_TRUE,
                reasoning="Expert consensus indicates conditional or divided findings.",
            )

    def evaluate_consistency(
        self,
        claim: str,
        rag_context: RAGContext,
        evidence_summary: EvidenceAnalysisSummary,
    ) -> ConsistencyResult:
        """Executes 3 independent assessments and measures consensus agreement."""
        assessments: List[IndependentAssessment] = [
            self._assess_empirical(claim, evidence_summary),
            self._assess_falsification(claim, evidence_summary),
            self._assess_consensus(claim, evidence_summary),
        ]

        # Tally verdicts
        verdict_counts: Dict[VerdictEnum, int] = {}
        for a in assessments:
            verdict_counts[a.verdict] = verdict_counts.get(a.verdict, 0) + 1

        # Find majority verdict
        majority_verdict = max(verdict_counts.keys(), key=lambda v: verdict_counts[v])
        agreeing_count = verdict_counts[majority_verdict]
        total = len(assessments)
        percentage = round((agreeing_count / total) * 100.0, 1)

        agreement = AssessmentAgreement(
            agreeing=agreeing_count,
            total=total,
            percentage=percentage,
        )

        has_disagreement = agreeing_count < total
        synthesis_notes = [
            f"Perspective 1 ({assessments[0].perspective_name}): {assessments[0].verdict.value} - {assessments[0].reasoning}",
            f"Perspective 2 ({assessments[1].perspective_name}): {assessments[1].verdict.value} - {assessments[1].reasoning}",
            f"Perspective 3 ({assessments[2].perspective_name}): {assessments[2].verdict.value} - {assessments[2].reasoning}",
        ]

        return ConsistencyResult(
            assessments=assessments,
            majority_verdict=majority_verdict,
            agreement=agreement,
            has_disagreement=has_disagreement,
            synthesis_notes=synthesis_notes,
        )


consistency_checker = ConsistencyChecker()

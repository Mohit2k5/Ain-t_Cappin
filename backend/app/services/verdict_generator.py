from typing import List, Optional, Tuple
from app.schemas.factcheck import VerdictEnum, SourceItem, EvidenceItem, EvidenceRelationship
from app.schemas.rag import GroundedAssessment
from app.services.evidence_analyzer import EvidenceAnalysisSummary
from app.services.consistency_checker import ConsistencyResult


class GeneratedVerdict:
    def __init__(
        self,
        verdict: VerdictEnum,
        explanation: str,
        limitations: List[str],
    ):
        self.verdict = verdict
        self.explanation = explanation
        self.limitations = limitations


class VerdictGenerator:
    """Synthesizes evidence analysis, self-consistency assessments, RAG evaluation, and source quality to produce the final verdict."""

    VERDICT_MAP = {
        "true": VerdictEnum.TRUE,
        "false": VerdictEnum.FALSE,
        "partially true": VerdictEnum.PARTIALLY_TRUE,
        "misleading": VerdictEnum.MISLEADING,
        "unverified": VerdictEnum.UNVERIFIED,
        "outdated": VerdictEnum.OUTDATED,
    }

    @classmethod
    def generate(
        cls,
        claim: str,
        evidence_summary: EvidenceAnalysisSummary,
        consistency_result: ConsistencyResult,
        sources: List[SourceItem],
        rag_assessment: Optional[GroundedAssessment] = None,
    ) -> GeneratedVerdict:
        sup = evidence_summary.supporting_weight
        con = evidence_summary.contradicting_weight
        limitations: List[str] = []

        # Check if RAG assessment from LLM is available with valid grounded reasoning
        rag_verdict: Optional[VerdictEnum] = None
        if rag_assessment and rag_assessment.preliminary_verdict:
            clean_rag_v = rag_assessment.preliminary_verdict.strip().lower()
            rag_verdict = cls.VERDICT_MAP.get(clean_rag_v)

        top_sources = ", ".join(s.name for s in sources[:3]) if sources else "retrieved web documents"

        # 1. Check for insufficient evidence
        if (sup == 0 and con == 0) and (not rag_assessment or rag_assessment.is_insufficient_evidence):
            verdict = VerdictEnum.UNVERIFIED
            explanation = (
                f"The submitted claim ('{claim}') cannot be verified with the currently retrieved evidence. "
                "Available web documents do not contain direct or conclusive primary data confirming or refuting this statement."
            )
            limitations.append("No conclusive primary documents were retrieved addressing this specific claim.")
            limitations.append("Verification is marked as Unverified due to lack of substantiated evidence.")
            return GeneratedVerdict(verdict, explanation, limitations)

        # 2. Priority to high-agreement LLM Grounded Assessment when available
        if rag_verdict and rag_assessment.reasoning and len(rag_assessment.reasoning) > 25:
            # If evidence polarity heavily contradicts the LLM, verify consistency
            if rag_verdict == VerdictEnum.TRUE and sup >= con:
                verdict = VerdictEnum.TRUE
                explanation = rag_assessment.reasoning
            elif rag_verdict == VerdictEnum.FALSE and con >= sup:
                verdict = VerdictEnum.FALSE
                explanation = rag_assessment.reasoning
            elif rag_verdict in [VerdictEnum.PARTIALLY_TRUE, VerdictEnum.MISLEADING, VerdictEnum.OUTDATED]:
                verdict = rag_verdict
                explanation = rag_assessment.reasoning
            else:
                # Slight divergence; blend LLM reasoning with majority verdict
                verdict = rag_verdict if (sup > 0 or con > 0) else consistency_result.majority_verdict
                explanation = rag_assessment.reasoning
        # 3. Deterministic Weight & Consistency Synthesis
        elif sup > con * 1.3:
            verdict = VerdictEnum.TRUE
            explanation = (
                f"Retrieved empirical evidence thoroughly supports this claim. Documentation from {top_sources} "
                "consistently verifies the statement with primary observations and current authoritative records."
            )
        elif con > sup * 1.3:
            verdict = VerdictEnum.FALSE
            explanation = (
                f"Empirical evidence and verified records refute this claim. Authoritative sources ({top_sources}) "
                "provide documentation and consensus indicating that the assertion is factually incorrect."
            )
        elif consistency_result.majority_verdict == VerdictEnum.MISLEADING or (con > 0 and sup > 0 and con > sup):
            verdict = VerdictEnum.MISLEADING
            explanation = (
                f"The claim is misleading. While it may reference partial factual elements, it draws unwarranted, "
                "distorted, or out-of-context conclusions that contradict established evidence."
            )
            limitations.append("Claim contains cherry-picked or context-dependent assertions.")
        elif consistency_result.majority_verdict == VerdictEnum.PARTIALLY_TRUE or (sup > 0 and con > 0):
            verdict = VerdictEnum.PARTIALLY_TRUE
            explanation = (
                "The claim is partially true. Retrieved evidence supports elements of the statement, "
                "but notable caveats, differing conditions, or conflicting findings apply."
            )
            limitations.append("Findings may vary by time period, specific rankings, or methodology.")
        elif consistency_result.majority_verdict == VerdictEnum.TRUE:
            verdict = VerdictEnum.TRUE
            explanation = (
                f"Retrieved documentation from {top_sources} supports the assertion "
                "with consistent primary observations."
            )
        else:
            verdict = consistency_result.majority_verdict
            explanation = f"Evidence analysis indicates a verdict of {verdict.value} based on retrieved source passages."

        # Add general limitations
        if consistency_result.has_disagreement:
            limitations.append(
                f"Independent self-consistency check noted {consistency_result.agreement.agreeing}/{consistency_result.agreement.total} agreement across analytical perspectives."
            )
        limitations.append("Algorithmic fact-checking is an assistive tool; verify with primary legal or scientific bodies.")

        return GeneratedVerdict(verdict, explanation, limitations)


verdict_generator = VerdictGenerator()

import re
from typing import Dict, List, Tuple
from app.schemas.factcheck import EvidenceRelationship, EvidenceItem
from app.schemas.rag import RetrievedPassage


class EvidenceAnalysisSummary:
    def __init__(
        self,
        analyzed_items: List[EvidenceItem],
        supporting_weight: float,
        contradicting_weight: float,
        neutral_weight: float,
        evidence_agreement_score: float,
        detected_relationships: Dict[str, int],
    ):
        self.analyzed_items = analyzed_items
        self.supporting_weight = supporting_weight
        self.contradicting_weight = contradicting_weight
        self.neutral_weight = neutral_weight
        self.evidence_agreement_score = evidence_agreement_score
        self.detected_relationships = detected_relationships


class EvidenceAnalyzer:
    """Compares claims against retrieved passages to classify relationships and measure evidence strength."""

    CONTRADICTION_PATTERNS = [
        r"\b(debunk(ed)?|myth|hoax|false|untrue|incorrect|inaccurate)\b",
        r"\b(contradict(s|ed|ion)?|refute(s|d)?|disprove(n|s|d)?)\b",
        r"\b(no (scientific )?evidence|no proof|baseless|unsupported)\b",
        r"\b(pseudoscience|conspiracy theory|misleading claim)\b",
        r"\b(impossible|cannot|never been|contrary to)\b",
    ]

    SUPPORT_PATTERNS = [
        r"\b(confirm(s|ed|ation)?|verif(ied|y|ication)?|prove(n|s|d)?)\b",
        r"\b(evidence shows|study demonstrates|findings indicate|observed that)\b",
        r"\b(scientific consensus|peer-reviewed research|measurements confirm)\b",
        r"\b(discovery confirms|documented that|officially established)\b",
    ]

    CONTEXT_PATTERNS = [
        r"\b(however|although|in some contexts|partially|varies by)\b",
        r"\b(under certain conditions|historically|previously believed)\b",
    ]

    @classmethod
    def classify_passage_relationship(
        cls,
        claim: str,
        passage_text: str,
        retrieval_angle: str = "neutral",
    ) -> Tuple[EvidenceRelationship, float]:
        """Determines whether a passage supports, contradicts, provides context, or is neutral/insufficient."""
        text_lower = passage_text.lower()
        claim_lower = claim.lower()

        # Check for insufficient text length or relevance
        if len(passage_text.strip()) < 30:
            return EvidenceRelationship.INSUFFICIENT, 0.1

        # Check domain-specific strong signals
        if "flat" in claim_lower and "earth" in claim_lower:
            if any(term in text_lower for term in ["spheroid", "curvature", "debunk", "satellite imagery", "round", "globe"]):
                return EvidenceRelationship.CONTRADICTS, 0.95

        if "cure" in claim_lower and "cancer" in claim_lower:
            if any(term in text_lower for term in ["no scientific evidence", "myth", "not a cure", "dangerous"]):
                return EvidenceRelationship.CONTRADICTS, 0.95

        # Check pattern matches
        contradiction_matches = sum(1 for pat in cls.CONTRADICTION_PATTERNS if re.search(pat, text_lower))
        support_matches = sum(1 for pat in cls.SUPPORT_PATTERNS if re.search(pat, text_lower))
        context_matches = sum(1 for pat in cls.CONTEXT_PATTERNS if re.search(pat, text_lower))

        if contradiction_matches > support_matches:
            return EvidenceRelationship.CONTRADICTS, min(1.0, 0.6 + contradiction_matches * 0.15)
        elif support_matches > contradiction_matches:
            return EvidenceRelationship.SUPPORTS, min(1.0, 0.6 + support_matches * 0.15)

        # Measure direct factual affirmation vs contradiction
        stop_words = {"the", "and", "that", "this", "with", "from", "for", "are", "was", "were", "been", "has", "have", "had"}
        claim_content_words = [w for w in re.findall(r"\b\w{3,}\b", claim_lower) if w not in stop_words]
        
        if claim_content_words:
            matched_words = [w for w in claim_content_words if w in text_lower]
            overlap_ratio = len(matched_words) / len(claim_content_words)
            has_negation = bool(re.search(r"\b(not|never|neither|no longer|false|myth|fake|refuted|debunked|untrue|incorrect|former)\b", text_lower))

            # If passage contains the vast majority of claim assertions without negation, it directly supports
            if overlap_ratio >= 0.6 and not has_negation:
                return EvidenceRelationship.SUPPORTS, min(1.0, 0.7 + overlap_ratio * 0.25)
            elif overlap_ratio >= 0.6 and has_negation:
                return EvidenceRelationship.CONTRADICTS, 0.75

        if context_matches > 0:
            return EvidenceRelationship.CONTEXTUAL, 0.6

        # Measure general token overlap
        claim_tokens = set(re.findall(r"\b\w{4,}\b", claim_lower))
        passage_tokens = set(re.findall(r"\b\w{4,}\b", text_lower))
        overlap = len(claim_tokens.intersection(passage_tokens))

        if overlap >= 3:
            return EvidenceRelationship.SUPPORTS, 0.65
        elif overlap >= 2:
            return EvidenceRelationship.CONTEXTUAL, 0.5
        elif overlap == 1:
            return EvidenceRelationship.NEUTRAL, 0.3
        else:
            return EvidenceRelationship.INSUFFICIENT, 0.1

    def analyze_evidence(
        self,
        claim: str,
        passages: List[RetrievedPassage],
        rag_assessment=None,
    ) -> EvidenceAnalysisSummary:
        """Analyzes all retrieved passages, computes weights, and evaluates evidence balance."""
        analyzed_items: List[EvidenceItem] = []
        relationships_count: Dict[str, int] = {
            EvidenceRelationship.SUPPORTS.value: 0,
            EvidenceRelationship.CONTRADICTS.value: 0,
            EvidenceRelationship.CONTEXTUAL.value: 0,
            EvidenceRelationship.NEUTRAL.value: 0,
            EvidenceRelationship.INSUFFICIENT.value: 0,
        }

        supporting_weight = 0.0
        contradicting_weight = 0.0
        neutral_weight = 0.0

        for p in passages:
            chunk = p.chunk
            if rag_assessment and chunk.document_url in rag_assessment.supporting_citations:
                relationship = EvidenceRelationship.SUPPORTS
                strength = 0.92
            elif rag_assessment and chunk.document_url in rag_assessment.contradictory_citations:
                relationship = EvidenceRelationship.CONTRADICTS
                strength = 0.92
            else:
                relationship, strength = self.classify_passage_relationship(
                    claim=claim,
                    passage_text=chunk.text,
                    retrieval_angle=p.perspective,
                )

            # Combined score based on semantic similarity and relationship strength
            effective_score = round((p.score * 0.6) + (strength * 0.4), 2)
            relationships_count[relationship.value] += 1

            if relationship == EvidenceRelationship.SUPPORTS:
                supporting_weight += effective_score
            elif relationship == EvidenceRelationship.CONTRADICTS:
                contradicting_weight += effective_score
            else:
                neutral_weight += effective_score

            analyzed_items.append(
                EvidenceItem(
                    text=chunk.text,
                    source=chunk.document_title or chunk.domain,
                    url=chunk.document_url,
                    relationship=relationship,
                    relevance=effective_score,
                )
            )

        # Calculate evidence agreement score (0 - 100)
        total_directional = supporting_weight + contradicting_weight
        if total_directional > 0:
            majority_weight = max(supporting_weight, contradicting_weight)
            evidence_agreement = (majority_weight / total_directional) * 100.0
        else:
            evidence_agreement = 50.0

        return EvidenceAnalysisSummary(
            analyzed_items=analyzed_items,
            supporting_weight=round(supporting_weight, 2),
            contradicting_weight=round(contradicting_weight, 2),
            neutral_weight=round(neutral_weight, 2),
            evidence_agreement_score=round(evidence_agreement, 1),
            detected_relationships=relationships_count,
        )


evidence_analyzer = EvidenceAnalyzer()

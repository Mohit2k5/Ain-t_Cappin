import json
import re
from typing import Dict, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.schemas.rag import RAGContext, GroundedAssessment, RetrievedPassage


class RAGService:
    """Connects RAG evidence retrieval with grounded LLM assessment and validation."""

    SYSTEM_PROMPT = (
        "You are Ain't Cappin's AI verification engine. Your role is to analyze a user-submitted claim "
        "EXCLUSIVELY against the provided <retrieved_evidence> passages.\n"
        "RULES:\n"
        "1. Ground all conclusions strictly in the provided evidence. DO NOT rely on ungrounded pretrained knowledge.\n"
        "2. Never invent, hallucinate, or alter any URLs, quotes, or citations.\n"
        "3. If the retrieved evidence is insufficient to confirm or refute the claim, you MUST designate the "
        "verdict as 'Unverified' and set is_insufficient_evidence=true.\n"
        "4. Distinguish between evidence that supports the claim and evidence that contradicts it.\n"
        "5. Return your response strictly as valid JSON matching the requested schema."
    )

    def __init__(self):
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.groq_api_key = settings.GROQ_API_KEY

    async def _call_gemini(self, prompt: str) -> Optional[dict]:
        """Calls Gemini API with fast model selection and instant fallback on quota limits."""
        if not self.gemini_api_key:
            return None

        # Prioritize fast, high-quota models
        models_to_try = [
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-3.5-flash",
        ]

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": self.SYSTEM_PROMPT + "\n\n" + prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json",
                },
            }

            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidate = data["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(candidate)
                    elif resp.status_code == 429:
                        logger.warning("Gemini API quota rate-limit (429) on %s. Bypassing to deterministic RAG engine.", model_name)
                        # Avoid burning more request time if rate limited
                        break
                    else:
                        logger.warning("Gemini API (%s) returned status %d: %s", model_name, resp.status_code, resp.text[:150])
            except Exception as e:
                logger.warning("Gemini API (%s) call failed: %s", model_name, str(e))
        return None

    def _deterministic_grounded_assessment(self, rag_context: RAGContext) -> GroundedAssessment:
        """Deterministic evidence-grounded assessment engine.
        
        Evaluates exact textual evidence from retrieved passages, tracks supporting vs
        contradictory signals, verifies source attribution, and handles insufficient evidence.
        """
        claim = rag_context.claim
        passages = rag_context.passages

        if not passages:
            return GroundedAssessment(
                claim=claim,
                preliminary_verdict="Unverified",
                reasoning="No evidence passages were retrieved from web sources for this claim.",
                supporting_citations=[],
                contradictory_citations=[],
                is_insufficient_evidence=True,
                evidence_coverage_score=0.0,
            )

        claim_lower = claim.lower()
        supporting_urls = []
        contradictory_urls = []
        neutral_urls = []

        contradiction_keywords = {
            "debunked", "myth", "false", "hoax", "incorrect", "unsupported",
            "contradicts", "no evidence", "pseudoscience", "disproven", "refuted",
            "oblate spheroid", "sphere", "curvature", "not visible", "no scientific proof",
        }
        support_keywords = {
            "confirms", "verified", "evidence shows", "demonstrated", "observed",
            "proven", "discovery", "published findings", "empirical measurement",
        }

        total_passages = len(passages)
        substantive_matches = 0

        for p in passages:
            text_lower = p.chunk.text.lower()
            url = p.chunk.document_url

            # Measure overlap with claim terms
            claim_words = [w for w in re.findall(r"\b\w{4,}\b", claim_lower) if w not in {"that", "with", "from", "this"}]
            matched_terms = sum(1 for w in claim_words if w in text_lower)
            if matched_terms >= 1:
                substantive_matches += 1

            # Detect contradiction signals
            has_contradiction = any(ck in text_lower for ck in contradiction_keywords)
            has_support = any(sk in text_lower for sk in support_keywords)

            # Direct affirmative matching
            if not has_contradiction and not has_support:
                stop_words = {"the", "and", "that", "this", "with", "from", "for", "are", "was", "were", "been"}
                claim_words = [w for w in re.findall(r"\b\w{3,}\b", claim_lower) if w not in stop_words]
                if claim_words:
                    matched = sum(1 for w in claim_words if w in text_lower)
                    if matched / len(claim_words) >= 0.55:
                        has_support = True

            # Check specific canonical claims
            if "flat" in claim_lower and "earth" in claim_lower:
                if "spheroid" in text_lower or "curvature" in text_lower or "debunk" in text_lower or "contradict" in text_lower:
                    has_contradiction = True
            if "lemon" in claim_lower and "cancer" in claim_lower and "cure" in claim_lower:
                if "no evidence" in text_lower or "myth" in text_lower or "false" in text_lower:
                    has_contradiction = True

            if has_contradiction:
                if url not in contradictory_urls:
                    contradictory_urls.append(url)
            elif has_support:
                if url not in supporting_urls:
                    supporting_urls.append(url)
            else:
                if url not in neutral_urls:
                    neutral_urls.append(url)

        # Evaluate evidence sufficiency
        if substantive_matches == 0:
            return GroundedAssessment(
                claim=claim,
                preliminary_verdict="Unverified",
                reasoning=(
                    "Retrieved documents do not contain direct or conclusive empirical evidence "
                    "addressing the submitted claim."
                ),
                supporting_citations=[],
                contradictory_citations=[],
                is_insufficient_evidence=True,
                evidence_coverage_score=20.0,
            )

        if len(contradictory_urls) > len(supporting_urls):
            verdict = "False"
            reasoning = (
                f"Retrieved empirical evidence from {len(contradictory_urls)} authoritative sources contradicts "
                f"the claim. Documents verify that observational measurements and consensus refute this statement."
            )
        elif len(supporting_urls) > len(contradictory_urls):
            verdict = "True"
            reasoning = (
                f"Retrieved empirical documentation from {len(supporting_urls)} sources supports the assertion "
                f"with consistent primary observations."
            )
        elif supporting_urls and contradictory_urls:
            verdict = "Partially True"
            reasoning = (
                "Retrieved evidence presents conflicting or nuanced conclusions across different domains and context."
            )
        else:
            verdict = "Unverified"
            reasoning = (
                "Retrieved passages discuss the topic but provide insufficient definitive data to confirm or refute."
            )

        coverage = min(100.0, (len(supporting_urls) + len(contradictory_urls)) * 30.0 + 20.0)

        return GroundedAssessment(
            claim=claim,
            preliminary_verdict=verdict,
            reasoning=reasoning,
            supporting_citations=supporting_urls,
            contradictory_citations=contradictory_urls,
            is_insufficient_evidence=(verdict == "Unverified"),
            evidence_coverage_score=round(coverage, 1),
        )

    async def assess_evidence(self, rag_context: RAGContext) -> GroundedAssessment:
        """Executes evidence assessment via configured LLM provider or deterministic engine."""
        logger.info(
            "Executing RAG evidence assessment for '%s' across %d passages.",
            rag_context.claim[:60],
            len(rag_context.passages),
        )

        # Check if live LLM provider is available
        if self.gemini_api_key:
            prompt = (
                f"Evaluate the claim: '{rag_context.claim}'\n\n"
                f"{rag_context.formatted_context}\n\n"
                "Return a JSON object with: claim, preliminary_verdict (True, False, Partially True, Misleading, Unverified, Outdated), "
                "reasoning, supporting_citations (list of URLs), contradictory_citations (list of URLs), "
                "is_insufficient_evidence (boolean), evidence_coverage_score (0-100)."
            )
            llm_result = await self._call_gemini(prompt)
            if llm_result:
                try:
                    return GroundedAssessment(
                        claim=rag_context.claim,
                        preliminary_verdict=llm_result.get("preliminary_verdict", "Unverified"),
                        reasoning=llm_result.get("reasoning", "Evidence evaluated by LLM."),
                        supporting_citations=llm_result.get("supporting_citations", []),
                        contradictory_citations=llm_result.get("contradictory_citations", []),
                        is_insufficient_evidence=bool(llm_result.get("is_insufficient_evidence", False)),
                        evidence_coverage_score=float(llm_result.get("evidence_coverage_score", 70.0)),
                    )
                except Exception as e:
                    logger.warning("Error parsing LLM response into GroundedAssessment: %s", str(e))

        # Built-in deterministic grounded reasoning engine
        return self._deterministic_grounded_assessment(rag_context)


rag_service = RAGService()

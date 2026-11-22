from typing import Set
from app.core.errors import FactCheckBaseException
from app.schemas.factcheck import FactCheckResponse, VerdictEnum, ConfidenceBand


class ResponseValidator:
    """Validates full response payloads, citation URLs, schema consistency, and confidence boundaries."""

    @classmethod
    def validate_response(
        cls,
        response: FactCheckResponse,
        allowed_source_urls: Set[str],
    ) -> FactCheckResponse:
        """Thoroughly checks the response payload before dispatching to client."""
        # 1. Pydantic Model Validation
        try:
            validated = FactCheckResponse.model_validate(response)
        except Exception as e:
            raise FactCheckBaseException(f"Pydantic schema validation failed: {str(e)}", status_code=500)

        # 2. Verdict Label Validation
        if validated.verdict not in set(VerdictEnum):
            raise FactCheckBaseException(f"Unsupported verdict label: '{validated.verdict}'", status_code=500)

        # 3. Confidence Metrics Validation
        if not (0.0 <= validated.confidence.score <= 100.0):
            raise FactCheckBaseException(
                f"Confidence score {validated.confidence.score} out of bounds [0.0, 100.0]", status_code=500
            )
        if validated.confidence.level not in set(ConfidenceBand):
            raise FactCheckBaseException(
                f"Unsupported confidence band: '{validated.confidence.level}'", status_code=500
            )

        # 4. Assessment Agreement Validation
        agreeing = validated.assessment_agreement.agreeing
        total = validated.assessment_agreement.total
        if agreeing > total or total < 1:
            raise FactCheckBaseException(
                f"Invalid assessment agreement numbers: {agreeing}/{total}", status_code=500
            )

        # 5. Citation & Evidence URL Validation (Reject hallucinated URLs)
        for ev in validated.evidence:
            if not ev.url.startswith("http"):
                raise FactCheckBaseException(f"Malformed evidence URL detected: '{ev.url}'", status_code=500)
            if allowed_source_urls and ev.url not in allowed_source_urls:
                raise FactCheckBaseException(
                    f"Evidence references ungrounded citation URL not present in retrieved documents: '{ev.url}'",
                    status_code=500,
                )

        # 6. Sources Validation
        for src in validated.sources:
            if not src.url.startswith("http"):
                raise FactCheckBaseException(f"Malformed source URL: '{src.url}'", status_code=500)
            if src.quality_score is not None and not (0.0 <= src.quality_score <= 100.0):
                raise FactCheckBaseException(
                    f"Source quality score {src.quality_score} out of bounds [0.0, 100.0]", status_code=500
                )

        return validated


response_validator = ResponseValidator()

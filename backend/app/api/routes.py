from fastapi import APIRouter, status
from app.core.config import settings
from app.core.logging import logger
from app.schemas.factcheck import (
    FactCheckRequest,
    FactCheckResponse,
    HealthResponse,
    ErrorResponse,
)
from app.services.factcheck_service import factcheck_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Check service health",
    description="Returns the operational status, service name, version, and environment.",
)
async def health_check() -> HealthResponse:
    """Service health check endpoint returning service status."""
    return HealthResponse(
        status="healthy",
        service="aint-cappin-backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.post(
    "/v1/fact-check",
    response_model=FactCheckResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"model": ErrorResponse, "description": "Claim Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        502: {"model": ErrorResponse, "description": "External Provider Error"},
    },
    tags=["Fact Check"],
    summary="Fact-check a claim",
    description="Submits a claim to the fact-checking RAG pipeline for retrieval, evidence verification, and verdict generation.",
)
async def fact_check_endpoint(payload: FactCheckRequest) -> FactCheckResponse:
    """Fact-check endpoint that coordinates claim analysis, search retrieval, RAG, and reasoning."""
    logger.info("Received fact-check request for claim: '%s'", payload.claim[:60])
    response = await factcheck_service.verify_claim(payload)
    return response

import os
import sys
from pathlib import Path

# Ensure backend root directory is in sys.path so app can be imported
# whether invoked from backend/ or backend/app/
backend_root = str(Path(__file__).resolve().parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.errors import (
    FactCheckBaseException,
    custom_domain_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.core.logging import logger
from app.api.routes import router as api_router
from app.schemas.factcheck import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s in %s mode", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(FactCheckBaseException, custom_domain_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes with /api prefix
app.include_router(api_router, prefix="/api")


# Top-level /health route
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Check service health",
    description="Returns the operational status, service name, version, and environment.",
)
async def root_health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="aint-cappin-backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )

# ============================================================
# Ain't Cappin — Backend Dockerfile
# FastAPI + Uvicorn + FAISS + Sentence Transformers
# ============================================================

# --- Stage 1: Builder ---
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies required for building native packages
# (faiss-cpu, numpy, sentence-transformers all need build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into a prefix for clean copy
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: Runtime ---
FROM python:3.13-slim AS runtime

WORKDIR /app

# Install only the runtime system libraries needed (libgomp for faiss/numpy BLAS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY . .

# ---- Environment Variables ----
# Server / Runtime
ENV ENVIRONMENT=production
ENV PORT=8000

# CORS — update ALLOWED_ORIGINS to your Cloudflare Pages domain(s) in production
# e.g., "https://your-project.pages.dev,https://yourcustomdomain.com"
ENV ALLOWED_ORIGINS=https://your-project.pages.dev

# Search Provider API Keys (set at least one at runtime via Docker env / secret manager)
ENV TAVILY_API_KEY=""
ENV SERPAPI_API_KEY=""

# LLM Provider API Keys (set at least one at runtime)
ENV GEMINI_API_KEY=""
ENV GROQ_API_KEY=""
ENV OPENAI_API_KEY=""

# Hugging Face model cache directory (sentence-transformers downloads on first run)
# Mount a volume to /app/.cache in production to persist downloaded models
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers

# Create cache dir
RUN mkdir -p /app/.cache/huggingface /app/.cache/sentence_transformers

# Expose the application port
EXPOSE 8000

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch Uvicorn — dynamic port expansion so Northflank / Cloud Run / PaaS $PORT is respected
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info"]

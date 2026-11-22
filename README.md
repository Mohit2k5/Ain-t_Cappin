# Ain't Cappin — AI-Powered Grounded Fact-Checking

> **"Claim it. Check it. Prove it."**

Ain't Cappin is an AI-powered fact-checking system that takes social media claims, retrieves live evidence from authoritative web sources, vectorizes and ranks evidence passages via Retrieval-Augmented Generation (RAG) using FAISS, analyzes supporting vs. contradictory data, runs self-consistency cross-checks, and outputs an explainable verdict with citations and confidence metrics.

The system is designed with zero blind reliance on LLM pretrained knowledge: every factual conclusion must be grounded in retrievable, verifiable evidence.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│                   Frontend (React + Vite)              │
│       Claim Input • Verdict Card • Evidence Trace      │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP JSON / API
┌───────────────────────────▼────────────────────────────┐
│                    API Layer (FastAPI)                 │
│              Endpoints: /health, /api/v1/fact-check    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         Claim Analyzer (Entity & Query Generation)     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│        Web Search & Source Quality Evaluator           │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│       Document Processing, Chunking & Cleaning         │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         RAG Vector Pipeline (Sentence Transformers     │
│                     + FAISS Index)                     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│  Evidence Analyzer & Self-Consistency Cross-Checker    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│        Confidence Scorer & Verdict Generator           │
└────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Ain't_Cappin/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application & CORS configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py           # /health and /api/v1/fact-check endpoints
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── factcheck.py        # Pydantic request & response models
│   │   ├── services/               # Claim analyzer, search, RAG, consistency checker
│   │   │   └── __init__.py
│   │   └── utils/                  # Source quality & text cleaning utilities
│   │       └── __init__.py
│   ├── tests/
│   │   └── test_health.py          # API & route test suite
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Sample environment configuration
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Home.tsx            # Landing page with branding, claim input, status
│   │   ├── components/             # Reusable UI components
│   │   ├── services/
│   │   │   └── api.ts              # Axios HTTP client configuration
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css               # Tailwind CSS v4 directives
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

---

## Local Development Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v

# Start development server
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000` (API Docs at `http://localhost:8000/docs`).

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build verification
npm run build

# Start development server
npm run dev
```

The frontend web application will run at `http://localhost:5173`.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and supply relevant API keys for upcoming phases:
- `GEMINI_API_KEY` or alternate LLM provider
- `TAVILY_API_KEY` or `SERPAPI_API_KEY` for live search retrieval

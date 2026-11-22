import time
from typing import List, Set
from app.core.config import settings
from app.core.logging import logger
from app.schemas.factcheck import (
    FactCheckRequest,
    FactCheckResponse,
    VerdictEnum,
    SourceItem,
    EvidenceItem,
)
from app.services.claim_analyzer import claim_analyzer
from app.services.search_service import search_service
from app.services.document_processor import document_processor
from app.services.retriever import evidence_retriever
from app.services.context_builder import context_builder
from app.services.rag_service import rag_service
from app.services.evidence_analyzer import evidence_analyzer
from app.services.consistency_checker import consistency_checker
from app.services.confidence_scorer import confidence_scorer
from app.services.verdict_generator import verdict_generator
from app.services.response_validator import response_validator


class FactCheckService:
    """Orchestrates the complete 18-step fact-checking pipeline."""

    def __init__(self):
        logger.info("Initializing complete FactCheckService orchestrator...")

    async def verify_claim(self, request: FactCheckRequest) -> FactCheckResponse:
        """Coordinates the end-to-end verification lifecycle:
        1. Validate claim input
        2. Analyze claim entities, categories, and verification needs (ClaimAnalyzer)
        3. Generate multi-angle search queries
        4. Execute web search (SearchService)
        5. Evaluate source quality (SourceQualityEvaluator)
        6. Process documents and extract content (DocumentProcessor)
        7. Chunk documents into coherent passages (DocumentChunker)
        8. Generate vector embeddings (EmbeddingService)
        9. Create in-memory FAISS vector index (VectorStore)
        10. Retrieve top-k multi-angle evidence passages (EvidenceRetriever)
        11. Build structured prompt context with injection guardrails (ContextBuilder)
        12. Generate evidence-grounded preliminary assessment (RAGService)
        13. Analyze evidence relationships and weights (EvidenceAnalyzer)
        14. Run 3 independent analytical assessments (ConsistencyChecker)
        15. Calculate consensus agreement metrics
        16. Calculate canonical confidence score C = 0.35R + 0.30S + 0.20A + 0.15M (ConfidenceScorer)
        17. Generate final verdict, explanation, and limitations (VerdictGenerator)
        18. Validate schema, citation integrity, and boundaries (ResponseValidator)
        19. Return structured JSON result
        """
        start_time = time.time()
        logger.info("Initiating full fact-check workflow for claim: '%s'", request.claim[:60])

        # Step 1 & 2 & 3: Claim Analysis & Multi-Query Generation
        analysis = claim_analyzer.analyze(request.claim)
        logger.info(
            "Step 2-3: Claim classified as '%s' (Entities: %d, Queries: %d)",
            analysis.category.value,
            len(analysis.entities),
            len(analysis.search_queries),
        )

        # Step 4 & 5: Web Search & Source Quality Evaluation
        search_candidates = await search_service.execute_searches(analysis.search_queries[:3])
        logger.info("Step 4-5: Retrieved and evaluated %d candidate documents.", len(search_candidates))

        # Step 6: Document Fetching & Sanitization
        processed_documents = await document_processor.process_candidates(search_candidates[:4])
        total_extracted_chars = sum(doc.cleaned_length for doc in processed_documents)
        logger.info(
            "Step 6: Extracted and cleaned %d documents (%d chars total).",
            len(processed_documents),
            total_extracted_chars,
        )

        # Track allowed citation URLs for validation
        allowed_source_urls: Set[str] = {doc.url for doc in processed_documents}
        for cand in search_candidates:
            allowed_source_urls.add(cand.url)

        # Step 7, 8, 9, 10: Chunking, Embeddings, FAISS Index, and Semantic Evidence Retrieval
        retrieved_passages = evidence_retriever.retrieve_evidence(
            claim=request.claim,
            documents=processed_documents,
            search_queries=analysis.search_queries,
        )
        logger.info("Step 7-10: Retrieved %d vector-ranked evidence passages.", len(retrieved_passages))

        for p in retrieved_passages:
            allowed_source_urls.add(p.chunk.document_url)

        # Step 11: Context Assembly with Security Isolation
        rag_context = context_builder.build_context(request.claim, retrieved_passages)

        # Step 12: Grounded RAG Assessment
        rag_assessment = await rag_service.assess_evidence(rag_context)
        logger.info("Step 12: Grounded RAG evaluation: %s", rag_assessment.preliminary_verdict)

        # Step 13: Detailed Evidence Relationship Analysis
        evidence_summary = evidence_analyzer.analyze_evidence(
            claim=request.claim,
            passages=retrieved_passages,
            rag_assessment=rag_assessment,
        )
        logger.info(
            "Step 13: Evidence balance: sup=%.2f, con=%.2f, agreement=%.1f%%",
            evidence_summary.supporting_weight,
            evidence_summary.contradicting_weight,
            evidence_summary.evidence_agreement_score,
        )

        # Step 14 & 15: Self-Consistency Cross-Checks across 3 Perspectives
        consistency_result = consistency_checker.evaluate_consistency(
            claim=request.claim,
            rag_context=rag_context,
            evidence_summary=evidence_summary,
        )
        logger.info(
            "Step 14-15: Consistency agreement: %d/%d (%.1f%%) -> Majority: %s",
            consistency_result.agreement.agreeing,
            consistency_result.agreement.total,
            consistency_result.agreement.percentage,
            consistency_result.majority_verdict.value,
        )

        # Step 16: Assemble Sources List
        seen_source_urls = set()
        sources: List[SourceItem] = []
        for p in retrieved_passages:
            url = p.chunk.document_url
            if url not in seen_source_urls:
                seen_source_urls.add(url)
                matching_doc = next((d for d in processed_documents if d.url == url), None)
                quality_score = matching_doc.source_quality.quality_score if matching_doc and matching_doc.source_quality else 60.0
                sources.append(
                    SourceItem(
                        name=p.chunk.document_title or p.chunk.domain,
                        domain=p.chunk.domain,
                        url=url,
                        publication_date=matching_doc.publication_date if matching_doc else None,
                        quality_score=quality_score,
                    )
                )

        # If retrieved passages were empty, include candidate search sources
        if not sources:
            for cand in search_candidates[:3]:
                if cand.url not in seen_source_urls:
                    seen_source_urls.add(cand.url)
                    sources.append(
                        SourceItem(
                            name=cand.source_name or cand.domain,
                            domain=cand.domain,
                            url=cand.url,
                            publication_date=cand.publication_date,
                            quality_score=cand.quality_assessment.quality_score if cand.quality_assessment else 50.0,
                        )
                    )

        # Step 16: Canonical Confidence Scoring C = 0.35R + 0.30S + 0.20A + 0.15M
        confidence = confidence_scorer.calculate_confidence(
            passages=retrieved_passages,
            sources=sources,
            evidence_summary=evidence_summary,
            consistency_result=consistency_result,
        )

        # Step 17: Final Verdict Synthesis
        generated_verdict = verdict_generator.generate(
            claim=request.claim,
            evidence_summary=evidence_summary,
            consistency_result=consistency_result,
            sources=sources,
            rag_assessment=rag_assessment,
        )

        # Limitations list
        limitations = [
            f"Topic Category: {analysis.category.value}",
            f"Passages Analyzed: {len(evidence_summary.analyzed_items)}",
        ] + generated_verdict.limitations

        elapsed = round(time.time() - start_time, 3)

        raw_response = FactCheckResponse(
            claim=request.claim,
            verdict=generated_verdict.verdict,
            explanation=generated_verdict.explanation,
            evidence=evidence_summary.analyzed_items,
            sources=sources,
            confidence=confidence,
            assessment_agreement=consistency_result.agreement,
            limitations=limitations,
            processing_metadata={
                "pipeline_version": "1.0.0",
                "execution_time_seconds": elapsed,
                "processing_time_ms": int(elapsed * 1000),
                "category": analysis.category.value,
                "entities": analysis.entities,
                "search_queries": analysis.search_queries,
                "queries_executed": analysis.search_queries,
                "total_sources_found": len(search_candidates),
                "candidate_sources_found": len(search_candidates),
                "total_documents_processed": len(processed_documents),
                "documents_processed": len(processed_documents),
                "total_text_length": total_extracted_chars,
                "total_chunks_indexed": len(retrieved_passages),
                "retrieved_passages_count": len(retrieved_passages),
                "passages_retrieved": len(retrieved_passages),
                "unique_sources": len(sources),
                "is_insufficient_evidence": rag_assessment.is_insufficient_evidence,
                "consistency_notes": consistency_result.synthesis_notes,
                "embedding_model": "all-MiniLM-L6-v2 (384-dim)",
                "llm_model": "Gemini-2.5-Flash (Grounded RAG)" if settings.GEMINI_API_KEY else "Deterministic Grounded Engine",
            },
        )

        # Step 18: Response Validation
        validated_response = response_validator.validate_response(raw_response, allowed_source_urls)
        logger.info(
            "Step 18-19: Pipeline complete in %.3fs -> Verdict: %s (Confidence: %s, %.1f)",
            elapsed,
            validated_response.verdict.value,
            validated_response.confidence.level.value,
            validated_response.confidence.score,
        )
        return validated_response


factcheck_service = FactCheckService()

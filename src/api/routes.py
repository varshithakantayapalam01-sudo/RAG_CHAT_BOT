from __future__ import annotations

"""
API Layer — Route Definitions

Implements endpoints for:
  - POST /api/chat: Processes user queries via Guardrails & RAG Pipeline
  - GET /api/health: Returns API and vector store health check metrics
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from src.api.models import ChatRequest, ChatResponse, HealthResponse, VectorStoreStatus
from src.ingestion.indexer import get_collection_stats
from src.pipeline.guardrails import Guardrails
from src.pipeline.rag_chain import RAGPipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_FILE = PROJECT_ROOT / "data" / "metadata.json"

router = APIRouter()

# Singletons reused across request lifecycles
rag_pipeline = RAGPipeline()
guardrails = Guardrails()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Route handler for processing user mutual fund queries.

    First checks query against local guardrails. If all pass, forwards
    the request to the main RAG retrieval & generation chain.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # 1. Run Guardrails Check
        refusal = guardrails.check_query(query)
        if refusal:
            return ChatResponse(
                status=refusal["status"],
                type=refusal["type"],
                answer=refusal["answer"],
                citation=refusal.get("citation"),
                educational_link=refusal.get("educational_link"),
                footer=refusal["footer"],
            )

        # 2. Run RAG Pipeline
        result = rag_pipeline.run(query)
        return ChatResponse(
            status=result["status"],
            type=result["type"],
            answer=result["answer"],
            citation=result.get("citation"),
            educational_link=result.get("educational_link"),
            footer=result["footer"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected internal error occurred: {e}",
        )


@router.get("/health", response_model=HealthResponse)
async def health_endpoint() -> HealthResponse:
    """Route handler for system health and vector store indexing status."""
    try:
        stats = get_collection_stats()
        last_ingestion = None
        last_collected = None

        if METADATA_FILE.exists():
            try:
                with open(METADATA_FILE, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                corpus_stats = meta.get("corpus_stats", {})
                last_collected = corpus_stats.get("last_collected")
                last_ingestion = corpus_stats.get("last_ingested") or last_collected
            except Exception:
                pass

        return HealthResponse(
            status="healthy",
            vectorstore=VectorStoreStatus(
                collection_name=stats["collection_name"],
                document_count=stats["count"],
                persist_directory=stats["persist_dir"],
            ),
            last_ingestion=last_ingestion,
            last_collected=last_collected,
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            error=str(e),
        )


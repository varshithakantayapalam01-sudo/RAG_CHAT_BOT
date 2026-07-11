from __future__ import annotations

"""
RAG Query Pipeline — Retriever Component

Implements semantic search using:
  1. ChromaDB vector search (top-K cosine similarity)
  2. BGE-specific query prefix formatting
  3. Similarity threshold filtering (s >= 0.65)
  4. Cross-Encoder re-ranking (top-3 final chunks)
"""

import chromadb
from sentence_transformers import CrossEncoder

from src.config import (
    TOP_K,
    SIMILARITY_THRESHOLD,
    RERANK_TOP_N,
    RERANKER_MODEL_NAME,
)
from src.ingestion.indexer import get_or_create_collection


class Retriever:
    """Retriever class responsible for fetching relevant context chunks."""

    def __init__(self, collection: chromadb.Collection | None = None) -> None:
        """Initialize the retriever with a ChromaDB collection and cross-encoder."""
        self.collection = collection or get_or_create_collection()
        self.reranker = CrossEncoder(RERANKER_MODEL_NAME)

    def retrieve(self, query: str) -> list[dict]:
        """Retrieve the top re-ranked chunks matching the query.

        Args:
            query: The user's query text.

        Returns:
            List of dicts representing the top chunks, each containing:
              - 'text': Chunk content
              - 'metadata': Sanitized chunk metadata dict
              - 'similarity': Cosine similarity score
              - 'rerank_score': Cross-encoder re-ranked score
        """
        # 1. Query Preprocessing & Instruction Prefix (mandatory for BGE query mode)
        prefixed_query = f"Represent this sentence for searching relevant passages: {query}"

        # 2. Dense Vector Search (ChromaDB)
        results = self.collection.query(
            query_texts=[prefixed_query],
            n_results=TOP_K,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return []

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        # 3. Cosine similarity = 1 - cosine distance
        candidates: list[dict] = []
        for doc, meta, dist in zip(docs, metas, dists):
            similarity = 1.0 - float(dist)
            
            # 4. Filter by minimum similarity threshold
            if similarity >= SIMILARITY_THRESHOLD:
                candidates.append({
                    "text": doc,
                    "metadata": meta,
                    "similarity": similarity,
                })

        if not candidates:
            return []

        # 5. Cross-Encoder Re-Ranking
        pairs = [(query, c["text"]) for c in candidates]
        rerank_scores = self.reranker.predict(pairs)

        # Predict returns single float if list length is 1, or numpy array
        if isinstance(rerank_scores, float):
            rerank_scores = [rerank_scores]

        for idx, score in enumerate(rerank_scores):
            candidates[idx]["rerank_score"] = float(score)

        # Sort candidates descending by re-rank score
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        return candidates[:RERANK_TOP_N]

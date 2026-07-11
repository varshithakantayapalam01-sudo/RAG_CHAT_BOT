from __future__ import annotations

"""
Unit Tests for Phase 4 — Retriever Component

Tests semantic search retrieval, threshold pruning, and cross-encoder sorting.
"""

import pytest

from src.pipeline.retriever import Retriever


@pytest.fixture
def retriever() -> Retriever:
    """Return a Retriever instance."""
    return Retriever()


def test_retriever_successful_query(retriever: Retriever) -> None:
    """Test retrieval for a highly relevant factual query."""
    query = "What is the expense ratio of HDFC Mid-Cap Fund?"
    results = retriever.retrieve(query)

    # Validate we get results (at most RERANK_TOP_N = 3)
    assert len(results) > 0
    assert len(results) <= 3

    # Check structure of results
    for res in results:
        assert "text" in res
        assert "metadata" in res
        assert "similarity" in res
        assert "rerank_score" in res
        
        # Verify similarity is above SIMILARITY_THRESHOLD = 0.65
        assert res["similarity"] >= 0.65
        # Verify source metadata exists
        meta = res["metadata"]
        assert "scheme_name" in meta
        assert "source_url" in meta

    # Verify results are sorted by rerank_score in descending order
    scores = [res["rerank_score"] for res in results]
    assert scores == sorted(scores, reverse=True)


def test_retriever_threshold_pruning(retriever: Retriever) -> None:
    """Test that unrelated queries are filtered out by the similarity threshold."""
    query = "How to implement quicksort in Python programming language?"
    results = retriever.retrieve(query)

    # Quicksort should have no relation to HDFC Mutual Fund facts and get pruned
    assert len(results) == 0

from __future__ import annotations

"""
Unit Tests for Phase 4 — Post-Processor Component

Tests sentence limit enforcement, citation extraction/cleanup, and fallback formatting.
"""

from src.pipeline.postprocessor import PostProcessor


def test_postprocessor_sentence_limiting() -> None:
    """Test that responses are truncated to a maximum of 3 sentences."""
    postprocessor = PostProcessor(max_sentences=3)
    raw = "Sentence one. Sentence two. Sentence three! Sentence four? Sentence five."
    retrieved = [
        {"metadata": {"source_url": "https://url.com", "downloaded_at": "2026-07-11"}}
    ]

    res = postprocessor.postprocess(raw, retrieved)
    assert res["answer"] == "Sentence one. Sentence two. Sentence three!"


def test_postprocessor_citation_extraction() -> None:
    """Test that cited URLs are extracted and cleaned from the text body."""
    postprocessor = PostProcessor()
    url = "https://groww.in/mutual-funds/hdfc-mid-cap"
    raw = f"The AUM is 1000 Cr. Source: {url}"
    retrieved = [
        {"metadata": {"source_url": url, "downloaded_at": "2026-07-11"}}
    ]

    res = postprocessor.postprocess(raw, retrieved)
    assert res["citation"] == url
    assert res["answer"] == "The AUM is 1000 Cr."
    assert res["footer"] == "Last updated from sources: 2026-07-11"


def test_postprocessor_fallback() -> None:
    """Test that fallback messages return clean status and empty citation/footers."""
    postprocessor = PostProcessor()
    raw = "I don't have enough information to answer this from my sources."
    retrieved = [
        {"metadata": {"source_url": "https://url.com", "downloaded_at": "2026-07-11"}}
    ]

    res = postprocessor.postprocess(raw, retrieved)
    assert res["answer"] == "I don't have enough information to answer this from my sources."
    assert res["citation"] is None
    assert res["footer"] == ""

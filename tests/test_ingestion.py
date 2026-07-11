"""
Unit Tests for Phase 3 — Ingestion Pipeline

Tests the scraper/loader, chunker, and indexer modules using pytest.
Uses temporary directories to avoid polluting production vector stores.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import pytest

from src.ingestion.scraper import _flatten_json_to_text, _build_metadata
from src.ingestion.chunker import chunk_document, chunk_all_documents
from src.ingestion.indexer import index_chunks, _sanitize_metadata, get_or_create_collection


@pytest.fixture
def sample_source_data() -> tuple[dict, dict]:
    """Return a mock metadata source entry and raw scheme details JSON."""
    source = {
        "id": "test_scheme",
        "url": "https://groww.in/mutual-funds/test-scheme",
        "scheme": "Test Mutual Fund - Direct Growth",
        "category": "Debt",
        "format": "html",
        "downloaded_at": "2026-07-11T20:00:00Z",
    }
    details = {
        "scheme_name": "Test Mutual Fund - Direct Growth",
        "amc_name": "Test AMC",
        "category": "Debt",
        "sub_category": "Liquid",
        "plan_type": "Direct",
        "scheme_type": "Growth",
        "launch_date": "01-Jan-2020",
        "benchmark": "NIFTY Liquid Index",
        "risk_level": "Low",
        "fund_manager": "John Doe",
        "isin": "INF000000001",
        "description": "A low risk liquid fund.",
        "nav": {
            "current_nav": 100.0,
            "nav_date": "10-Jul-2026",
        },
        "expense_ratio": "0.25",
        "exit_load": "Nil",
        "stamp_duty": "0.005%",
        "aum": 1000.0,
        "min_investment": {
            "lumpsum": 1000,
            "sip": 500,
            "additional": 1000,
        },
        "lock_in": {
            "years": 0,
            "months": 0,
            "days": 0,
        },
        "top_holdings": [
            {"name": "GOI Sovereign Bond", "sector": "Sovereign", "percentage": 15.5, "instrument_type": "Bond"},
            {"name": "T-Bills", "sector": "Sovereign", "percentage": 10.2, "instrument_type": "Bill"},
        ],
        "fund_manager_details": [
            {"name": "John Doe", "experience": "10 years in debt fund management."}
        ]
    }
    return source, details


# ───────────────────────────────────────────────────────────
# Scraper / Flattening Tests
# ───────────────────────────────────────────────────────────

def test_scraper_flattening(sample_source_data):
    source, details = sample_source_data
    text = _flatten_json_to_text(details, source)
    
    # Assertions on natural-language generation
    assert "Test Mutual Fund - Direct Growth" in text
    assert "Test AMC" in text
    assert "NIFTY Liquid Index" in text
    assert "100.0" in text
    assert "0.25%" in text
    assert "GOI Sovereign Bond" in text
    assert "15.5%" in text
    assert "John Doe" in text


def test_scraper_metadata(sample_source_data):
    source, _ = sample_source_data
    metadata = _build_metadata(source)
    
    assert metadata["source_id"] == "test_scheme"
    assert metadata["scheme_name"] == "Test Mutual Fund - Direct Growth"
    assert metadata["source_url"] == "https://groww.in/mutual-funds/test-scheme"
    assert "ingestion_date" in metadata


# ───────────────────────────────────────────────────────────
# Chunker Tests
# ───────────────────────────────────────────────────────────

def test_chunker_basic(sample_source_data):
    source, details = sample_source_data
    text = _flatten_json_to_text(details, source)
    metadata = _build_metadata(source)
    
    chunks = chunk_document(text, metadata, chunk_size=500, chunk_overlap=50)
    
    assert len(chunks) > 0
    for idx, chunk in enumerate(chunks):
        assert "text" in chunk
        assert chunk["chunk_id"] == f"test_scheme_chunk_{idx}"
        assert chunk["chunk_index"] == idx
        assert chunk["total_chunks"] == len(chunks)
        assert chunk["scheme_name"] == "Test Mutual Fund - Direct Growth"
        assert chunk["source_url"] == "https://groww.in/mutual-funds/test-scheme"


def test_chunk_all_documents(sample_source_data):
    source, details = sample_source_data
    text = _flatten_json_to_text(details, source)
    metadata = _build_metadata(source)
    
    documents = [(text, metadata)]
    chunks = chunk_all_documents(documents, chunk_size=500, chunk_overlap=50)
    
    assert len(chunks) > 0
    assert chunks[0]["source_id"] == "test_scheme"


# ───────────────────────────────────────────────────────────
# Indexer & Metadata Sanitization Tests
# ───────────────────────────────────────────────────────────

def test_metadata_sanitization():
    meta = {
        "valid_str": "hello",
        "valid_int": 42,
        "valid_float": 3.14,
        "valid_bool": True,
        "invalid_none": None,
        "invalid_list": [1, 2, 3],
        "invalid_dict": {"key": "val"},
    }
    
    clean = _sanitize_metadata(meta)
    
    assert clean["valid_str"] == "hello"
    assert clean["valid_int"] == 42
    assert clean["valid_float"] == 3.14
    assert clean["valid_bool"] is True
    
    assert "invalid_none" not in clean
    assert clean["invalid_list"] == "[1, 2, 3]"
    assert clean["invalid_dict"] == "{'key': 'val'}"


def test_indexer_roundtrip(sample_source_data):
    # Setup temporary directory for vectorstore
    temp_dir = tempfile.mkdtemp()
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path=temp_dir)
        collection = get_or_create_collection(client, "test_collection")
        
        source, details = sample_source_data
        text = _flatten_json_to_text(details, source)
        metadata = _build_metadata(source)
        
        chunks = chunk_document(text, metadata, chunk_size=500, chunk_overlap=50)
        
        # Test index upsert
        indexed = index_chunks(chunks, collection)
        assert indexed == len(chunks)
        assert collection.count() == len(chunks)
        
        # Test retrieval
        results = collection.get(limit=1, include=["documents", "metadatas"])
        assert len(results["documents"]) == 1
        assert results["metadatas"][0]["scheme_name"] == "Test Mutual Fund - Direct Growth"
        
    finally:
        # Clean up temporary directory (ignore errors on Windows due to locked db files)
        shutil.rmtree(temp_dir, ignore_errors=True)

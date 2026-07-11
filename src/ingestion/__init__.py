"""
Ingestion Package

Modules for loading, chunking, and indexing mutual fund
scheme data into the ChromaDB vector store.

Public API:
  - scraper:  load_all_documents, load_document_from_json, load_document_from_text
  - chunker:  chunk_document, chunk_all_documents
  - indexer:  index_chunks, get_or_create_collection, get_collection_stats
"""

from src.ingestion.scraper import load_all_documents  # noqa: F401
from src.ingestion.chunker import chunk_all_documents  # noqa: F401
from src.ingestion.indexer import index_chunks, get_collection_stats  # noqa: F401

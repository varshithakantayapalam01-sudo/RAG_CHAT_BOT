from __future__ import annotations

"""
Ingestion — Text Chunker

Splits full document text into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter.  Each chunk inherits the parent document's
metadata and is assigned a unique chunk_id + positional index.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHUNK_SIZE, CHUNK_OVERLAP


def create_text_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> RecursiveCharacterTextSplitter:
    """Create a configured RecursiveCharacterTextSplitter.

    Args:
        chunk_size:    Maximum characters per chunk (default from config).
        chunk_overlap: Overlap between consecutive chunks (default from config).

    Returns:
        A ready-to-use text splitter instance.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or CHUNK_SIZE,
        chunk_overlap=chunk_overlap or CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        is_separator_regex=False,
    )


def chunk_document(
    text: str,
    metadata: dict,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict]:
    """Split a single document into chunks with metadata.

    Each chunk dict contains:
      - ``text``:         The chunk content.
      - ``chunk_id``:     ``<source_id>_chunk_<index>``
      - ``chunk_index``:  0-based position in the document.
      - ``total_chunks``: How many chunks the document was split into.
      - All keys from the parent ``metadata`` dict.

    Args:
        text:          Full document text.
        metadata:      Metadata dict from the scraper/loader.
        chunk_size:    Override CHUNK_SIZE.
        chunk_overlap: Override CHUNK_OVERLAP.

    Returns:
        List of chunk dicts.
    """
    splitter = create_text_splitter(chunk_size, chunk_overlap)
    raw_chunks: list[str] = splitter.split_text(text)

    source_id = metadata.get("source_id", "unknown")
    chunks: list[dict] = []

    for idx, chunk_text in enumerate(raw_chunks):
        chunk = {
            "text": chunk_text,
            "chunk_id": f"{source_id}_chunk_{idx}",
            "chunk_index": idx,
            "total_chunks": len(raw_chunks),
            **metadata,  # inherit all parent metadata
        }
        chunks.append(chunk)

    return chunks


def chunk_all_documents(
    documents: list[tuple[str, dict]],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict]:
    """Chunk a list of (text, metadata) tuples.

    Args:
        documents:     List of (text, metadata) from the scraper.
        chunk_size:    Override CHUNK_SIZE.
        chunk_overlap: Override CHUNK_OVERLAP.

    Returns:
        Flat list of all chunk dicts across all documents.
    """
    all_chunks: list[dict] = []

    for text, metadata in documents:
        doc_chunks = chunk_document(text, metadata, chunk_size, chunk_overlap)
        all_chunks.extend(doc_chunks)

    return all_chunks

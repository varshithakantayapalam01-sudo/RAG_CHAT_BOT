"""
Phase 3 — View Embeddings Script

Fetches sample chunks from the persistent ChromaDB collection and displays
their raw embedding vectors (dimension counts, shapes, and snippet values).

Usage:
    python scripts/view_embeddings.py [--limit 3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.indexer import get_or_create_collection, get_collection_stats


def main() -> None:
    # Ensure console output handles unicode correctly on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="View raw embedding vectors for indexed chunks."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=2,
        help="Number of chunk embeddings to display.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ChromaDB Embedding Viewer")
    print("=" * 60)

    # ── 1. Load Collection ──
    stats = get_collection_stats()
    print(f"\nCollection Stats:")
    print(f"  Name:        {stats['collection_name']}")
    print(f"  Total Docs:  {stats['count']}")
    
    if stats["count"] == 0:
        print("\n[ERROR] Collection is empty! Run 'python scripts/run_ingestion.py' first.")
        sys.exit(1)

    collection = get_or_create_collection()

    # ── 2. Retrieve Sample Chunks with Embeddings ──
    limit = min(args.limit, stats["count"])
    print(f"\nRetrieving {limit} sample chunks with embeddings...\n")

    results = collection.get(
        limit=limit,
        include=["documents", "metadatas", "embeddings"],
    )

    ids = results["ids"]
    docs = results["documents"]
    metas = results["metadatas"]
    embeddings = results["embeddings"]

    if embeddings is None or len(embeddings) == 0:
        print("[ERROR] No embeddings returned. Ensure ChromaDB persists vectors correctly.")
        sys.exit(1)

    for i in range(limit):
        chunk_id = ids[i]
        text = docs[i]
        meta = metas[i]
        vector = embeddings[i]

        scheme = meta.get("scheme_name", "Unknown")
        section = meta.get("category", "N/A")
        
        # Display Info
        print("-" * 60)
        print(f"Chunk {i+1} ID:   {chunk_id}")
        print(f"Scheme:       {scheme}")
        print(f"Section Type: {section}")
        print(f"Snippet:      {text[:120].strip()}...")
        print(f"Vector Shape: [{len(vector)}] (Expected: 384 dimensions for BGE Small)")
        
        # Print first 10 dimensions of float values
        preview_dim = min(10, len(vector))
        vector_preview = [round(float(val), 6) for val in vector[:preview_dim]]
        print(f"Vector Preview (first {preview_dim} values):")
        print(f"  {vector_preview}")
        print("-" * 60)


if __name__ == "__main__":
    main()

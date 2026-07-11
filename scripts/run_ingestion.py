"""
Phase 3 — Ingestion Orchestration Script

End-to-end pipeline:
  1. Load all processed scheme data  (scraper)
  2. Chunk into overlapping passages  (chunker)
  3. Embed + upsert into ChromaDB     (indexer)

Usage:
    python scripts/run_ingestion.py [--clean] [--mode json|text]
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.scraper import load_all_documents
from src.ingestion.chunker import chunk_all_documents
from src.ingestion.indexer import (
    clear_collection,
    get_collection_stats,
    index_chunks,
)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Run the full ingestion pipeline (load → chunk → index)."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing collection before indexing (clean re-ingestion).",
    )
    parser.add_argument(
        "--mode",
        choices=["json", "text"],
        default="json",
        help="Loading mode: 'json' (structured → NL) or 'text' (raw .txt). Default: json.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Phase 3 — Ingestion Pipeline")
    print("=" * 60)

    t0 = time.perf_counter()

    # -- Step 0: Optionally clean existing collection --
    if args.clean:
        print("\n[1/4] Clearing existing collection...")
        clear_collection()
        print("  [OK] Collection cleared.")
    else:
        print("\n[1/4] Using existing collection (pass --clean to reset).")

    # -- Step 1: Load processed documents --
    print(f"\n[2/4] Loading documents (mode={args.mode})...")
    documents = load_all_documents(mode=args.mode)
    if not documents:
        print("  [ERROR] No documents found. Run Phase 2 scripts first.")
        sys.exit(1)
    total_chars = sum(len(t) for t, _ in documents)
    print(f"  [OK] Loaded {len(documents)} documents ({total_chars:,} chars total)")
    for text, meta in documents:
        print(f"    * {meta['scheme_name']} ({len(text):,} chars)")

    # -- Step 2: Chunk --
    print("\n[3/4] Chunking documents...")
    chunks = chunk_all_documents(documents)
    if not chunks:
        print("  [ERROR] Chunking produced 0 chunks - something is wrong.")
        sys.exit(1)
    print(f"  [OK] Created {len(chunks)} chunks")

    # Per-document breakdown
    from collections import Counter
    doc_counts = Counter(c["source_id"] for c in chunks)
    for doc_id, count in doc_counts.items():
        print(f"    * {doc_id}: {count} chunks")

    avg_len = sum(len(c["text"]) for c in chunks) / len(chunks)
    print(f"  Average chunk length: {avg_len:.0f} chars")

    # -- Step 3: Index --
    print("\n[4/4] Embedding + indexing into ChromaDB...")
    indexed = index_chunks(chunks)
    print(f"  [OK] Upserted {indexed} chunks into ChromaDB")

    # Update metadata.json with last_ingested timestamp
    metadata_file = PROJECT_ROOT / "data" / "metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            if "corpus_stats" not in metadata:
                metadata["corpus_stats"] = {}
            metadata["corpus_stats"]["last_ingested"] = datetime.now(timezone.utc).isoformat()
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  [WARNING] Failed to update metadata.json: {e}")

    # ── Summary ──
    stats = get_collection_stats()
    elapsed = time.perf_counter() - t0

    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print(f"  Collection:   {stats['collection_name']}")
    print(f"  Total chunks: {stats['count']}")
    print(f"  Persist dir:  {stats['persist_dir']}")
    print(f"  Elapsed:      {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()

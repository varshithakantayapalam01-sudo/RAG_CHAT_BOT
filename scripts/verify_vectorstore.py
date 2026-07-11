"""
Phase 3 — Vector Store Verification Script

Validates the ChromaDB collection after ingestion:
  1. Reports collection stats (chunk count, persist dir)
  2. Shows per-scheme chunk distribution
  3. Displays sample chunks
  4. Runs a test similarity query to verify retrieval quality

Usage:
    python scripts/verify_vectorstore.py [--query "your test query"]
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.indexer import get_or_create_collection, get_collection_stats


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Verify the ChromaDB vector store after ingestion."
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What is the expense ratio of HDFC Mid-Cap Fund?",
        help="A test query to run against the vector store.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to retrieve (default: 5).",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Vector Store Verification")
    print("=" * 60)

    # ── 1. Collection Stats ──
    stats = get_collection_stats()
    print(f"\n1. Collection Stats")
    print(f"   Name:        {stats['collection_name']}")
    print(f"   Total Docs:  {stats['count']}")
    print(f"   Persist Dir: {stats['persist_dir']}")

    if stats["count"] == 0:
        print("\n   [ERROR] Collection is empty! Run 'python scripts/run_ingestion.py' first.")
        sys.exit(1)

    # -- 2. Per-scheme distribution --
    collection = get_or_create_collection()
    all_data = collection.get(include=["metadatas"])

    scheme_counts: dict[str, int] = {}
    for meta in all_data["metadatas"]:
        scheme = meta.get("scheme_name", "Unknown")
        scheme_counts[scheme] = scheme_counts.get(scheme, 0) + 1

    print(f"\n2. Chunks Per Scheme")
    for scheme, count in sorted(scheme_counts.items()):
        print(f"   * {scheme}: {count} chunks")

    # -- 3. Sample chunks --
    print(f"\n3. Sample Chunks (first 3)")
    sample = collection.get(limit=3, include=["documents", "metadatas"])
    for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"])):
        print(f"\n   --- Chunk {i+1} ---")
        print(f"   Scheme:  {meta.get('scheme_name', 'N/A')}")
        print(f"   Source:  {meta.get('source_url', 'N/A')}")
        print(f"   Index:   {meta.get('chunk_index', '?')}/{meta.get('total_chunks', '?')}")
        # Truncate display
        display = doc[:200] + "..." if len(doc) > 200 else doc
        print(f"   Text:    {display}")

    # -- 4. Test similarity query --
    print(f"\n4. Test Query: \"{args.query}\"")
    print(f"   Retrieving top-{args.top_k} results...\n")

    # Apply BGE query instruction prefix for bi-encoder retrieval
    prefixed_query = f"Represent this sentence for searching relevant passages: {args.query}"
    results = collection.query(
        query_texts=[prefixed_query],
        n_results=min(args.top_k, stats["count"]),
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
        # ChromaDB returns cosine distance; similarity = 1 - distance
        similarity = 1 - dist
        print(f"   Result {i+1} (similarity: {similarity:.4f})")
        print(f"     Scheme: {meta.get('scheme_name', 'N/A')}")
        print(f"     Source: {meta.get('source_url', 'N/A')}")
        display = doc[:200] + "..." if len(doc) > 200 else doc
        print(f"     Text:   {display}")
        print()

    # -- Summary --
    print("=" * 60)
    total = stats["count"]
    if 30 <= total <= 1000:
        print(f"[OK] Verification PASSED - {total} chunks indexed across {len(scheme_counts)} schemes.")
    else:
        print(f"[WARN] Unexpected chunk count: {total}. Expected 30-1000.")
    print("=" * 60)


if __name__ == "__main__":
    main()

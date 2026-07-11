"""
Phase 2.3 — Download raw HTML from Groww source URLs.

Reads URLs from data/metadata.json and saves raw HTML to data/raw/groww/.
Updates metadata.json with download status and timestamps.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests

METADATA_FILE = PROJECT_ROOT / "data" / "metadata.json"
RAW_GROWW_DIR = PROJECT_ROOT / "data" / "raw" / "groww"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 30  # seconds


def load_metadata() -> dict:
    """Load the source URL registry."""
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_metadata(metadata: dict) -> None:
    """Save updated metadata back to file."""
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def download_page(url: str, output_path: Path) -> dict:
    """Download a single URL and save raw HTML.

    Returns:
        dict with keys: success, status_code, content_length, error
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Save raw HTML
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        return {
            "success": True,
            "status_code": response.status_code,
            "content_length": len(response.text),
            "error": None,
        }

    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "status_code": e.response.status_code if e.response else None,
            "content_length": 0,
            "error": f"HTTP Error: {e}",
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "status_code": None,
            "content_length": 0,
            "error": f"Connection Error: {e}",
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": None,
            "content_length": 0,
            "error": f"Timeout after {REQUEST_TIMEOUT}s",
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "content_length": 0,
            "error": str(e),
        }


def main():
    """Download all source URLs and update metadata."""
    print("=" * 60)
    print("Phase 2.3 - Downloading Groww Source Pages")
    print("=" * 60)

    metadata = load_metadata()
    sources = metadata["sources"]
    now = datetime.now(timezone.utc).isoformat()

    success_count = 0
    fail_count = 0

    for source in sources:
        source_id = source["id"]
        url = source["url"]
        scheme = source["scheme"]

        # Output filename: e.g., groww_hdfc_midcap.html
        output_file = RAW_GROWW_DIR / f"{source_id}.html"

        print(f"\n[{source_id}] {scheme}")
        print(f"  URL: {url}")
        print(f"  Saving to: {output_file.relative_to(PROJECT_ROOT)}")

        result = download_page(url, output_file)

        if result["success"]:
            print(f"  Status: {result['status_code']} OK")
            print(f"  Size: {result['content_length']:,} chars")
            source["status"] = "downloaded"
            source["downloaded_at"] = now
            source["raw_file"] = str(output_file.relative_to(PROJECT_ROOT))
            source["content_length"] = result["content_length"]
            success_count += 1
        else:
            print(f"  FAILED: {result['error']}")
            source["status"] = "failed"
            source["error"] = result["error"]
            fail_count += 1

    # Update corpus stats
    metadata["corpus_stats"]["last_collected"] = now

    # Save updated metadata
    save_metadata(metadata)

    # Summary
    print("\n" + "=" * 60)
    print(f"Download Summary:")
    print(f"  Total:   {len(sources)}")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {fail_count}")
    print(f"  Metadata updated: {METADATA_FILE.relative_to(PROJECT_ROOT)}")
    print("=" * 60)

    if fail_count > 0:
        print("\nWARNING: Some downloads failed. Check metadata.json for details.")
        sys.exit(1)

    print("\nAll source pages downloaded successfully!")


if __name__ == "__main__":
    main()

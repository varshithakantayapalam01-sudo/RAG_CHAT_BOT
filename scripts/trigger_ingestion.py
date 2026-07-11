"""
Phase 10 — Ingestion Trigger Orchestration

Runs the entire ingestion pipeline:
1. scripts/download_sources.py
2. scripts/extract_text.py
3. scripts/run_ingestion.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_script(script_name: str, args: list = None) -> int:
    """Run a python script in a subprocess, forwarding output and returning status."""
    script_path = PROJECT_ROOT / "scripts" / script_name
    if not script_path.exists():
        print(f"Error: script not found at {script_path}")
        sys.exit(1)

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print("\n" + "=" * 60)
    print(f"Executing: {script_name} {' '.join(args or [])}")
    print("=" * 60)

    # Run and stream stdout/stderr directly to parent process console
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"\n[ERROR] Step '{script_name}' failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print(f"[SUCCESS] Step '{script_name}' completed successfully.\n")
    return result.returncode


def main(args: list = None) -> int:
    print("Starting Ingestion Orchestrator...")

    # Step 1: Download raw sources
    run_script("download_sources.py")

    # Step 2: Extract structured text
    run_script("extract_text.py")

    # Step 3: Run indexing pipeline (with clean to reset vector store to fresh daily state)
    ingestion_args = args if args is not None else ["--clean"]
    run_script("run_ingestion.py", ingestion_args)

    print("=" * 60)
    print("Orchestration pipeline execution finished successfully.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] if len(sys.argv) > 1 else None))


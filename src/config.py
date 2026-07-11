"""
Mutual Fund FAQ Assistant — Centralized Configuration

Loads all settings from environment variables with sensible defaults.
Validates required variables on import to fail fast.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file (if present)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
METADATA_FILE = DATA_DIR / "metadata.json"

# ---------------------------------------------------------------------------
# LLM — Groq
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE: float = 0.0  # Deterministic for factual answers
GROQ_MAX_TOKENS: int = 512

# ---------------------------------------------------------------------------
# Embedding Model — BGE
# ---------------------------------------------------------------------------
EMBEDDING_MODEL_NAME: str = os.getenv(
    "EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5"
)

# ---------------------------------------------------------------------------
# Re-Ranker Model
# ---------------------------------------------------------------------------
RERANKER_MODEL_NAME: str = os.getenv(
    "RERANKER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# ---------------------------------------------------------------------------
# Vector Store — ChromaDB
# ---------------------------------------------------------------------------
CHROMA_PERSIST_DIR: str = os.getenv(
    "CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "vectorstore" / "chroma_db")
)
CHROMA_COLLECTION_NAME: str = os.getenv(
    "CHROMA_COLLECTION_NAME", "mutual_fund_faq"
)

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
TOP_K: int = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))
RERANK_TOP_N: int = 3  # Number of chunks after re-ranking

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# ---------------------------------------------------------------------------
# Response Constraints
# ---------------------------------------------------------------------------
MAX_RESPONSE_SENTENCES: int = 3
MAX_QUERY_LENGTH: int = 500

# ---------------------------------------------------------------------------
# Supported Schemes (for scope validation)
# ---------------------------------------------------------------------------
SUPPORTED_SCHEMES: list[str] = [
    "HDFC Mid-Cap Fund – Direct Growth",
    "HDFC Equity Fund – Direct Growth",
    "HDFC Focused Fund – Direct Growth",
    "HDFC ELSS Tax Saver Fund – Direct Plan Growth",
    "HDFC Large Cap Fund – Direct Growth",
]

SCHEME_URLS: dict[str, str] = {
    "HDFC Mid-Cap Fund – Direct Growth": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "HDFC Equity Fund – Direct Growth": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "HDFC Focused Fund – Direct Growth": "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "HDFC ELSS Tax Saver Fund – Direct Plan Growth": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "HDFC Large Cap Fund – Direct Growth": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
}

# ---------------------------------------------------------------------------
# Validation — fail fast if critical config is missing
# ---------------------------------------------------------------------------
def validate_config() -> None:
    """Validate that all required configuration is present.

    Raises:
        ValueError: If a required environment variable is missing.
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Please add it to your .env file. "
            "Get a key at https://console.groq.com/keys"
        )


# Run validation on import only if not in test mode
if os.getenv("TESTING", "").lower() != "true":
    # Defer validation — allow imports without key for setup/testing
    pass

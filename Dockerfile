# ==========================================================
# Mutual Fund FAQ Assistant — Containerization (Dockerfile)
# ==========================================================

FROM python:3.9-slim

WORKDIR /app

# Install build dependencies for libraries like sentence-transformers/chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Cache dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source directory, static frontend files, raw data, and persistent indexes
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data/ ./data/
COPY vectorstore/ ./vectorstore/

EXPOSE 8000

# Centralized environment configs
ENV HOST=0.0.0.0
ENV PORT=8000

# Start FastAPI server
CMD ["python", "-m", "src.api.main"]

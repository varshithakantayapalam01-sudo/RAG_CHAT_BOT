# HDFC Mutual Fund FAQ Assistant (Facts-Only Chatbot)

An end-to-end, compliance-oriented, facts-only FAQ chatbot that answers factual questions about HDFC Mutual Fund schemes. Built using the Retrieval-Augmented Generation (RAG) framework, it incorporates rigorous local guardrails to prevent PII leaks, block investment advice, reject off-topic questions, and enforce strict citation policies.

---

## 🏦 Selected AMC & Schemes

* **Asset Management Company (AMC)**: HDFC Asset Management Company
* **Supported Schemes**:
  1. *HDFC Mid-Cap Fund – Direct Growth* (Category: Equity Mid-Cap)
  2. *HDFC Equity Fund – Direct Growth* (Category: Equity Flexi-Cap)
  3. *HDFC Focused Fund – Direct Growth* (Category: Equity Focused)
  4. *HDFC ELSS Tax Saver Fund – Direct Plan Growth* (Category: Equity ELSS Tax Saver)
  5. *HDFC Large Cap Fund – Direct Growth* (Category: Equity Large Cap)

---

## ⚙️ Architecture Overview

The system is split into two pipelines:

### 1. Offline Ingestion Pipeline
* **Load**: Fetches pre-processed JSON and plain-text documents curated from official AMC factsheets and Groww pages.
* **Chunk**: Uses LangChain's `RecursiveCharacterTextSplitter` to segment sections (e.g. costs, exit loads, NAV) at paragraph boundaries (`\n\n`) to preserve numerical context.
* **Index**: Embeds chunks using the asymmetric bi-encoder `BAAI/bge-small-en-v1.5` and persists them into a local `ChromaDB` collection with cosine distance.

### 2. Online RAG Query Pipeline
* **Guardrails**: Intercepts input queries offline:
  * *PII*: Regex filters block PAN, Aadhaar, phone numbers, emails, and OTPs.
  * *Advisory*: Blocks advice intents and redirects to the SEBI/AMFI portal.
  * *Scope*: Rejects off-topic queries and competitive AMC references.
  * *Profanity*: Refuses abusive content.
* **Retrieve**: Adds the asymmetric search instruction prefix to the query, searches ChromaDB for the top 5 candidates, calculates similarity scores ($1.0 - d$), filters by threshold ($s \ge 0.65$), and re-ranks with `cross-encoder/ms-marco-MiniLM-L-6-v2` down to 3 final passages.
* **Generate**: Queries the Groq API (`llama-3.3-70b-versatile` at `temperature=0.0`) using structured system prompt guidelines. Wires an in-memory 128-query cache layer to bypass Groq rate limits.
* **Post-Process**: Restricts lengths to $\le 3$ sentences, cleans raw inline URL citation suffixes, and appends the source update footer.
* **API & UI**: Served via a FastAPI app (CORS enabled, static routes) and a responsive HTML/CSS/JS frontend utilizing Outfit typography and glassmorphic panels.

---

## 🚀 Setup Instructions

### 1. Prerequisites
* Python 3.9+ installed on your system.
* A valid Groq API Key (get one at [Groq Console](https://console.groq.com/)).

### 2. Installation
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository_url>
   cd RAG_CHATBOT
   ```

2. Initialize a virtual environment and activate it:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **Linux/macOS**:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

3. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
Ensure `GROQ_API_KEY` is set inside the newly created `.env` file.

### 4. Running the Ingestion Pipeline
To execute the complete end-to-end ingestion orchestrator locally (downloads sources, extracts structured text, and cleanly rebuilds the ChromaDB vector database index):
```bash
python scripts/trigger_ingestion.py
```
To run only the indexing step directly on existing processed files:
```bash
python scripts/run_ingestion.py --clean
```
To verify the indexed document distribution and test retriever similarity quality:
```bash
python scripts/verify_vectorstore.py
```

### 5. Daily Automated & Manual Ingestion (GitHub Actions)
The repository includes an automated scheduler workflow configured in `.github/workflows/daily_ingestion.yml`:
* **Scheduled Schedule**: Runs automatically every day at **10:30 AM IST** (`0 5 * * *` UTC cron schedule).
* **Manual Execution**: You can manually trigger the workflow from the repository's GitHub UI by navigating to the **Actions** tab → selecting **Daily Mutual Fund Ingestion Pipeline** → clicking **Run workflow**.
* **Workflow Behavior**: Checks out the repository, installs dependencies, executes `python scripts/trigger_ingestion.py`, updates `data/metadata.json` timestamps (`last_collected`, `last_ingested`), and commits/pushes updated data and vector store files back to the repository automatically.

### 6. Starting the Server
Start the FastAPI application (which will also host the UI client at `http://localhost:8000`):
```bash
python -m src.api.main
```

---

## 💬 Usage & API Endpoints

### Example Factual Queries to Try
* *"What is the expense ratio of HDFC Mid-Cap Fund – Direct Growth?"*
* *"What is the lock-in period for HDFC ELSS Tax Saver Fund?"*
* *"What is the exit load of HDFC Equity Fund – Direct Growth?"*
* *"How do I download my capital gains statement from HDFC AMC?"*

### Backend API Endpoints

#### 1. POST `/api/chat`
Process user queries through Guardrails and RAG.
* **Request Payload**:
  ```json
  {
    "query": "What is the exit load for HDFC Equity Fund?",
    "session_id": "optional_session_uuid"
  }
  ```
* **Success Response (Factual)**:
  ```json
  {
    "status": "success",
    "type": "factual",
    "answer": "The exit load for HDFC Equity Fund – Direct Growth is 1% if redeemed within 1 year from the date of allotment.",
    "citation": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "educational_link": null,
    "footer": "Last updated from sources: 2026-07-11"
  }
  ```

#### 2. GET `/api/health`
Checks backend health, vector store index state, and last ingestion timestamps from `data/metadata.json`:
* **Response**:
  ```json
  {
    "status": "healthy",
    "vectorstore": {
      "collection_name": "mutual_fund_faq",
      "document_count": 35,
      "persist_directory": "./vectorstore/chroma_db"
    },
    "last_ingestion": "2026-07-11T22:54:23.123456+00:00",
    "last_collected": "2026-07-11T20:52:58.498898+00:00",
    "error": null
  }
  ```

---

## 🛡️ Constraints & Disclaimer

* **Disclaimer**: A sticky disclaimer banner *"Facts-only. No investment advice."* is permanently visible in the UI client.
* **Factual Limits**: The bot rejects questions asking for advice (e.g. *"Should I buy HDFC Mid-Cap?"*), recommendations, or performance comparisons.
* **PII Redaction**: All queries containing PAN, Aadhaar, email, phone numbers, or OTP credentials are automatically blocked locally and never logged on disk to ensure investor privacy.

---

## 📝 License

This project is open-source and available under the MIT License.

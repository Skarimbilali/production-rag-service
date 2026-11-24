
# Production RAG Service

A document-grounded Retrieval-Augmented Generation (RAG)
application built with FastAPI, ChromaDB, Hugging Face
embeddings, Groq LLM, and a web-based frontend.

## Features

- PDF and DOCX document ingestion
- Document validation and text extraction
- Configurable overlapping text chunking
- Multilingual sentence embeddings
- ChromaDB vector similarity search
- Grounded question answering with source citations
- Input/output guardrails
- Document listing and deletion
- Browser-based dashboard
- Automated tests and retrieval evaluation

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Backend | FastAPI |
| Vector database | ChromaDB |
| Embeddings | intfloat/multilingual-e5-small |
| LLM | Groq openai/gpt-oss-20b |
| Frontend | HTML, CSS, JavaScript |
| Testing | pytest |

## Architecture

Document upload -> Validation -> Text extraction ->
Chunking -> Embeddings -> ChromaDB

User question -> Input guardrails -> Retrieval ->
LLM generation -> Output guardrails -> Answer + citations

## Getting Started

### 1. Clone

```bash
git clone https://github.com/Skarimbilali/production-rag-service.git
cd production-rag-service
```

### 2. Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` and supply your own required API credentials.
Do not commit `.env` or real API keys.

### 5. Start application

```powershell
uvicorn app.main:app --reload
```

Application:
http://127.0.0.1:8000

API documentation:
http://127.0.0.1:8000/docs

## Usage

1. Start the FastAPI application.
2. Open the dashboard in a web browser.
3. Upload a supported document.
4. Ask a question about the uploaded content.
5. Review the answer, citations and retrieved chunks.
6. List or delete documents through the interface.

## Evaluation Results

### Retrieval Evaluation

Based on 25 golden questions:
20 answerable and 5 unanswerable.

| Metric | Result |
|---|---:|
| Hit@5 | 100.00% |
| Recall@5 | 97.50% |
| MRR@5 | 0.7958 |

### Answer Faithfulness

20/20 generated answers were judged faithful
by the same v2 question-aware LLM judge.

LLM-judged faithfulness: 100%.

This is an automated judge result, not an
independent guarantee of factual correctness.

### Chunking Experiments

| Size | Overlap | Hit@5 | Recall@5 |
|---:|---:|---:|---:|
| 256 | 50 | 85.00% | 64.58% |
| 512 | 80 | 100.00% | 86.25% |
| 800 | 150 | 100.00% | 95.00% |

Selected baseline: 800 characters with 150 overlap.

Results are based on one small source PDF and
provisional relevance labels.

Full methodology and limitations: `EVAL.md`.

## Automated Tests

```powershell
python -m pytest -q
```

Latest verified result:

35 passed.

## Project Structure

```text
app/
  api/
  core/
  generation/
  guardrails/
  ingestion/
  retrieval/
  vector_store/

frontend/
tests/
evals/
docs/
screenshots/

README.md
DESIGN.md
EVAL.md
AI_USAGE.md
DEVELOPMENT_LOG.md
```

## Evaluation Commands

```powershell
python evals/run_evals.py
python evals/run_faithfulness.py
python evals/run_chunk_experiments.py --pdf "PATH_TO_SOURCE_PDF"
```

For rejudging saved answers with an outdated judge:

```powershell
python evals/run_faithfulness.py --rejudge-outdated
```

## Security and Limitations

- API credentials are configured through environment variables.
- Source documents are treated as untrusted input.
- Guardrails reduce certain prompt-injection risks but
  do not guarantee protection against all attacks.
- Evaluation uses a limited corpus and question set.
- The application has not been validated for
  large-scale production traffic or deployment.

## Project Documentation

- `DESIGN.md` — architecture and technical decisions
- `EVAL.md` — experiments and evaluation methodology
- `AI_USAGE.md` — AI assistance disclosure
- `DEVELOPMENT_LOG.md` — development history
- `docs/ai-history/` — available AI development notes

## Repository

https://github.com/Skarimbilali/production-rag-service

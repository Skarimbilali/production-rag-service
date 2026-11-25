# Production RAG Service

A document-grounded **Retrieval-Augmented Generation (RAG)** application built with Python, FastAPI, ChromaDB, multilingual Hugging Face embeddings, Groq LLM, and an HTML/CSS/JavaScript frontend.

Users can upload PDF and DOCX documents, ask questions about their contents, and receive answers with source citations, retrieved text chunks, and similarity scores.

The project focuses on building a modular RAG service, evaluating retrieval quality, testing guardrails, and documenting engineering decisions rather than providing only a working chatbot demonstration.

**GitHub Repository:** https://github.com/Skarimbilali/production-rag-service

---

## 1. Features

### Document Management

- Upload PDF and DOCX documents.
- Validate supported file types and document content.
- Extract text and document metadata.
- Extract structured tables from PDF documents.
- Detect duplicate document uploads.
- List uploaded documents.
- Delete documents and their stored vector representations.
- Store source filename, document ID, page or section, and chunk position.

### Retrieval-Augmented Question Answering

- Paragraph- and sentence-aware smart chunking.
- Multilingual document and question embeddings.
- Persistent ChromaDB vector storage.
- Hybrid semantic and keyword-based reranking.
- Automatic retrieval across multiple uploaded documents.
- Grounded answer generation using Groq.
- Source citations linked to retrieved document chunks.
- Refusal when sufficient document evidence is unavailable.

### Frontend

- HTML, CSS, and JavaScript browser interface.
- Document upload and listing.
- Question submission and generated answers.
- Source citations and page references.
- Retrieved chunk count.
- Actual retrieved chunk content.
- Individual similarity scores.

### Testing and Evaluation

- Automated pytest tests.
- Jupyter notebooks demonstrating the RAG pipeline.
- Golden-question retrieval evaluation.
- Hit Rate@K, Recall@K, and MRR.
- Chunking configuration comparison.
- LLM-as-a-Judge faithfulness evaluation.
- Manual multi-document retrieval testing.
- Prompt-injection and guardrail testing.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Programming language | Python 3.11 |
| Backend API | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| PDF extraction | pypdf, pdfplumber |
| DOCX extraction | python-docx |
| Embedding model | `intfloat/multilingual-e5-small` |
| Embedding dimensions | 384 |
| Vector database | ChromaDB |
| Similarity metric | Cosine |
| Retrieval | Semantic search with keyword-based hybrid reranking |
| LLM provider | Groq |
| Generation model | `openai/gpt-oss-20b` |
| Automated testing | pytest |
| Notebook testing | Jupyter |
| Evaluation | Custom Python scripts and LLM-as-a-Judge |

The project uses a code-based implementation rather than a no-code RAG builder.

Design justifications and trade-offs are discussed in [DESIGN.md](DESIGN.md).

---

## 3. System Architecture

### 3.1 Document Ingestion Pipeline

```text
PDF / DOCX Upload
        |
        v
FastAPI Document Endpoint
        |
        v
File Validation
        |
        v
Duplicate Detection (SHA-256)
        |
        v
Text, Headings and Table Extraction
        |
        v
Smart Chunking
        |
        v
Source Metadata and Context
        |
        v
Multilingual E5 Embeddings
        |
        v
ChromaDB Vector Store
```

The ingestion pipeline prepares document content for semantic retrieval while retaining information about its original source.

### 3.2 Question Answering Pipeline

```text
User Question
        |
        v
Input Guardrails
        |
        v
Multilingual E5 Query Embedding
        |
        v
ChromaDB Semantic Candidate Retrieval
        |
        v
Keyword Relevance Scoring
        |
        v
Hybrid Reranking
        |
        v
Final Top-K Retrieved Chunks
        |
        v
Groq Grounded Answer Generation
        |
        v
Citation Validation
        |
        v
Output Guardrails
        |
        v
Answer + Citations + Retrieved Chunks
```

If sufficient evidence is unavailable, the system returns a refusal rather than intentionally generating an unsupported answer.

Guardrails and citations are safeguards, not guarantees of perfect factual correctness.

---

## 4. Phase 2 — Multi-Document Retrieval Improvements

### 4.1 Problem Identified

During initial development, the RAG service answered questions from an uploaded PDF.

After uploading a second PDF into the same document collection, the system continued answering questions from the first document but failed to answer some questions associated with the second document.

Both PDFs had been indexed successfully.

The problem was therefore investigated as a **multi-document retrieval relevance issue**, rather than a document upload failure.

### 4.2 Diagnosis

Inspection of retrieved document chunks showed that semantic search sometimes ranked chunks from a less relevant PDF ahead of the information needed to answer the question.

The relevant evidence was consequently missing from the final Top-K context.

This could lead to an incorrect refusal even when the answer was present in the uploaded document collection.

### 4.3 Improvements Implemented

| Component | Improvement |
|---|---|
| `app/ingestion/chunker.py` | Smart paragraph- and sentence-aware splitting |
| `app/ingestion/service.py` | Dynamic source filename, page, and section context |
| `app/ingestion/extractor.py` | Improved PDF heading detection and structured table extraction |
| `app/vector_store/store.py` | Hybrid semantic and keyword-based reranking |
| `app/generation/generator.py` | Improved conditional reasoning, calculations, table interpretation, and refusals |

### 4.4 Hybrid Retrieval

The improved pipeline retrieves a broader set of semantic candidates and then uses keyword relevance to help determine which chunks should be returned.

This makes retrieval less dependent on semantic similarity alone.

The system searches across indexed documents automatically; the user does not need to manually choose a particular PDF before asking a question.

### 4.5 Observed Improvements

Manual testing demonstrated improvements in previously failing cases:

| Question area | Previously observed | After Phase 2 |
|---|---|---|
| Promotion eligibility | Incorrect refusal | Correctly identifies the unmet 18-month requirement |
| Probation resignation | Incorrect refusal | Correctly identifies seven days' written notice |
| International hotel limit | Per diem confused with hotel limit | Correctly identifies that the limit is unspecified |

These are observed manual results, not a complete quantitative before-and-after benchmark.

### 4.6 Limitations

Hybrid retrieval does not guarantee perfect document selection or retrieval accuracy.

Keyword matching can be imperfect across languages and synonyms, and processing additional candidates may increase latency.

A controlled semantic-only versus hybrid evaluation on the same multi-document corpus remains future evaluation work.

Full details are available in [DESIGN.md](DESIGN.md) and [EVAL.md](EVAL.md).

---

## 5. Getting Started

### Prerequisites

- Python 3.11
- Git
- Internet connectivity for initial model download and Groq requests
- Valid Groq API credentials

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Skarimbilali/production-rag-service.git
cd production-rag-service
```

### Step 2 — Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents environment activation, adjust the execution policy for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

For Jupyter notebooks, install the notebook packages if they are not already available:

```powershell
python -m pip install notebook ipykernel
```

### Step 4 — Configure Environment Variables

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure the required values, including your Groq API key.

Never commit `.env` or real API credentials to Git.

### Step 5 — Start the Backend

```powershell
uvicorn app.main:app --reload
```

### Step 6 — Open the Application

**Frontend:**

http://127.0.0.1:8000

**Swagger API documentation:**

http://127.0.0.1:8000/docs

---

## 6. Using the Application

1. Start the FastAPI backend.
2. Open the frontend in a browser.
3. Upload a supported PDF or DOCX document.
4. Confirm the document appears in the uploaded-document list.
5. Upload additional documents if required.
6. Ask a question about the indexed documents.
7. Review the generated answer and its source citations.
8. Expand the retrieved-chunks section to inspect evidence and scores.
9. Delete documents when they are no longer required.

### Example Question

**Question:**

How many annual leave days are allowed?

**Observed answer:**

20 working days

**Observed citations:**

- S1 — TechNova HR Policy Manual, page 5
- S4 — TechNova HR Policy Manual, page 5

The frontend also displayed five retrieved chunks with their original text, source pages, and similarity scores.

This result was verified manually using the TechNova test document.

---

## 7. Evaluation

The project uses retrieval metrics, chunking experiments, LLM-based faithfulness judgments, and manual testing.

### 7.1 Golden Dataset

The original golden question set contains:

- 20 answerable questions
- 5 unanswerable questions
- 25 questions total

Dataset:

`evals/golden_questions.json`

### 7.2 Historical Retrieval Results

| Metric | Result |
|---|---:|
| Hit@5 | 100.00% |
| Recall@5 | 97.50% |
| MRR@5 | 0.7958 |

These are historical results obtained before the final Phase 2 hybrid retrieval modifications.

They must not be interpreted as updated hybrid retrieval benchmark scores.

### 7.3 Chunking Configuration Comparison

| Chunk size | Overlap | Hit@5 | Recall@5 | MRR@5 |
|---:|---:|---:|---:|---:|
| 256 | 50 | 85.00% | 64.58% | 0.7225 |
| 512 | 80 | 100.00% | 86.25% | 0.7283 |
| 800 | 150 | 100.00% | 95.00% | 0.8583 |

The 800-character chunk size and 150-character overlap achieved the strongest results in the preliminary experiment.

The experiment used one small source PDF and provisional relevance labels.

### 7.4 Faithfulness Evaluation

A question-aware LLM judge classified 20 of 20 evaluated answers as faithful.

**Reported LLM-judged faithfulness: 100%.**

This represents the automated judge's classifications, not independently verified factual accuracy.

The judge was not calibrated against a fully independent human-annotated dataset.

### 7.5 Phase 2 Evaluation

Phase 2 was tested using the TechNova HR Manual and the RAG Project Guide.

Manual testing demonstrated improvements in multi-document retrieval, policy eligibility reasoning, structured table interpretation, and refusal behavior.

The latest hybrid implementation has not yet been quantitatively compared with semantic-only retrieval using a controlled identical question set.

**Detailed results, methodology, failure analysis, and limitations: [EVAL.md](EVAL.md).**

---

## 8. Evaluation Commands

### Retrieval Evaluation

```powershell
python evals/run_evals.py
```

### Faithfulness Evaluation

```powershell
python evals/run_faithfulness.py
```

### Rejudge a Specific Question

```powershell
python evals/run_faithfulness.py --rejudge Q016
```

### Chunking Experiments

```powershell
python evals/run_chunk_experiments.py
```

These commands depend on the configured environment, available evaluation corpus, and required indexed document data.

The evaluation scripts should be run with a consistent corpus and configuration when reproducing reported results.

A unified, independently verified single-command evaluation for all metrics and experiments has not yet been confirmed.

---

## 9. Automated Testing

The project uses pytest to test the implemented application components.

Run:

```powershell
python -m pytest -q
```

**Latest reported regression result:**

35 tests passed.

The passing test suite covers selected application behaviors but does not prove that all possible production failures are handled.

---

## 10. Jupyter Notebook Testing

The assignment requires pipeline testing through Jupyter notebooks before full API-based testing.

Two notebooks were created and committed to the development branch.

### Notebook 1 — Ingestion Pipeline

`notebooks/01_ingestion_pipeline.ipynb`

Demonstrates:

- PDF extraction
- DOCX extraction
- Smart chunking
- Source metadata
- Document embeddings
- Query embeddings

The observed execution ended with `NOTEBOOK 1: PASSED`.

### Notebook 2 — Retrieval and Generation

`notebooks/02_retrieval_generation.ipynb`

Demonstrates:

- ChromaDB document indexing
- Retrieval of document evidence
- Hybrid retrieval results
- Groq answer generation
- Citation handling
- Refusal without evidence

The saved notebook was reported to contain seven executed code cells and zero saved execution errors.

The exact answer and citation quality require separate source review.

### Run Jupyter

From the project directory:

```powershell
python -m notebook
```

Open the `notebooks/` folder, select a notebook, and choose **Run All Cells**.

The Groq generation step requires the configured API credentials.

**Notebook development commit:** `523c30a`

---

## 11. API Documentation and Error Handling

FastAPI provides interactive OpenAPI documentation at:

http://127.0.0.1:8000/docs

The project includes document-management and question-answering endpoints.

The assignment expects consistent responses for cases such as:

| HTTP status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Document created |
| 204 | Document deleted |
| 400 | Invalid or empty document |
| 404 | Resource not found |
| 409 | Duplicate upload |
| 415 | Unsupported file type |
| 422 | Invalid request data |
| 429 | Rate limit exceeded |
| 503 | Dependent service unavailable |

These are expected API behaviors; successful handling of every listed case must be established through actual API tests.

Swagger screenshots and full error-case verification are part of the final submission evidence.

---

## 12. Security and Guardrails

The system includes input and output checks to reduce unsafe or unsupported responses.

Security considerations include:

- Empty and invalid questions
- Excessively long questions
- Off-topic requests
- Prompt-injection attempts
- Jailbreak attempts
- Instructions embedded in retrieved documents
- Unsupported factual claims
- Citation validation
- Protection of environment secrets

Uploaded documents are treated as untrusted source data.

The system attempts to use document contents as evidence rather than as instructions.

### Security Limitations

Prompt-based and programmatic guardrails are defense-in-depth controls.

They do not guarantee protection against every adversarial input.

The system has not undergone independent penetration testing.

---

## 13. Project Structure

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
  index.html
  script.js
  style.css

tests/

evals/
  golden_questions.json
  run_evals.py
  run_faithfulness.py
  run_chunk_experiments.py
  results/

notebooks/
  01_ingestion_pipeline.ipynb
  02_retrieval_generation.ipynb
  create_notebooks.py

docs/
  phase2-history/

README.md
DESIGN.md
EVAL.md
AI_USAGE.md
DEVELOPMENT_LOG.md
requirements.txt
.env.example
```

Additional documentation and test evidence may be present in the `docs/`, `evals/results/`, and screenshot directories.

---

## 14. Development and Git Workflow

Development is tracked using Git and GitHub.

The repository uses:

- `main` as the intended stable branch
- `development` for ongoing development and testing
- Meaningful commits for completed changes

### Phase 2 Work

Phase 2 included improvements to chunking, extraction, source context, retrieval, generation, and documentation.

**Documentation and hybrid RAG commit:**

`8ecbc11`

**Jupyter notebook commit:**

`523c30a`

These commits were pushed to the `development` branch.

The latest merge of the development branch into `main` must be verified separately.

---

## 15. Known Limitations

- Limited evaluation corpus.
- Small original golden dataset.
- Provisional relevance labels.
- Incomplete independent faithfulness-judge validation.
- Final hybrid retrieval lacks a controlled comparative benchmark.
- Multi-document retrieval is improved but not guaranteed to be perfect.
- Some retrieved chunks may be less relevant than others.
- Scanned PDF OCR is not implemented.
- Large-scale production concurrency has not been benchmarked.
- Claim-level citation verification remains incomplete.
- Full DOCX upload-to-answer-to-delete flow requires final confirmation.
- Cloud production deployment is not verified.
- Monitoring and distributed tracing are not established as implemented features.

These limitations are documented to distinguish measured functionality from future improvements.

---

## 16. Future Improvements

Potential improvements include:

- Larger independently annotated multi-document evaluation datasets.
- Formal semantic-only versus hybrid retrieval benchmarks.
- Additional reranking methods.
- Improved multilingual retrieval evaluation.
- RAGAS-based supplementary quality metrics.
- Langfuse or equivalent observability tooling.
- p50/p95 latency and token-cost reporting.
- Stronger adversarial guardrails.
- OCR for scanned PDFs.
- Authentication and document ownership controls.
- Load and concurrency testing.
- Containerization and cloud deployment.

These items are future work unless separately implemented and verified.

---

## 17. Project Documentation

- [DESIGN.md](DESIGN.md) — Architecture, technology choices, and engineering trade-offs.
- [EVAL.md](EVAL.md) — Retrieval metrics, faithfulness, experiments, diagnosis, and limitations.
- [AI_USAGE.md](AI_USAGE.md) — AI-assisted development disclosure.
- [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) — Development history.
- `docs/phase2-history/2026-11-24.md` — Phase 2 development record.
- `docs/phase2-history/AI_PROMPT_HISTORY.md` — Selected AI prompt history.
- `docs/phase2-history/TEST_REPORT.md` — Phase 2 manual testing record.
- `notebooks/` — Jupyter pipeline tests.

The selected AI prompt history is not a replacement for the complete verbatim AI conversation history required by the assignment.

---

## 18. Submission Requirements

The final assignment submission requires:

- Public GitHub repository.
- Complete source code.
- Executed Jupyter notebooks.
- Pinned dependencies and `.env.example`.
- README, DESIGN, EVAL, and AI usage documentation.
- Complete AI prompts and project chat history.
- Swagger API screenshots.
- Mandatory end-to-end demonstration video.
- Evidence of evaluation, testing, guardrails, and design decisions.

Some submission evidence, including screenshots, complete chat export, final hybrid benchmarks, and video coverage, requires final verification.

---

## 19. Repository

**GitHub:** https://github.com/Skarimbilali/production-rag-service

**Project:** Portfolio 01 — Production RAG Service

**Instructor:** Osama Izhar

**Assignment deadline:** 25 November 2026
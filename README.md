
# Production RAG Service

A document-grounded **Retrieval-Augmented Generation (RAG)** application built using Python, FastAPI, ChromaDB, multilingual Hugging Face embeddings, Groq LLM, and a React + Vite dashboard.

The project includes an original HTML/CSS/JavaScript frontend and a separate modern React frontend.

Users can upload PDF and DOCX documents, ask questions in English or Roman Urdu, and receive evidence-grounded answers with source citations, actual retrieved chunks, similarity scores, and retrieval counts.

The implementation emphasizes modular architecture, measurable retrieval evaluation, document security, automated testing, observability, and engineering documentation.

**Repository:** https://github.com/Skarimbilali/production-rag-service

---

## 1. Features

### Document Management

- Upload PDF and DOCX files.
- Validate file formats and document content.
- Extract document text and metadata.
- Extract headings and structured tables from PDFs.
- Detect duplicate uploads using SHA-256 hashes.
- List indexed documents.
- Delete documents and their stored vector representations.
- Preserve filename, document ID, page or section, and chunk position.
- Apply document-level security checks before indexing.

### Retrieval-Augmented Question Answering

- Smart paragraph- and sentence-aware chunking.
- Multilingual document and question embeddings.
- Persistent ChromaDB vector storage.
- Semantic retrieval with keyword-based hybrid reranking.
- Automatic retrieval across multiple uploaded documents.
- Grounded answer generation using Groq.
- English and Roman Urdu question-answering support.
- Source citations linked to retrieved document chunks.
- Actual retrieved text, similarity scores, and chunk counts.
- Refusal behavior when sufficient evidence is unavailable.

### React Frontend

The React frontend is located in `frontend-react/`.

Implemented functionality:

- Responsive dashboard built with React and Vite.
- Document upload, listing, and deletion.
- English and Roman Urdu question input.
- Configurable Top-K and similarity threshold.
- Generated answers and source citations.
- Retrieved chunk count and complete chunk text.
- Similarity scores displayed as percentages.
- API health status.
- Monitoring dashboard backed by `/metrics`.
- Responsive navigation and dashboard cards.
- Success, error, and loading states.

The original HTML/CSS/JavaScript frontend remains available in `frontend/`.

Both frontends communicate with the same FastAPI backend and use the same indexed document collection.

### Security and Guardrails

- Input validation for questions.
- Prompt-injection and jailbreak checks.
- Document-level instruction-injection screening.
- Output and citation safeguards.
- Unsupported-answer refusal behavior.
- File format and content validation.
- Duplicate document detection.
- Environment secret protection.

These safeguards reduce risk but do not guarantee protection against every adversarial input.

### Monitoring

The FastAPI backend exposes:

`GET /metrics`

Available metrics include:

- Backend uptime.
- Total API requests.
- Successful requests.
- Failed requests.
- HTTP status code counts.
- Average API request duration.
- RAG retrieval call count.
- Average retrieval duration.
- RAG generation call count.
- Average generation duration.

Metrics are maintained in memory and reset when the backend restarts.

### Testing and Evaluation

- Automated pytest regression tests.
- Executed Jupyter pipeline notebooks.
- Golden-question retrieval evaluation.
- Hit@5, Recall@5, and MRR@5 metrics.
- Semantic-only versus hybrid retrieval comparison.
- Chunking configuration experiments.
- LLM-as-a-Judge faithfulness evaluation.
- Multi-document manual testing.
- Prompt-injection and document guardrail tests.
- React frontend browser and production build verification.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Programming language | Python 3.11 |
| Backend API | FastAPI |
| Modern frontend | React + Vite |
| Original frontend | HTML, CSS, JavaScript |
| PDF extraction | pypdf, pdfplumber |
| DOCX extraction | python-docx |
| Embedding model | `intfloat/multilingual-e5-small` |
| Embedding dimensions | 384 |
| Vector database | ChromaDB |
| Similarity metric | Cosine |
| Retrieval | Semantic search with keyword-based hybrid reranking |
| LLM provider | Groq |
| Generation model | `openai/gpt-oss-20b` |
| Backend testing | pytest |
| Notebook testing | Jupyter |
| Evaluation | Custom Python scripts and LLM-as-a-Judge |
| Monitoring | Custom FastAPI metrics collection |

The RAG implementation is written in Python code rather than assembled through a no-code RAG builder.

Technology choices and trade-offs are discussed in [DESIGN.md](DESIGN.md).

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
File and Content Validation
        |
        v
Document-Level Security Guardrails
        |
        v
Duplicate Detection (SHA-256)
        |
        v
Text, Heading and Table Extraction
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

The ingestion pipeline prepares document content for semantic retrieval while retaining its original source information.

Uploaded documents are treated as untrusted data.

### 3.2 Question Answering Pipeline

```text
User Question
        |
        v
FastAPI Question Endpoint
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

The question-answering response includes:

- `answer`
- `citations`
- `retrieved_count`
- `retrieved_chunks`

Each returned chunk can include its text, source metadata, and similarity score.

If sufficient evidence is unavailable, the system is designed to refuse unsupported answers.

Guardrails and citations are safeguards, not guarantees of perfect factual correctness.

### 3.3 Frontend Architecture

```text
           React + Vite Dashboard
                localhost:5173
                       |
                       | Vite Development Proxy
                       v
              FastAPI Backend
                localhost:8000
                       |
          +------------+------------+
          |            |            |
          v            v            v
       Documents    Questions     Metrics
          |            |
          v            v
      Ingestion     Retrieval
          |            |
          v            v
       ChromaDB    Groq Generation
```

During local React development, the Vite proxy forwards API requests to FastAPI.

The original HTML frontend remains served by FastAPI at `http://127.0.0.1:8000/`.

The React dashboard is served separately by Vite at `http://127.0.0.1:5173/`.

A successful Vite production build does not by itself mean the React application has been deployed to a production web server.

---

## 4. Phase 2 — Multi-Document Retrieval Improvements

### 4.1 Problem Identified

During initial development, the RAG service answered questions from an uploaded PDF.

After a second PDF was uploaded into the same collection, some questions related to that second document produced incorrect refusals, even though the document had been indexed successfully.

The issue was investigated as a multi-document retrieval relevance problem rather than a document upload failure.

### 4.2 Diagnosis

Inspection of retrieved document chunks showed that semantic search could rank less relevant chunks above the evidence needed to answer a question.

Relevant evidence could therefore be missing from the final Top-K context.

### 4.3 Improvements Implemented

| Component | Improvement |
|---|---|
| `app/ingestion/chunker.py` | Smart paragraph- and sentence-aware splitting |
| `app/ingestion/service.py` | Dynamic filename, page, and section context |
| `app/ingestion/extractor.py` | Improved PDF heading and table extraction |
| `app/vector_store/store.py` | Hybrid semantic and keyword-based reranking |
| `app/generation/generator.py` | Improved grounding, conditional reasoning, calculations, and refusals |

### 4.4 Hybrid Retrieval

The improved pipeline retrieves a broader candidate set using semantic search and then applies keyword relevance to help rerank candidates.

The final chunks are selected from this reranked set.

The system searches across indexed documents automatically; the user does not need to select a particular PDF before asking a question.

### 4.5 Observed Manual Improvements

| Question area | Previously observed | After Phase 2 |
|---|---|---|
| Promotion eligibility | Incorrect refusal | Identifies unmet 18-month requirement |
| Probation resignation | Incorrect refusal | Identifies seven days' written notice |
| International hotel limit | Per diem confused with hotel limit | Identifies that the limit is unspecified |

These are manual observations, not a complete controlled before-and-after benchmark for every RAG behavior.

### 4.6 Limitations

Hybrid retrieval does not guarantee perfect ranking or retrieval accuracy.

Keyword matching can be imperfect across languages and synonyms, and processing additional candidates may increase retrieval latency.

A controlled semantic-only versus hybrid Top-5 comparison was subsequently completed and is reported below.

---

## 5. Getting Started

### Prerequisites

- Python 3.11
- Git
- Node.js and npm for the React frontend
- Internet connection for initial model download and Groq requests
- Valid Groq API credentials

The React frontend was locally tested with Node.js `v20.20.1` and npm `10.8.2`.

### Step 1 — Clone the Repository

```powershell
git clone https://github.com/Skarimbilali/production-rag-service.git
cd production-rag-service
```

To access the latest React development work, switch to the development branch:

```powershell
git switch development
```

### Step 2 — Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents environment activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install Python Dependencies

```powershell
python -m pip install -r requirements.txt
```

For Jupyter notebooks, install notebook packages if they are not already available:

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

### Step 5 — Start the FastAPI Backend

From the repository root:

```powershell
uvicorn app.main:app --reload
```

Backend:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

Health endpoint:

http://127.0.0.1:8000/health

Monitoring endpoint:

http://127.0.0.1:8000/metrics

### Step 6 — Start the React Frontend

Open a second terminal.

From the repository root:

```powershell
cd frontend-react
npm ci
npm run dev
```

Open:

http://127.0.0.1:5173

The FastAPI backend must also be running.

The Vite development proxy forwards these API paths to FastAPI:

- `/health`
- `/documents`
- `/questions`
- `/metrics`

### Step 7 — Build the React Frontend

From `frontend-react/`:

```powershell
npm run build
```

A successful build creates production-ready static assets inside `frontend-react/dist/`.

The build does not automatically deploy or serve the generated files.

### Original HTML Frontend

The original frontend remains accessible through FastAPI:

http://127.0.0.1:8000/

It is maintained separately inside `frontend/`.

---

## 6. Using the Application

1. Start the FastAPI backend.
2. Start the React frontend.
3. Open the React dashboard.
4. Confirm the API status displays `API Online`.
5. Upload a PDF or DOCX document.
6. Confirm its filename and indexed chunk count.
7. Ask a question in English or Roman Urdu.
8. Review the generated answer.
9. Inspect citations, source filenames, and page references.
10. Inspect retrieved chunk text and similarity scores.
11. Review API and RAG metrics.
12. Delete documents when no longer required.

### Example Question

**Question:**

How many annual leave days do permanent employees get?

**Observed answer:**

Permanent employees receive 20 working days of annual leave per year.

### Observed React Results

A successful live request returned:

- 2 source citations.
- 5 retrieved chunks.
- Source filenames and available page references.
- Actual retrieved text.
- Similarity scores for all five chunks.

Example sources included:

- `TechNova_HR_Policy_Manual.pdf`, page 5.
- A temporary DOCX used during document testing.

The temporary test DOCX was subsequently deleted successfully using the React interface.

Document data and source ordering depend on the currently indexed collection and can change between runs.

### Roman Urdu Support

The question-answering pipeline also supports Roman Urdu questions.

For example:

```text
Permanent employees ko saal mein kitni annual leave milti hai?
```

A previously verified response was:

```text
Permanent employees ko har saal 20 working days ki annual leave milti hai.
```

Language support does not imply perfect translation or equal retrieval quality across all languages.

---

## 7. Evaluation

The project uses retrieval metrics, chunking experiments, LLM-based faithfulness judgments, and manual testing.

### 7.1 Golden Dataset

The golden question dataset contains:

- 20 answerable questions.
- 5 unanswerable questions.
- 25 questions total.

Dataset:

`evals/golden_questions.json`

### 7.2 Semantic-Only vs Hybrid Retrieval

A controlled Top-5 retrieval comparison was executed using the same evaluation setup.

| Metric | Semantic-only | Hybrid retrieval |
|---|---:|---:|
| Hit@5 | 100.00% | 100.00% |
| Recall@5 | 97.50% | 100.00% |
| MRR@5 | 0.7958 | 0.8750 |

**Observed result:** Hybrid retrieval improved Recall@5 and MRR@5 in this evaluation while maintaining the same Hit@5.

Results are recorded in:

- `evals/results/retrieval_comparison.csv`
- `evals/results/retrieval_comparison.json`

The benchmark uses a limited evaluation corpus and provisional relevance labels. The golden labels are not equivalent to a large, independently annotated, multi-document benchmark.

Results should not be generalized to all possible documents or questions.

### 7.3 Historical Retrieval Results

Earlier recorded retrieval results were:

| Metric | Historical result |
|---|---:|
| Hit@5 | 100.00% |
| Recall@5 | 97.50% |
| MRR@5 | 0.7958 |

These historical results must be distinguished from the subsequently executed semantic-only versus hybrid comparison.

### 7.4 Chunking Configuration Comparison

| Chunk size | Overlap | Hit@5 | Recall@5 | MRR@5 |
|---:|---:|---:|---:|---:|
| 256 | 50 | 85.00% | 64.58% | 0.7225 |
| 512 | 80 | 100.00% | 86.25% | 0.7283 |
| 800 | 150 | 100.00% | 95.00% | 0.8583 |

The 800-character chunk size and 150-character overlap achieved the strongest results in this preliminary experiment.

The experiment used a small source corpus and provisional relevance labels. It should not be presented as universal proof of optimal chunk size.

### 7.5 Faithfulness Evaluation

A question-aware LLM judge classified 20 of 20 evaluated answers as faithful.

**Reported LLM-judged faithfulness: 100%.**

This is the automated judge's classification result, not independently verified factual accuracy.

The judge has not been fully calibrated against a separate, human-annotated reference dataset.

### 7.6 Phase 2 Evaluation

Phase 2 was tested using the TechNova HR Manual and the RAG Project Guide.

Manual testing included:

- Multi-document retrieval.
- Policy eligibility questions.
- Conditional reasoning.
- Structured table interpretation.
- Refusal behavior.
- Source citation inspection.

**Detailed methodology, results, and limitations:** [EVAL.md](EVAL.md).

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

Evaluation commands depend on the configured environment, available evaluation corpus, and indexed document data.

Reproduction requires a consistent corpus, evaluation labels, model configuration, and retrieval settings.

A unified, independently validated one-command run for every metric and experiment has not been established.

---

## 9. Automated Testing

The project uses pytest to verify implemented application components.

Run from the repository root:

```powershell
python -m pytest -q
```

**Latest verified regression result:**

```text
134 passed, 1 warning
```

The warning was associated with a third-party Starlette/AnyIO deprecation and did not fail the test run.

Test coverage includes application logic, API behavior, retrieval, generation, ingestion, guardrails, and monitoring components.

Passing tests do not guarantee the absence of production failures or security vulnerabilities.

### React Frontend Build Verification

From `frontend-react/`:

```powershell
npm run build
```

The React production build was successfully executed using Vite `v8.3.8`.

Live browser verification also covered:

- FastAPI connection.
- Document uploading.
- Document deletion.
- Question answering.
- Source citations.
- Retrieved chunks and similarity scores.
- Monitoring metrics.
- The upper section of the responsive mobile layout.

The entire mobile application and production deployment have not been independently verified.

---

## 10. Jupyter Notebook Testing

The assignment requires pipeline testing using Jupyter notebooks before complete API-based demonstrations.

Two executed notebooks were created and committed.

### Notebook 1 — Ingestion Pipeline

`notebooks/01_ingestion_pipeline.ipynb`

Demonstrates:

- PDF extraction.
- DOCX extraction.
- Smart chunking.
- Source metadata.
- Document embeddings.
- Query embeddings.

The observed execution ended with:

```text
NOTEBOOK 1: PASSED
```

### Notebook 2 — Retrieval and Generation

`notebooks/02_retrieval_generation.ipynb`

Demonstrates:

- ChromaDB document indexing.
- Retrieval of document evidence.
- Hybrid retrieval results.
- Groq answer generation.
- Citation handling.
- Refusal without evidence.

The saved notebook was reported to contain seven executed code cells with zero saved execution errors.

Exact answer and citation quality should be assessed separately through evaluation and source review.

### Run Jupyter

From the project directory:

```powershell
python -m notebook
```

Open the `notebooks/` directory and execute the notebook cells.

The generation step requires configured Groq credentials.

**Notebook development commit:** `523c30a`.

---

## 11. API Documentation and Error Handling

FastAPI provides interactive OpenAPI documentation at:

http://127.0.0.1:8000/docs

### Document Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/documents/upload` | Upload PDF/DOCX |
| GET | `/documents` | List indexed documents |
| DELETE | `/documents/{document_id}` | Delete document and chunks |

### Question Endpoint

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/questions/ask` | Retrieve evidence and generate answer |

Example request:

```json
{
  "question": "How many annual leave days do permanent employees get?",
  "top_k": 5,
  "threshold": 0.0
}
```

The response contains an answer, citations, retrieved count, and retrieved chunks.

### Health and Monitoring

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| GET | `/metrics` | Read runtime metrics |

### HTTP Error Handling

Expected API behaviors include:

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

These represent intended response behaviors; not every error path has been independently verified through live API tests.

Swagger screenshots and final error-case evidence should be included in the submission where required.

---

## 12. Security and Guardrails

The application contains safeguards at document ingestion, question input, and answer generation.

### Input Guardrails

Considerations include:

- Empty questions.
- Invalid requests.
- Excessively long questions.
- Prompt-injection attempts.
- Jailbreak attempts.
- Unsupported or off-topic requests.

### Document-Level Guardrails

Uploaded documents are checked for suspicious instruction-like content before indexing.

A live malicious-DOCX upload test returned HTTP 400 and did not store the rejected document.

A legitimate DOCX upload was accepted with HTTP 201 and was subsequently deleted successfully with HTTP 204.

These tests demonstrate specific observed behaviors, not comprehensive security coverage.

### Output Guardrails

Answer-generation safeguards include:

- Grounding answers in retrieved evidence.
- Validating source citations.
- Refusing unsupported factual answers.
- Treating retrieved content as reference material rather than system instructions.

### Security Limitations

Prompt-based and programmatic guardrails are defense-in-depth measures.

They do not guarantee protection against every malicious document, prompt-injection technique, or jailbreak attempt.

The application has not undergone independent penetration testing.

Authentication and per-user document ownership controls are not currently established as implemented features.

---

## 13. Monitoring and Observability

Custom monitoring functionality is implemented in the FastAPI backend.

Relevant components include:

- `app/core/monitoring.py`
- `app/main.py`
- `app/api/questions.py`
- `tests/test_monitoring.py`

The React dashboard reads the `/metrics` endpoint.

### Example Monitoring Fields

```json
{
  "uptime_seconds": 63.47,
  "requests": {
    "total": 1,
    "successful": 1,
    "failed": 0,
    "status_codes": {
      "200": 1
    },
    "average_duration_ms": 2.62
  },
  "rag_performance": {
    "retrieval_calls": 2,
    "average_retrieval_ms": 3746.83,
    "generation_calls": 2,
    "average_generation_ms": 631.49
  }
}
```

The example illustrates the response structure, not fixed performance targets.

### Live React Monitoring Verification

A live dashboard session displayed:

- 23 total API requests.
- 23 successful requests.
- 0 failed requests.
- 3 retrieval calls.
- Average retrieval duration of 2649.87 ms.
- Average generation duration of 654.13 ms.

These values were recorded in one local session and are not a repeatable performance benchmark.

### Monitoring Limitations

- Metrics are maintained in process memory.
- Values reset when FastAPI restarts.
- No persistent cross-instance aggregation is implemented.
- Distributed tracing is not implemented.
- p50/p95 latency and token-cost monitoring remain future work.

---

## 14. Project Structure

```text
app/
  api/
  core/
    monitoring.py
  generation/
  guardrails/
  ingestion/
  retrieval/
  vector_store/

frontend/
  index.html
  script.js
  style.css

frontend-react/
  public/
  src/
    App.jsx
    App.css
    index.css
    main.jsx
  index.html
  package.json
  package-lock.json
  vite.config.js
  eslint.config.js

tests/

evals/
  golden_questions.json
  run_evals.py
  run_faithfulness.py
  run_chunk_experiments.py
  results/
    retrieval_comparison.csv
    retrieval_comparison.json

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

This diagram shows the principal project files and directories, rather than every individual module.

Additional documentation and evaluation artifacts may exist in `docs/` and `evals/results/`.

Generated frontend folders such as `node_modules/` and `dist/` should not be committed.

---

## 15. Development and Git Workflow

Development is tracked using Git and GitHub.

The repository uses:

- `main` as the intended stable branch.
- `development` for active development and testing.
- Meaningful commits for completed features.

### Selected Development Commits

| Commit | Work |
|---|---|
| `8ecbc11` | Earlier Phase 2 improvements |
| `523c30a` | Jupyter notebooks |
| `cd4f472` | Monitoring implementation |
| `61d38e9` | React RAG dashboard |

The React frontend was pushed to the `development` branch in commit `61d38e9`.

The latest merge from `development` into `main` must be verified separately.

The README and related documentation should be committed after review.

---

## 16. Known Limitations

- Limited evaluation corpus.
- Small golden-question dataset.
- Provisional retrieval relevance labels.
- Incomplete independent faithfulness-judge validation.
- Multi-document retrieval is improved but not guaranteed to be perfect.
- Some retrieved chunks may be less relevant than others.
- Scanned PDF OCR is not implemented.
- Large-scale production concurrency has not been benchmarked.
- Claim-level citation verification remains incomplete.
- Document guardrails cannot detect every malicious instruction.
- Complete mobile-layout testing remains outstanding.
- React production hosting has not been verified.
- Authentication and per-user document access controls are not implemented.
- Persistent observability and distributed tracing are not implemented.
- Cloud production deployment is not verified.

These limitations distinguish implemented and measured functionality from future improvements.

---

## 17. Future Improvements

Potential improvements include:

- Larger independently annotated multi-document evaluation datasets.
- Additional reranking techniques.
- Improved multilingual retrieval evaluation.
- RAGAS-based supplementary quality metrics.
- Independent faithfulness-judge calibration.
- Langfuse or equivalent distributed observability.
- Persistent metrics and tracing.
- p50/p95 latency and token-cost reporting.
- Stronger adversarial document screening.
- OCR for scanned PDF documents.
- Authentication and document ownership controls.
- Load testing and concurrency benchmarking.
- Containerization and cloud deployment.
- Additional React accessibility and mobile testing.

These are future improvements unless separately implemented and verified.

---

## 18. Project Documentation

- [DESIGN.md](DESIGN.md) — Architecture, technology choices, and engineering trade-offs.
- [EVAL.md](EVAL.md) — Retrieval evaluation, faithfulness, experiments, and limitations.
- [AI_USAGE.md](AI_USAGE.md) — AI-assisted development disclosure.
- [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) — Development history.
- `docs/phase2-history/2026-11-24.md` — Phase 2 development record.
- `docs/phase2-history/AI_PROMPT_HISTORY.md` — Selected AI prompt history.
- `docs/phase2-history/TEST_REPORT.md` — Phase 2 manual testing record.
- `notebooks/` — Executed pipeline notebooks.

Selected AI prompt history does not replace the complete verbatim AI conversation history required by the assignment.

---

## 19. Submission Requirements

The final assignment submission requires:

- Public GitHub repository.
- Complete project source code.
- Executed Jupyter notebooks.
- Dependency files and `.env.example`.
- README, DESIGN, EVAL, and AI usage documentation.
- Complete AI prompts and required project chat history.
- Swagger API screenshots.
- Mandatory end-to-end demonstration video.
- Evidence of evaluation, testing, guardrails, and design decisions.
- Demonstration of the implemented React frontend and monitoring features.

Some final submission evidence, including screenshots, full chat export, demo video coverage, and the `main` branch merge, requires separate verification.

---

## 20. Repository Information

**GitHub:** https://github.com/Skarimbilali/production-rag-service

**Project:** Portfolio 01 — Production RAG Service

**Instructor:** Osama Izhar

**Assignment deadline:** 25 November 2026

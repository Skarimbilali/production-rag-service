
# Production RAG Service â€” System Design

## 1. Overview

Production RAG Service is a document-grounded
question-answering application built with Python,
FastAPI, ChromaDB, Hugging Face embeddings, and Groq.

The system processes uploaded documents and retrieves
relevant text chunks to produce answers supported by
source evidence.

## 2. Architecture

### Document Ingestion

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
Text Extraction
       |
       v
Paragraph- and Sentence-Aware Smart Chunking
       |
       v
Multilingual E5 Embeddings
       |
       v
ChromaDB Vector Store
```

### Question Answering

```text
User Question
      |
      v
Input Guardrails
      |
      v
Query Embedding
      |
      v
ChromaDB Similarity Search
      |
      v
Top-K Retrieved Chunks
      |
      v
Groq LLM Generation
      |
      v
Output Guardrails
      |
      v
Grounded Answer + Citations
```

## 3. Technology Decisions

| Component | Selection | Reason |
|---|---|---|
| API framework | FastAPI | Typed request validation and OpenAPI |
| Embeddings | multilingual-e5-small | Multilingual semantic retrieval |
| Vector database | ChromaDB | Local persistence and vector similarity |
| Generation | Groq / gpt-oss-20b | Hosted language-model inference |
| Frontend | React + Vite and HTML/CSS/JavaScript | Responsive React dashboard with original HTML frontend preserved |
| Tests | pytest | Automated regression testing |

## 4. Document Ingestion

The ingestion pipeline validates incoming files,
extracts document text, splits text into overlapping
character-based chunks, creates embeddings and stores
the chunks with source metadata.

Stored metadata includes document ID, filename,
page number, section and chunk position.

### Chunking Configuration

Current baseline:

- Chunk size: 800 characters
- Overlap: 150 characters
- Chunking type: Paragraph- and sentence-aware smart chunking
- Whitespace: Normalized before splitting

The baseline was retained after comparing three
chunking configurations in the evaluation pipeline.

## 5. Retrieval Design

The embedding model is:

`intfloat/multilingual-e5-small`

Document passages use the `passage:` prefix.

User queries use the `query:` prefix.

Embedding vectors are normalized and searched with
cosine distance in ChromaDB.

The retrieval pipeline uses configurable Top-K and
similarity filtering.

The evaluation configuration used Top-K = 5.

## 6. Answer Generation

The generation layer sends the original question
and retrieved document evidence to the Groq LLM.

The answer is expected to:

- Stay grounded in retrieved evidence
- Avoid inventing unsupported information
- Provide references to source chunks
- Return a refusal when sufficient evidence is absent

The refusal behavior is supported by application
logic and guardrails.

## 7. Guardrails

The system includes input validation and
prompt-injection detection patterns.

Output handling checks generated responses before
returning them to users.

Threats considered include:

- Direct prompt injection
- Indirect instructions embedded in documents
- Jailbreak attempts
- Requests for unsupported or sensitive information

### Security Limitations

These guardrails are defense-in-depth measures,
not a guarantee against adversarial inputs.

The application is not independently security
audited or penetration tested.

## 8. API and Frontend

FastAPI provides document-management and
question-answering functionality.

The browser frontend allows users to:

- Upload a supported document
- View uploaded documents
- Delete documents
- Ask questions
- Read grounded answers
- Inspect citations and retrieved chunks

FastAPI also exposes interactive API
documentation at `/docs`.

## 9. Evaluation Design

The golden dataset contains:

- 20 answerable questions
- 5 unanswerable questions

### Retrieval Metrics

The corrected golden-label run produced:

| Metric | Result |
|---|---:|
| Hit@5 | 100.00% |
| Recall@5 | 97.50% |
| MRR@5 | 0.7958 |

### Faithfulness

The v2 question-aware judge classified
20 of 20 evaluated answers as faithful.

This is an LLM-as-judge estimate and
not independently validated factual accuracy.

### Chunking Experiments

| Size | Overlap | Hit@5 | Recall@5 |
|---:|---:|---:|---:|
| 256 | 50 | 85.00% | 64.58% |
| 512 | 80 | 100.00% | 86.25% |
| 800 | 150 | 100.00% | 95.00% |

The experiment used provisional evidence-phrase
labels on a small source document.

Detailed methodology: `EVAL.md`.

## 10. Testing

The automated pytest suite covers the
implemented retrieval, vector-store,
generation and guardrail behavior.

Latest verified regression run:

`134 passed, 1 third-party deprecation warning`

The passing suite does not imply that
all production failure modes are covered.

## 11. Operational Considerations

### Configuration

Runtime settings are loaded from environment
variables. Example settings are documented
in `.env.example`.

### Logging

Application logging is implemented under
`app/core/logger.py`.

### Persistence

ChromaDB stores document embeddings and
associated metadata.

### Dependencies

Runtime dependencies are recorded in
`requirements.txt`.

## 12. Known Limitations

- Limited evaluation corpus
- Small golden dataset
- Human relevance-label audit is incomplete
- No independently measured production scalability
- No formal security penetration testing
- DOCX upload and deletion were verified; broader adversarial and production testing remains necessary
- Evaluation metrics may differ on larger datasets

## 13. Future Improvements

Potential future work includes:

- Further hybrid retrieval optimization and benchmarking
- Larger human-annotated evaluation dataset
- Retrieval quality monitoring
- Better prompt-injection defenses
- Performance and concurrency testing
- Containerized production deployment

## 14. References

- `README.md` â€” Setup and usage
- `EVAL.md` â€” Evaluation and experiments
- `AI_USAGE.md` â€” AI-assistance disclosure
- `DEVELOPMENT_LOG.md` â€” Development history
- `evals/` â€” Evaluation scripts and results

## 15. Phase 2 - Multi-Document Retrieval Diagnosis

### Problem Identified

Initially, the system answered questions correctly when
one PDF was uploaded.

After uploading a second PDF, the system continued
answering questions from the first document but failed
to answer some questions from the second document.

Both documents were indexed successfully.

### Root Cause

Analysis of the retrieved chunks revealed that semantic
search sometimes ranked chunks from the less relevant
PDF above the correct evidence.

As a result, the final Top-K context did not always
contain the information required to answer the question.

This caused incorrect refusals even when the answer
existed in an uploaded document.

### Solution Implemented

1. Paragraph- and sentence-aware smart chunking.
2. Dynamic filename, page and section metadata.
3. Improved PDF heading and table extraction.
4. Hybrid semantic and keyword-based reranking.
5. Improved conditional reasoning and grounded generation.

### Updated Retrieval Flow

User Question
  -> Input Guardrails
  -> E5 Query Embedding
  -> ChromaDB Semantic Candidate Retrieval
  -> Keyword Relevance + Hybrid Reranking
  -> Top-K Relevant Chunks Across Uploaded PDFs
  -> Groq LLM
  -> Citation Validation
  -> Answer or Refusal

### Live Verification

- Promotion eligibility questions improved.
- Probation resignation notice questions improved.
- International hotel-limit hallucination was corrected.

### Design Trade-offs

Hybrid reranking improves retrieval relevance for
keyword-sensitive questions but introduces additional
computation and latency.

Keyword matching may perform imperfectly across
languages, synonyms and Roman Urdu variations.

The solution does not guarantee perfect retrieval
accuracy across arbitrary documents.

### Evaluation Limitations

The earlier golden-set metrics were measured before
the final Phase 2 hybrid retrieval improvements.

Live tests demonstrate observed improvements, not
a statistically verified accuracy improvement.

A controlled semantic-only versus hybrid Top-5 benchmark was completed on 25 November 2026.

---

## 16. Final Architecture and React Frontend

The application maintains two browser interfaces:

- `frontend/` — original HTML, CSS and JavaScript frontend.
- `frontend-react/` — React + Vite dashboard.

The React frontend uses the Vite development proxy to access the FastAPI backend running at `http://127.0.0.1:8000`.

The React development application runs at `http://127.0.0.1:5173`.

Both frontends share the existing FastAPI document collection and retrieval implementation.

### React Features

- PDF and DOCX document uploading.
- Indexed document listing and deletion.
- English and Roman Urdu question entry.
- Configurable Top-K and similarity threshold.
- Generated answer display.
- Source citations with filenames and available page numbers.
- Actual retrieved text chunks and similarity percentages.
- API connection status.
- RAG monitoring dashboard.
- Responsive navigation and dashboard layout.

### Frontend-to-Backend Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | API health |
| POST | `/documents/upload` | Upload document |
| GET | `/documents` | List documents |
| DELETE | `/documents/{document_id}` | Delete document |
| POST | `/questions/ask` | Ask a grounded question |
| GET | `/metrics` | Runtime monitoring |

The Vite production build was verified successfully. Cloud production deployment has not been verified.

## 17. Final Retrieval Architecture

Phase 2 uses:

1. Smart paragraph- and sentence-aware document chunking.
2. Source filename, page and section metadata.
3. Multilingual E5 embeddings.
4. Semantic candidate retrieval from ChromaDB.
5. Keyword-aware hybrid reranking.
6. Final Top-K evidence selection.
7. Groq grounded answer generation.
8. Citation validation and output guardrails.

### Controlled Retrieval Comparison

The benchmark on 25 November 2026 used two indexed PDFs, 42 chunks, 25 golden questions, Top-K = 5 and threshold 0.0.

| Metric | Semantic-only | Hybrid |
|---|---:|---:|
| Hit@5 | 100.00% | 100.00% |
| Recall@5 | 97.50% | 100.00% |
| MRR@5 | 0.7958 | 0.8750 |

The hybrid approach improved aggregate recall and reciprocal ranking under the tested conditions.

The golden labels primarily cover one PDF and are position-based. They require a manual audit after smart-chunking changes. These results are not a production-wide accuracy guarantee.

## 18. Document Guardrails and Multilingual Support

### Document Guardrails

Security screening is implemented during document ingestion.

A malicious DOCX containing suspicious instructions was rejected with HTTP 400 and was not indexed.

A legitimate DOCX was accepted with HTTP 201 and subsequently deleted with HTTP 204.

Relevant modules include:

- `app/guardrails/guardrails.py`
- `app/ingestion/service.py`
- `tests/test_ingestion.py`

The safeguards are defense-in-depth and do not guarantee detection of every adversarial document.

### Multilingual Generation

The multilingual E5 model supports retrieval for English and Roman Urdu questions.

The generation layer includes multilingual answer instructions in `app/generation/generator.py`.

An English annual-leave question and a Roman Urdu equivalent were tested successfully.

Multilingual support does not guarantee equal answer quality for every language or question type.

## 19. Monitoring and Operational Design

Custom monitoring is implemented through:

- `app/core/monitoring.py`
- `app/main.py`
- `app/api/questions.py`
- `tests/test_monitoring.py`

The `/metrics` endpoint provides:

- Backend uptime.
- Total, successful and failed API requests.
- HTTP status code counts.
- Average request duration.
- Retrieval call count and average retrieval time.
- Generation call count and average generation time.

The React dashboard displays these measurements.

Metrics are process-local, in-memory and reset on application restart.

Distributed tracing, persistent metrics, p50/p95 reporting and production load testing remain future improvements.

## 20. Final Verification and Limitations

### Verified

- React production build with Vite 8.3.8.
- React-to-FastAPI connectivity.
- React PDF upload and document deletion.
- Grounded answer generation.
- Two citations and five retrieved chunks in a live browser test.
- Chunk text, source metadata and similarity scores.
- Live monitoring metrics.
- Upper portion of the responsive mobile layout.
- Automated pytest regression: 134 passed, 1 third-party deprecation warning.

### Remaining Limitations

- Complete mobile-page testing remains outstanding.
- No verified cloud deployment.
- No authentication or per-user document ownership.
- No OCR for scanned PDFs.
- Limited and incompletely audited golden dataset.
- Faithfulness judge not independently calibrated.
- No large-scale concurrency benchmark.
- No security penetration test.
- No persistent or distributed monitoring.

The React frontend was committed as `61d38e9` and pushed to the `development` branch.

See `README.md` for setup, `EVAL.md` for evaluation methodology and `AI_USAGE.md` for AI assistance disclosure.

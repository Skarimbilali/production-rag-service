# Development Log

Project: Portfolio 01 — Production RAG Service  
Development branch: `development`

## 2026-11-19 — Initial Setup

### Verified

- Project directory structure created
- Python 3.11 virtual environment activated
- Dependencies installed and checked
- FastAPI health endpoint returned HTTP 200
- Swagger UI tested successfully
- PDF/DOCX extraction modules imported
- Chunking test generated 4 chunks
- Git main and development branches configured
- Multilingual E5 model loaded successfully
- Query embedding returned 384 dimensions
- Centralized logging produced expected messages

### Errors and Corrections

1. Git example output accidentally executed as commands.  
   Resolution: Used actual Git commands.

2. VS Code branch indicator was inconsistent.  
   Resolution: Verified active branch with Git commands.

3. `ImportError` for `embed_query`.  
   Cause: `embeddings.py` was empty.  
   Resolution: Implemented `EmbeddingService`.

### Pending at This Stage

- ChromaDB storage testing
- Complete upload and deletion endpoints
- Retrieval and answer generation
- Guardrails and frontend
- Automated tests and evaluation
- Full assignment documentation

## 2026-11-19 — Vector Store Testing

- ChromaDB insert, search and delete: 3 tests passed
- `pytest.ini` configuration error fixed
- Test execution completed in 25.20 seconds without warnings

## 2026-11-19 — Document API Integration

### Verified

- PDF upload: HTTP 201 Created
- Document chunks stored: 7
- Duplicate upload: HTTP 409 Conflict
- Document listing: HTTP 200 OK
- Document deletion: HTTP 204 No Content
- Listing after deletion: HTTP 200 OK, empty list

### Pending at This Stage

- Verify deleted content cannot be retrieved

## 2026-11-20 — Document APIs and Retrieval

Branch: `development`

### Completed

- PDF upload API
- Duplicate upload detection
- Document listing
- Document deletion
- Empty listing verification
- RetrievalService implementation
- English retrieval smoke test
- Roman Urdu retrieval smoke test
- Similarity score inspection

### Testing

- 2 retrieval tests passed in 19.95 seconds

### Pending at This Stage

- Stronger isolated retrieval tests
- LLM integration
- Grounded answers and citations
- Guardrails
- Frontend
- Evaluation and documentation

## 2026-11-21 to 2026-11-23 — RAG Integration and Evaluation Work

The following features were implemented and tested during subsequent development. Exact per-feature completion dates were not separately recorded.

### Backend and Generation

- Integrated Groq language model client
- Implemented retrieval-grounded answer generation
- Added source citations
- Implemented refusal behavior for unsupported answers
- Added input and output guardrail checks

### Frontend

- Developed HTML, CSS and JavaScript dashboard
- Integrated document upload, listing and deletion
- Integrated question-answering interaction
- Displayed retrieved chunks, source information and similarity scores

### Testing

- Expanded automated tests for generation and guardrails
- Added mocked indirect prompt-injection tests
- Performed a manual live indirect prompt-injection test
- Verified application functionality through browser and API testing

### Evaluation

- Created 25-question golden dataset
- Implemented retrieval evaluation
- Tested answerable and unanswerable questions
- Implemented LLM-as-judge faithfulness evaluation
- Added rate-limit retry and checkpoint handling

## 2026-11-24 — Faithfulness Evaluation Finalization

### Problem

The original faithfulness judge did not include the user's question when evaluating an answer.

A short numerical response for Q016 was judged unfaithful even though the supporting document contained the relevant evidence.

### Correction

- Updated judge prompt to include the original question
- Added judge version tracking
- Preserved existing generated answers
- Re-evaluated all 20 answers using `v2_question_aware`
- Confirmed mixed judge versions were eliminated

### Final Observed Results

| Metric | Result |
|---|---|
| Answerable questions | 20 |
| Completed evaluations | 20 |
| Faithful answers | 20 |
| Refused answers | 0 |
| LLM-judged faithfulness | 100% |
| Judge version | v2_question_aware |
| Mixed judge versions | False |

The result is an automated judge estimate, not an independent guarantee of correctness.

## 2026-11-24 — Chunk-Size Experiments

### Configurations Tested

| Configuration | Chunk Size | Overlap | Chunk Count |
|---|---:|---:|---:|
| A | 256 | 50 | 21 |
| B | 512 | 80 | 11 |
| C | 800 | 150 | 7 |

### Top-5 Results

| Configuration | Hit@5 | Recall@5 | MRR@5 |
|---|---:|---:|---:|
| A | 85.00% | 64.58% | 0.7225 |
| B | 100.00% | 86.25% | 0.7283 |
| C | 100.00% | 95.00% | 0.8583 |

### Decision

Retained the existing 800-character chunk size with 150-character overlap.

The experiment used one small PDF and provisional evidence-phrase relevance labels.

Experiment files:

- `evals/run_chunk_experiments.py`
- `evals/results/chunk_experiments.json`
- `evals/results/chunk_experiments.csv`

## 2026-11-24 — Golden Dataset Audit

### Problem

Retrieval question Q005 initially failed because its expected relevant chunk positions included only position 0.

### Investigation

Manual inspection of stored ChromaDB chunks confirmed the relevant statement appeared in both chunk positions 0 and 1.

The retrieval result included chunk position 1, but the evaluator did not count it as relevant.

### Correction

Updated Q005:

- Previous labels: `[0]`
- Corrected labels: `[0, 1]`

Re-ran the retrieval evaluation after the correction.

### Final Observed Retrieval Results

| Metric | Result |
|---|---:|
| Total questions | 25 |
| Answerable | 20 |
| Unanswerable | 5 |
| Hit@5 | 100.00% |
| Recall@5 | 97.50% |
| MRR@5 | 0.7958 |

A complete independent audit of every golden relevance label remains pending.

## 2026-11-24 — Final Regression Testing

Executed:

`python -m pytest -q`

Observed result:

**35 passed in 24.53 seconds**

No test failures were reported.

## 2026-11-24 — Documentation and Git Preparation

- Updated `EVAL.md` with retrieval, faithfulness and chunk experiments
- Prepared `README.md`
- Prepared `DESIGN.md`
- Reviewed `AI_USAGE.md`
- Reviewed `DEVELOPMENT_LOG.md`
- Verified Git branch: `development`
- Staged application, tests and evaluation scripts
- Staged final evaluation JSON/CSV results
- Excluded intermediate evaluation checkpoint backups from the intended commit

## Remaining Submission Checks

- Review final documentation and Git staging
- Verify `.env` and secrets are not staged
- Confirm required screenshots are present
- Confirm demo video is prepared and accessible
- Confirm any required AI conversation-history deliverable
- Commit and push the development branch
- Merge into main after final verification
- Confirm the GitHub repository contains the required submission files

## Known Limitations

- Evaluation used one small PDF corpus
- Faithfulness was measured using an LLM judge
- Golden relevance labels were not all independently audited
- DOCX ingestion requires final end-to-end validation
- Guardrails are not a complete defense against prompt injection
- Production deployment, load testing and security audit are outside the verified scope

## Supporting Evidence

- `EVAL.md`
- `evals/results/retrieval_results.json`
- `evals/results/faithfulness_results.json`
- `evals/results/chunk_experiments.json`
- `tests/`
- `docs/ai-history/`
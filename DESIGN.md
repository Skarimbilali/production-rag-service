
# Production RAG Service — System Design

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
Character-based Chunking
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
| Frontend | HTML/CSS/JavaScript | Lightweight browser dashboard |
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
- Chunking type: Character-based
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

Latest verified run:

`35 passed`

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
- DOCX ingestion requires final end-to-end validation
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

- `README.md` — Setup and usage
- `EVAL.md` — Evaluation and experiments
- `AI_USAGE.md` — AI-assistance disclosure
- `DEVELOPMENT_LOG.md` — Development history
- `evals/` — Evaluation scripts and results

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

A controlled baseline-versus-hybrid benchmark is
still required.

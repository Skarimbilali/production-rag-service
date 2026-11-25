# AI Usage Documentation

## Project

Portfolio 01 — Production RAG Service

## AI Assistant

- Tool: OpenAI ChatGPT
- Model: GPT-6
- Purpose: Architecture, implementation assistance, debugging, testing, evaluation, documentation and Git guidance
- Primary implementation responsibility: Developer

## How AI Was Used

### 1. Architecture and Planning

ChatGPT assisted with organizing the application into modular components:

- FastAPI API endpoints
- Document ingestion and validation
- Text extraction and chunking
- Embedding generation
- ChromaDB vector storage
- Retrieval and answer generation
- Input/output guardrails
- Browser-based frontend
- Testing and evaluation

### 2. Implementation Assistance

AI-generated suggestions and code were used during development of:

- PDF/DOCX processing modules
- Character-based chunking with source metadata
- Multilingual E5 embeddings
- Vector search and retrieval
- Groq LLM integration
- Grounded answers with citations
- Input and output guardrails
- Frontend HTML, CSS and JavaScript
- Automated tests and evaluation scripts

The developer copied, integrated, executed and iteratively corrected code in the local repository.

### 3. Debugging and Troubleshooting

AI assistance included investigating:

- Python import and module errors
- Git branch and command-line issues
- Document upload and deletion behavior
- ChromaDB integration
- Groq API rate limiting
- Faithfulness evaluation checkpoint handling
- LLM judge inconsistency for short numerical answers
- Retrieval relevance-label errors
- Local PDF path resolution
- Git staging and Windows line-ending warnings

### 4. Testing and Evaluation

AI helped develop and interpret:

- A 25-question golden dataset
- Retrieval Hit@K, Recall@K and MRR evaluation
- Answer-refusal checks
- LLM-as-judge faithfulness evaluation
- Chunk-size comparison experiments
- Prompt-injection test cases

Latest observed results:

| Evaluation | Observed Result |
|---|---|
| Automated pytest suite | 134 passed, 1 third-party warning |
| Retrieval Hit@5 | 100.00% |
| Retrieval Recall@5 | 97.50% |
| Retrieval MRR@5 | 0.7958 |
| LLM-judged faithfulness | 20/20 (100%) |
| Faithfulness judge consistency | v2_question_aware only |
| Selected chunk configuration | 800 characters / 150 overlap |

These results are based on a limited document corpus and evaluation dataset. The faithfulness result is an LLM judge assessment rather than an independently verified accuracy guarantee.

## Examples of AI-Assisted Corrections

### Retrieval Evaluation Label Correction

Question Q005 was initially marked as unsuccessful because only chunk position 0 was labeled relevant.

Manual inspection showed that chunk positions 0 and 1 both contained the supporting statement about running Qdrant through Docker.

The relevance label was corrected from `[0]` to `[0, 1]`, and retrieval metrics were recomputed.

### Faithfulness Judge Improvement

An earlier judge evaluated answers without the original question. This caused a short numerical answer to be marked unfaithful despite supporting evidence.

The evaluation prompt was updated to include the original question. Previously generated answers were re-evaluated consistently using the version 2 question-aware judge.

### Chunking Decision

AI assisted in comparing three chunk configurations using temporary ChromaDB collections. The developer retained the existing 800/150 baseline based on the preliminary experiment results.

## Developer Responsibilities

The developer remains responsible for:

- Understanding and reviewing AI-suggested code
- Executing and testing the application
- Verifying API behavior and evaluation results
- Managing credentials and local configuration
- Reviewing security limitations
- Validating Git changes before publishing
- Ensuring assignment requirements are satisfied

AI-generated code and explanations were not treated as automatically correct.

## Known Limitations of AI Assistance

- Generated code required local testing and correction.
- Prompt-injection guardrails are not comprehensive.
- LLM judge results can contain errors or bias.
- Evaluation labels require human review.
- The current corpus is too small to establish production-wide performance.
- DOCX upload and deletion were successfully tested; comprehensive security and production testing remain outstanding.

## Conversation and Prompt History

Development summaries are stored under `docs/ai-history/`, where available.

The original ChatGPT conversations are the primary record of AI interaction. The complete conversation export or consolidated prompt-history artifact has not yet been verified as part of this repository.

The documentation in this file is a disclosure and summary of AI assistance, not a substitute for the complete original conversation history.
---

## Final Development Phase

### React Frontend Assistance

ChatGPT assisted the developer with:

- Choosing React + Vite.
- Resolving the Windows `spawnSync cmd.exe ENOENT` installation issue.
- Configuring the Vite development proxy.
- Developing the React dashboard components.
- Implementing PDF/DOCX upload, document listing and deletion.
- Integrating RAG question answering.
- Displaying citations, retrieved chunk text and similarity scores.
- Building the monitoring dashboard.
- Creating responsive CSS.
- Reviewing browser and API verification results.

The original HTML/CSS/JavaScript frontend was preserved.

The developer installed dependencies, integrated source files, ran the React application, tested API responses, verified the production build and committed the code.

### Multi-Document Retrieval and Evaluation

AI assistance included diagnosis of multi-PDF retrieval ranking problems, smart chunking improvements, structured extraction, hybrid reranking and evaluation design.

The controlled semantic-only versus hybrid benchmark reported:

| Metric | Semantic-only | Hybrid |
|---|---:|---:|
| Hit@5 | 100.00% | 100.00% |
| Recall@5 | 97.50% | 100.00% |
| MRR@5 | 0.7958 | 0.8750 |

The experiment used a limited corpus and position-based relevance labels requiring independent review.

### Security and Multilingual Features

ChatGPT assisted in implementing and testing document-level guardrails and English/Roman Urdu generation.

Observed security verification included rejection of a malicious DOCX with HTTP 400 and successful upload and deletion of a legitimate DOCX.

The developer remained responsible for executing and validating these tests.

### Monitoring Assistance

ChatGPT assisted in developing:

- FastAPI request monitoring.
- Retrieval and generation timing.
- A JSON `/metrics` endpoint.
- Monitoring regression tests.
- React dashboard integration.

Metrics are in memory and reset on restart.

### Final Testing and Git

The latest verified automated regression reported:

**134 passed, 1 third-party deprecation warning.**

React production build and browser integration were verified.

ChatGPT also provided assistance with Git staging, line-ending warnings, commit verification, branch workflow and documentation updates.

React frontend commit:

`61d38e9`

Branch:

`development`

### AI Assistance Limitations

- All AI-generated code required developer integration and local testing.
- Reported measurements depend on the tested environment and corpus.
- Guardrails do not eliminate all prompt-injection risk.
- LLM judge results are not independently verified factual accuracy.
- Some retrieval relevance labels still require human auditing.
- Cloud deployment and large-scale concurrency remain unverified.
- A complete original ChatGPT conversation export has not been verified as submitted evidence.

The developer retains responsibility for the final implementation, correctness, security, disclosure and assignment submission.

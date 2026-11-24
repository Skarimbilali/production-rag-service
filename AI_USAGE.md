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
| Automated pytest suite | 35 passed |
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
- DOCX processing implementation has not been independently confirmed by a final end-to-end upload test.

## Conversation and Prompt History

Development summaries are stored under `docs/ai-history/`, where available.

The original ChatGPT conversations are the primary record of AI interaction. The complete conversation export or consolidated prompt-history artifact has not yet been verified as part of this repository.

The documentation in this file is a disclosure and summary of AI assistance, not a substitute for the complete original conversation history.
# Production RAG Service — AI Prompt and Development History

Period: 19–24 November 2026
Assistant: OpenAI ChatGPT (GPT-6)
Repository: https://github.com/Skarimbilali/production-rag-service

## Evidence and completeness statement

This submission combines existing day-wise development notes,
selected original prompts and reconstructed summaries.
It is not a complete verbatim ChatGPT conversation export.
Entries with unverified dates are marked accordingly.

---

# AI Prompt History - 2026-11-19

Project: Production RAG Service
Working branch: development

## Entry 001 - Project Structure
Prompt: "ni pdf ke hisab se structure create kro"
Task: Create a layered FastAPI project structure.
Result: Project directories and files created.

## Entry 002 - Environment Verification
Reported: "No broken requirements found."
Result: Python dependencies verified.

## Entry 003 - FastAPI Health Check
Reported: HTTP 200 with healthy service response.
Result: FastAPI and Swagger UI verified.

## Entry 004 - Document Chunking
Reported: "Chunks created: 4"
Result: Baseline chunking test passed.

## Entry 005 - Git Branching
Issue: Example Git output executed as commands.
Result: main and development branches configured.

## Entry 006 - Missing Embedding Function
Error: ImportError for embed_query.
Root cause: embeddings.py was empty.
Correction: Implemented class-based EmbeddingService.

## Entry 007 - Multilingual Embedding Test
Model: intfloat/multilingual-e5-small
Input: Roman Urdu leave-policy question
Result: 384-dimensional embedding generated.
Logger: Successfully verified.

## Entry 008 - Vector Database
Task: ChromaDB service implementation.
Status: Code provided; execution not yet verified.

## Important
This document is a reconstructed summary of
available conversation details, not a complete
verbatim prompt and response transcript.

Preserve the complete original chat separately.

## Entry 010 - pytest Configuration Fix
- Error: unexpected line in pytest.ini.
- Cause: PowerShell here-string marker saved in configuration file.
- Fix: Replaced contents using Set-Content.
- Verification: 3 tests passed in 25.20 seconds without warnings.

## Document API Testing
Task: Test upload, duplicate detection, listing and deletion through Swagger UI.
AI assistance: Step-by-step API testing instructions.
Developer result: All five API checks passed.
Pending: Deleted document retrieval verification.
Original prompts and responses: Refer to saved ChatGPT conversation.


---

# AI Prompt History - 20 November 2026

Project: Production RAG Service
Branch: development
AI Assistant: ChatGPT

## Prompt 1 - Document Upload API
Task: Implement PDF/DOCX upload using FastAPI.
Files: app/ingestion/service.py, app/api/documents.py
Result: HTTP 201 Created; 7 chunks stored.

## Prompt 2 - Duplicate Document Detection
Task: Test SHA-256 duplicate detection.
Result: HTTP 409 Conflict.
Message: Document already exists.

## Prompt 3 - Document Listing
Task: Verify uploaded documents through API.
Result: HTTP 200 OK; document listed with 7 chunks.

## Prompt 4 - Document Deletion
Task: Delete uploaded document and its vectors.
Result: HTTP 204 No Content.
Verification: GET /documents returned [].

## Prompt 5 - Retrieval Implementation
Task: Implement class-based RetrievalService.
File: app/retrieval/retriever.py
Requirements: Central logger, validation, top-k and threshold.
Result: Empty database retrieval returned 0 chunks.

## Prompt 6 - English and Roman Urdu Retrieval
Task: Verify semantic retrieval in both languages.
File: tests/test_retrieval.py
Result: 2 pytest tests passed in 19.95 seconds.

## Prompt 7 - Similarity Score Verification
Original question: RAG project kaise kaam karta hai?
Model: intfloat/multilingual-e5-small
Top-k: 3
Threshold: 0.0

Results:
Chunk 0: 0.8807 - Page 1
Chunk 4: 0.8766 - Page 2
Chunk 3: 0.8523 - Page 1

Status: Retrieval execution passed.
Pending: Ground-truth relevance evaluation.

## Important
These entries summarize AI-assisted work and test results.
They are not the complete verbatim ChatGPT transcript.
Preserve the original conversation separately.

## Additional Original Prompts - 20 November 2026

### Prompt 08
User: "next development krte hen aur baki kitna rehta hai ?"
AI Assistance: Reviewed assignment progress and provided RetrievalService implementation.
File: app/retrieval/retriever.py
Result: Empty database retrieval returned 0 chunks.

### Prompt 09
User: "Retrieved chunks: 0"
AI Assistance: Explained the empty database result and guided PDF upload testing.

### Prompt 10
User: Reported HTTP 201 Created for RAG_Project_Steps_Roman_Urdu.pdf.
AI Assistance: Guided English and Roman Urdu retrieval testing.
Result: 7 chunks stored.

### Prompt 11
User: Reported 2 pytest tests passed in 19.95 seconds.
AI Assistance: Reviewed test results and provided similarity inspection command.
Files: tests/test_retrieval.py

### Prompt 12
User: Shared Roman Urdu retrieval logs and similarity scores.
AI Assistance: Analyzed retrieved chunks and explained similarity versus answer accuracy.
Results:
- Chunk 0: 0.8807, Page 1
- Chunk 4: 0.8766, Page 2
- Chunk 3: 0.8523, Page 1

### Prompt 13
User: "thak gaya hun"
AI Assistance: Summarized progress and provided Git save instructions.

### Prompt 14
User: "promp wagera save krne hen"
AI Assistance: Provided PowerShell commands for AI history and development log.
Result: History documentation created.

### Prompt 15
User: Reported history file sizes.
AI Assistance: Verified saved summaries and provided Git commit instructions.

### Prompt 16
User: "prompt history bhe update krni hai"
AI Assistance: Provided instructions to append additional prompt records.

## Documentation Note
These entries preserve selected user prompts and summaries
of AI responses. They are not the complete verbatim transcript.
The original ChatGPT conversation must also be preserved.


---

# AI Development History — 21 November 2026

Project: Production RAG Service
Record type: Reconstructed development summary
Source status: Exact prompts and their timestamps are not available.

## Development work under review

The development period after the initial document API and
retrieval implementation included work on:

- Grounded answer generation with the Groq LLM
- Answer citations and refusal handling
- Input and output guardrails
- Automated generation and security tests

These activities are supported by the subsequent project
implementation and development records. The precise
attribution of each activity to 21 November is unverified.

## Prompt history limitation

No verbatim user prompt can be reliably assigned to this
date from the currently available records.

This document is a reconstructed development-history note,
not a complete original ChatGPT transcript.

## Related project files

- app/generation/generator.py
- app/generation/llm_client.py
- app/guardrails/guardrails.py
- tests/test_generation.py
- tests/test_guardrails.py


---

# AI Development History — 22 November 2026

Project: Production RAG Service
Record type: Reconstructed development summary
Source status: Exact prompt timestamps are not available.

## Development work under review

The subsequent project work included:

- Frontend dashboard development with HTML, CSS and JS
- Connecting the frontend to document management APIs
- Displaying grounded answers and citations
- Showing retrieved chunks and similarity scores
- Testing direct and indirect prompt injection

The project evidence supports these activities, but does
not establish which were completed specifically on
22 November 2026.

## Prompt history limitation

No original prompt text is attributed to this date without
a verifiable dated conversation record.

## Related project files

- frontend/index.html
- frontend/style.css
- frontend/script.js
- tests/test_indirect_injection.py
- tests/manual_live_injection.py


---

# AI Development History — 23 November 2026

Project: Production RAG Service
Record type: Reconstructed development summary
Source status: Per-prompt timestamps are not verified.

## Development work under review

The evaluation phase included:

- Preparing the 25-question golden dataset
- Implementing retrieval Hit@K, Recall@K and MRR
- Measuring refusals for unanswerable questions
- Creating the LLM-as-judge faithfulness evaluation
- Handling Groq rate limits and resumable checkpoints

These activities are documented as part of the project
development sequence. Their exact completion dates
cannot be reconstructed reliably.

## Prompt history limitation

This document does not fabricate original user prompts.
The original conversation export remains the authoritative
source for any missing verbatim transcripts.

## Related project files

- evals/golden_questions.json
- evals/run_evals.py
- evals/run_faithfulness.py
- evals/results/


---

# AI Prompt History — 24 November 2026

Project: Portfolio 01 — Production RAG Service
Branch: development, followed by main
Record type: Selected actual user prompts and verified outcomes

## Entry 01 — Faithfulness checkpoint

User: "Q016 removed from checkpoint"

AI assistance:
- Explained checkpoint verification.
- Updated the faithfulness evaluation workflow.
- Introduced question-aware judging.

Developer verification:
- Completed: 19
- Q016 present: False

## Entry 02 — Faithfulness judge comparison

User supplied:
"judge_versions: ['v1_question_unaware', 'v2_question_aware']"
"mixed_judge_versions: True"

AI assistance:
- Identified non-comparable judge versions.
- Recommended rejudging saved answers without regenerating them.
- Supplied an updated run_faithfulness.py script.

## Entry 03 — Standardized faithfulness

Developer reported:
- 20 answerable questions
- 20 completed evaluations
- 20 faithful answers
- 0 refusals
- judge_versions: ['v2_question_aware']
- mixed_judge_versions: False

Result:
100% LLM-judged faithfulness under the consistent v2 judge.

Limitation:
Automated LLM-as-judge result, not an independent accuracy guarantee.

## Entry 04 — Chunking implementation review

User provided the complete app/ingestion/chunker.py code.

AI assistance:
- Confirmed baseline size of 800 characters.
- Confirmed overlap of 150 characters.
- Planned controlled size/overlap comparisons.

## Entry 05 — Source PDF path error

User reported:
"FileNotFoundError: Source PDF not found automatically."

AI assistance:
- Explained path discovery.
- Provided a PowerShell command to locate the source PDF.

Developer verified:
D:\Agentic-Ai-Course\RAG_Project_Steps_Roman_Urdu.pdf

## Entry 06 — Chunk experiments

Developer supplied the completed results:

A — 256/50, 21 chunks:
Hit@5 85%, Recall@5 64.58%, MRR@5 0.7225

B — 512/80, 11 chunks:
Hit@5 100%, Recall@5 86.25%, MRR@5 0.7283

C — 800/150, 7 chunks:
Hit@5 100%, Recall@5 95%, MRR@5 0.8583

Decision:
Keep the existing 800/150 baseline.

Limitation:
Evidence-phrase labels were provisional.

## Entry 07 — Documentation of experiments

User reported:
"EVAL.md:752:## Chunk-Size Configuration Experiments"

AI assistance:
Confirmed that the experiment section was added.

## Entry 08 — Golden question Q005

User shared Q005 and reported that its relevant positions
were initially [0].

AI assistance:
- Inspected recorded retrieval positions [6, 1, 3].
- Guided comparison with actual stored chunk text.
- Established that chunks 0 and 1 contained the Docker/Qdrant answer.

Developer changed the golden label from [0] to [0, 1].

## Entry 09 — Corrected retrieval evaluation

Developer reported:
- Total questions: 25
- Answerable: 20
- Unanswerable: 5
- Hit@5: 1.0000
- Recall@5: 0.9750
- MRR@5: 0.7958

AI assistance:
Interpreted metrics and moved the project into
submission finalization.

## Entry 10 — Finalization priority

User: "finish ki taraf kab jaengy  ?"

AI assistance:
Prioritized final documentation, Git staging,
screenshots and submission over new features.

## Entry 11 — Git repository audit

Developer provided git status and tracked file listing.

AI assistance:
- Identified final evaluation files.
- Separated deliverables from temporary checkpoint backups.
- Guided staging of 25 initial files.

## Entry 12 — Regression testing

Developer reported:
"35 passed in 24.53s"

AI assistance:
Confirmed passing automated tests.

## Entry 13 — Documentation audit

Developer showed:
- README.md: empty
- DESIGN.md: empty
- AI_USAGE.md: existing but outdated
- DEVELOPMENT_LOG.md: existing but outdated
- EVAL.md: populated

AI assistance:
Prepared completed README, DESIGN, AI_USAGE and
DEVELOPMENT_LOG content.

## Entry 14 — Documentation verification

Developer reported:
- README.md: 4152 bytes
- DESIGN.md: 5919 bytes
- 29 staged files
- Five documentation files staged
- No secret filename detected in staged-file check

## Entry 15 — Commit and development push

Developer reported commit:
5931194

Commit message:
"Complete production RAG service, evaluations and documentation"

29 files were committed and the development branch
was pushed to GitHub.

Whitespace issues were reported by Git before commit;
the commit nevertheless completed.

## Entry 16 — Main branch merge

Developer performed a fast-forward merge and pushed main.

Verified remote main commit:
5931194

Repository:
https://github.com/Skarimbilali/production-rag-service

## Entry 17 — Screenshots

User: "screen shots lelo then add kr do"

AI assistance:
Provided a five-screenshot capture plan covering:
dashboard, upload, answers, retrieval and Swagger.

Status:
Actual screenshot capture and upload not verified.

## Entry 18 — AI prompt history requirement

User:
"main important bt prompts bhe muje submit krne hen day1 se leky abhi tak history"

User:
"mene tmhe pehly bht bataya tha ti tum khud manage kro exact instruction already bta chuka hun"

User:
"kro ready phi"

AI assistance:
Prepared a submission-oriented history package
using available prompt evidence and clearly labelled
reconstructed entries for unverified dates.

## Integrity declaration

This file contains selected actual conversation excerpts
and summaries of verified developer outcomes.

It is not the complete verbatim transcript.
Original conversation exports should be retained separately
if the assignment explicitly requires every message.


---


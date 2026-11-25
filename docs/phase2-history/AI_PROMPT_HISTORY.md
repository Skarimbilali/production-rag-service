# Phase 2 - AI Prompt History

Date: 24 November 2026
Branch: development
Project: Production RAG Service

## Goal

Improve generic question answering across multiple PDFs
without hardcoding document-specific answers.

## Selected User Prompts and AI Assistance

### 1. Generic PDF support
User: "system aisa ho ke koi bhe pdf ho question asnser to sahi de"
AI: Recommended smart chunking, structured extraction,
generic retrieval and broader testing.

### 2. Development workflow
User: "ye kaam develoment branch pe banaegy. one by one"
AI: Established one-file-change, test and verify workflow.

### 3. Hardcoding concern
User: "tum chezen hardcoded to ni kr rahe"
AI: Explained dynamic filename, page and section metadata.

### 4. Conditional reasoning failures
User reported incorrect refusals for maternity eligibility,
probation resignation and promotion questions.
AI: Reviewed retrieval, generation and vector-store code.

### 5. Automatic multi-document retrieval
User: "bhaly do pdf ak sath ho no issue mera sawal relavent pdf se kre"
AI: Proposed semantic and keyword hybrid reranking
without mandatory manual PDF selection.

### 6. Complete updated files
User: "puri file bhejo muje kia pata kahan paste kran hai"
AI: Provided full updated generator.py implementation.

## Code Changes

- app/ingestion/chunker.py: Smart chunking
- app/ingestion/service.py: Dynamic source context
- app/ingestion/extractor.py: PDF tables and heading detection
- app/generation/generator.py: Generic reasoning instructions
- app/vector_store/store.py: Hybrid retrieval
- requirements.txt: pdfplumber dependency

## Verification

- 35 automated tests passed in 27.68 seconds.
- TechNova manual: 20 extracted sections, 6 structured tables.
- Promotion and probation answers improved after reranking.
- International hotel-limit hallucination corrected.
- Multiple calculation and multi-section answers manually checked.

## AI Disclosure

AI drafted code and documentation.
The user applied code changes, ran tests and performed
manual evaluations.

This file contains selected prompts and summaries.
It is NOT a complete verbatim transcript of the AI conversation.
Complete conversation history must be exported separately
if required for submission.

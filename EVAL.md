# Production RAG Service — Evaluation Report

**Project:** Portfolio 01 — Production RAG Service
**Evaluation Date:** 24–25 November 2026
**Framework:** Custom Python evaluation scripts with LLM-as-a-Judge
**Backend:** FastAPI
**Embedding Model:** `intfloat/multilingual-e5-small`
**Vector Database:** ChromaDB
**LLM:** Groq — `openai/gpt-oss-20b`

---

## 1. Evaluation Overview

The Production RAG Service is designed to answer questions using information retrieved from uploaded documents.

The purpose of this evaluation is to measure retrieval quality, assess answer faithfulness, compare alternative chunking configurations, identify system failures, and document improvements introduced during development.

A working demonstration alone is not sufficient to establish retrieval quality. The evaluation therefore includes quantitative retrieval metrics, an automated faithfulness judge, and manual testing using different documents.

The evaluation was conducted in two stages:

**Phase 1 — Initial RAG Implementation**

- PDF and DOCX ingestion
- Document extraction and character-based chunking
- Multilingual E5 embeddings
- ChromaDB semantic retrieval
- Groq answer generation
- Citation handling and refusals
- Golden-question retrieval evaluation
- Chunk-size comparisons
- LLM-as-a-Judge faithfulness evaluation

**Phase 2 — Multi-Document Retrieval Improvements**

- Diagnosis of retrieval failures involving two uploaded PDFs
- Paragraph- and sentence-aware smart chunking
- Improved PDF heading and table extraction
- Dynamic source context
- Hybrid semantic and keyword-based reranking
- Improved conditional reasoning and answer grounding
- Manual before-and-after testing

The results from Phase 1 and Phase 2 are reported separately to avoid presenting historical evaluation scores as measurements of the final hybrid implementation.

---

## 2. Evaluation Objectives

The evaluation addresses the following questions:

1. Does the retriever find the correct document evidence?
2. Does relevant evidence appear within the final Top-K results?
3. How does chunk size affect retrieval quality?
4. Are generated answers supported by retrieved evidence?
5. Does the system refuse unsupported questions?
6. Can the system retrieve evidence correctly when multiple PDFs are uploaded?
7. What failures remain after the Phase 2 improvements?

---

## 3. System Configuration

| Component | Configuration |
|---|---|
| Backend | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| PDF extraction | pypdf and pdfplumber |
| DOCX extraction | python-docx |
| Chunking baseline | 800 characters |
| Chunk overlap | 150 characters |
| Embedding model | `intfloat/multilingual-e5-small` |
| Embedding dimensions | 384 |
| Document embedding prefix | `passage:` |
| Query embedding prefix | `query:` |
| Vector database | ChromaDB |
| Similarity metric | Cosine |
| Final retrieval depth | Top-K = 5 |
| Similarity threshold | 0.30 |
| LLM | Groq `openai/gpt-oss-20b` |
| Faithfulness judge | Question-aware binary LLM judge |
| Judge version | `v2_question_aware` |

### Phase 2 Retrieval Configuration

The final Phase 2 implementation uses a hybrid retrieval approach.

ChromaDB first identifies semantic candidates. The retrieval layer then considers keyword relevance and reranks the candidates before returning the final relevant chunks.

The implementation uses semantic and keyword relevance rather than relying exclusively on vector similarity.

This is important when multiple uploaded documents contain overlapping terminology.

The candidate pool and final Top-K results are separate concepts: the system can examine more candidates internally before selecting the five chunks returned to the user.

---

## 4. Evaluation Dataset

The original golden dataset contains **25 questions**:

| Question category | Count |
|---|---:|
| Answerable questions | 20 |
| Unanswerable questions | 5 |
| Total | 25 |

The golden questions are stored in:

`evals/golden_questions.json`

Questions include source-related and unsupported-answer cases.

The golden set is intended to measure whether the system retrieves evidence from the correct document and whether answers are supported by that evidence.

### Test Documents

Two PDFs were also used in Phase 2 testing:

**Document A: RAG Project Guide**

- Two-page project guide
- Contains instructions and project requirements
- Used in earlier chunking experiments
- Used to test retrieval of project-related information

**Document B: TechNova HR Policy Manual**

- Fourteen-page simulated company HR manual
- Contains employee policies, eligibility conditions, leave entitlements, resignation rules, allowances and tables
- Used to test reasoning, calculations and structured document retrieval

The combination was useful because the two PDFs contain different subjects and different document structures.

This made it possible to observe whether the system retrieved content from the document relevant to each question.

### Dataset Limitations

The original golden set is relatively small.

Its relevance labels have not been fully independently audited.

The original evaluation was not a comprehensive multi-document benchmark of the final hybrid system.

---

## 5. Retrieval Evaluation Metrics

Three standard retrieval metrics were used.

### 5.1 Hit Rate@K

Hit Rate@K measures the proportion of questions for which at least one relevant document chunk appears within the first K retrieved chunks.

A higher value indicates that relevant evidence is found more consistently.

### 5.2 Recall@K

Recall@K measures how much of the labelled relevant evidence is retrieved within the first K chunks.

A higher value indicates that more of the expected evidence is recovered.

### 5.3 Mean Reciprocal Rank (MRR@K)

MRR measures how early the first relevant result appears in the ranked retrieval list.

A relevant result appearing in position one receives a reciprocal rank of 1.0.

A relevant result appearing in position two receives a reciprocal rank of 0.5.

Higher MRR indicates that relevant evidence tends to appear earlier.

---

## 6. Original Golden-Set Retrieval Results

The previously reported corrected golden-label evaluation produced:

| Metric | Result |
|---|---:|
| Hit@5 | 100.00% |
| Recall@5 | 97.50% |
| MRR@5 | 0.7958 |

### Interpretation

The historical evaluation indicated that relevant evidence appeared within the first five results for all questions counted in the Hit@5 measurement.

Recall@5 of 97.50% indicated that most labelled relevant evidence was recovered.

MRR@5 of 0.7958 indicated that relevant evidence generally appeared near the top of the ranked results.

### Important Qualification

These numbers were recorded before the final Phase 2 hybrid retrieval modifications.

They describe the earlier evaluation configuration.

They are **not** a fresh measurement of the final hybrid retrieval pipeline.

The results also depend on the correctness of the original relevance labels.

---

## 7. Chunking Configuration Experiments

### Objective

The purpose of the chunking experiment was to compare alternative chunk sizes and overlaps using the same document and questions.

The experiment used:

- Document: `RAG_Project_Steps_Roman_Urdu.pdf`
- Embedding model: `intfloat/multilingual-e5-small`
- Vector database: Temporary ChromaDB collections
- Similarity metric: Cosine
- Evaluation questions: 20 answerable questions
- Relevance labels: Provisional evidence-phrase matching

### Compared Configurations

| Configuration | Chunk size | Overlap | Generated chunks |
|---|---:|---:|---:|
| A | 256 | 50 | 21 |
| B | 512 | 80 | 11 |
| C | 800 | 150 | 7 |

### Top-5 Retrieval Results

| Configuration | Hit@5 | Recall@5 | MRR@5 |
|---|---:|---:|---:|
| A — 256/50 | 85.00% | 64.58% | 0.7225 |
| B — 512/80 | 100.00% | 86.25% | 0.7283 |
| C — 800/150 | 100.00% | 95.00% | 0.8583 |

### Top-3 Retrieval Results

| Configuration | Hit@3 | Recall@3 | MRR@3 |
|---|---:|---:|---:|
| A — 256/50 | 75.00% | 57.08% | 0.7000 |
| B — 512/80 | 80.00% | 65.00% | 0.6833 |
| C — 800/150 | 100.00% | 92.50% | 0.8583 |

### Decision

Configuration C achieved the strongest retrieval results in the preliminary experiment.

The project therefore retained the baseline:

- **Chunk size: 800 characters**
- **Overlap: 150 characters**

### Trade-offs

Smaller chunks may provide more precise evidence but can lose context that spans multiple sentences.

Larger chunks may preserve more context but can include unrelated information.

The 800-character configuration performed best in the evaluated small document.

This does not establish that the same configuration is optimal for every document or corpus.

### Limitations

The experiment used one small two-page PDF.

Relevance labels were based on selected evidence phrases rather than a fully independently verified annotation set.

Generation quality, latency and cost were not separately compared for each chunking configuration.

### Evidence Files

- `evals/run_chunk_experiments.py`
- `evals/results/chunk_experiments.json`
- `evals/results/chunk_experiments.csv`

---

## 8. Answer Faithfulness Evaluation

### Objective

The purpose of faithfulness evaluation was to check whether generated answers were supported by the retrieved document evidence.

The project implemented a question-aware LLM judge.

### Judge Methodology

For each answerable golden question, the evaluator:

1. Retrieves relevant document chunks.
2. Generates an answer using the RAG service.
3. Provides the original question, answer and retrieved evidence to the judge.
4. Requests a structured JSON judgment.
5. Records the judgment and explanation.
6. Saves results to JSON.

The judge is instructed to mark an answer unfaithful when factual claims contradict or exceed the supplied evidence.

The original question is included to help interpret short or numerical answers.

### Judge Configuration

| Property | Value |
|---|---|
| Judge type | Binary LLM-as-a-Judge |
| Judge version | `v2_question_aware` |
| LLM provider | Groq |
| Model | `openai/gpt-oss-20b` |
| Output | JSON |
| Primary judgment | `faithful: true/false` |
| Explanation | `reason` |

### Previously Reported Faithfulness Results

| Metric | Result |
|---|---:|
| Answerable questions | 20 |
| Completed evaluations | 20 |
| Judged answers | 20 |
| Faithful answers | 20 |
| Refused answers | 0 |
| LLM-judged faithfulness | 100.00% |
| Mixed judge versions | False |

### Interpretation

The judge classified all 20 evaluated answers as supported by the retrieved evidence.

This is an **LLM-judged faithfulness result**, not an independent guarantee of factual accuracy.

The same model family was used for answer generation and judging.

### Judge Reliability Limitations

The judge was not independently validated against a separate human-labelled set.

The evaluation did not establish judge precision, recall or inter-annotator agreement.

A judge may incorrectly accept unsupported claims or reject answers that are actually valid.

The evaluation also did not independently measure correctness against every reference answer.

Therefore, the 100% faithfulness result must not be interpreted as 100% real-world answer accuracy.

### Evaluation Script

`evals/run_faithfulness.py`

The script supports:

- Answer generation
- Faithfulness judging
- Retry and backoff for Groq rate limits
- Checkpoint saving
- Resuming interrupted evaluations
- Rejudging selected questions
- Saving final JSON results

### Commands

```bash
python evals/run_faithfulness.py
```

To rejudge an existing question:

```bash
python evals/run_faithfulness.py --rejudge Q016
```

### Evidence Files

- `evals/golden_questions.json`
- `evals/run_faithfulness.py`
- `evals/results/faithfulness_results.json`

Checkpoint files may also exist locally; their presence in Git must be verified before citing them as submitted evidence.

---

## 9. Phase 2 — Multi-Document Retrieval Problem

### 9.1 Initial Behavior

During the initial implementation, the RAG service was able to answer questions using an uploaded PDF.

A second PDF was then uploaded into the same document collection.

The system continued answering questions from the first document, but some questions associated with the second document failed despite the relevant information existing in the uploaded files.

This exposed a multi-document retrieval quality problem.

### 9.2 Diagnosis

The retrieved chunks and their rankings were inspected.

The investigation showed that the required evidence was not always included in the final Top-K results.

In some cases, semantic retrieval prioritized chunks from a less relevant document.

This meant the generation layer did not receive the evidence required to answer the user's question.

Consequently, the LLM could return a refusal even though the answer existed in the indexed document collection.

### 9.3 Root Cause

The principal observed issue was **retrieval ranking across multiple indexed documents**.

The problem was not simply a failed document upload.

Both PDFs were accessible to the retrieval system, but the ranking of semantically similar chunks did not always correspond to the user's intended question.

This distinction was important during debugging.

### 9.4 Example Failure Cases

The following questions exposed problems during manual testing:

**Promotion eligibility**

The employee had completed 15 months in the current grade and had strong performance ratings.

The relevant policy required at least 18 months, but initial retrieval did not consistently return the required evidence.

**Probation resignation**

The HR manual contained the required written notice period.

Initial retrieval failed to bring the relevant policy into the final context, causing a refusal.

**International travel hotel limit**

The system incorrectly interpreted an international per diem allowance as an international hotel limit.

This was a generation-grounding and table-interpretation issue in addition to retrieval relevance.

---

## 10. Phase 2 — Improvements Implemented

Five implementation areas were improved.

### 10.1 Smart Chunking

**File:** `app/ingestion/chunker.py`

The chunking logic was improved to consider paragraph and sentence boundaries.

The goal was to preserve related information and reduce fragmentation of important policy conditions.

The system retained the existing 800-character chunk size and approximately 150-character overlap configuration.

### 10.2 Dynamic Source Context

**File:** `app/ingestion/service.py`

Chunks received additional dynamic source context based on their originating document.

Relevant context includes:

- Filename
- Page
- Section, when detected

This makes source information more explicit during retrieval and generation.

The values are derived from uploaded documents rather than hardcoded for a specific PDF.

### 10.3 Improved PDF Extraction

**File:** `app/ingestion/extractor.py`

Extraction improvements included:

- Better numbered-section detection
- Structured PDF table extraction
- Preserving useful page-level information
- Clearer handling of unreadable or scanned PDFs

`pdfplumber` was introduced for improved table extraction.

During testing of the TechNova HR manual, the extractor returned 20 sections and identified six structured tables.

### 10.4 Hybrid Retrieval and Reranking

**File:** `app/vector_store/store.py`

The retrieval pipeline was enhanced to combine semantic similarity with keyword relevance.

The revised approach:

1. Generates a query embedding.
2. Retrieves a broader semantic candidate set from ChromaDB.
3. Calculates keyword relevance.
4. Combines semantic and keyword evidence for reranking.
5. Returns the final relevant Top-K chunks.

The search operates across uploaded documents without requiring the user to manually select a PDF.

The implementation uses a weighted combination of semantic and keyword relevance for reranking.

### 10.5 Grounded Generation Improvements

**File:** `app/generation/generator.py`

The generation instructions were improved to support:

- Conditional reasoning
- Policy eligibility checks
- Table-column interpretation
- Numeric calculations
- Currency and unit distinctions
- Correction of false assumptions
- Refusal when requested information is absent

These changes were intended to reduce unsupported conclusions when relevant evidence was retrieved.

---

## 11. Updated Phase 2 Retrieval Flow

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
Keyword Relevance Calculation
      |
      v
Hybrid Reranking
      |
      v
Final Top-K Evidence Chunks
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
Answer with Sources / Refusal
```

The revised pipeline is designed to improve retrieval relevance when the indexed collection contains multiple PDFs.

It does not guarantee that every relevant chunk will appear in every result.

---

## 12. Phase 2 — Before-and-After Manual Testing

The following table summarizes observed behavior before and after the Phase 2 retrieval and generation improvements.

| Test case | Before improvements | After improvements |
|---|---|---|
| Promotion with 15 months in grade | Incorrect refusal | Correctly identifies that 18-month requirement is unmet |
| Resignation during probation | Incorrect refusal | Correctly identifies seven days' written notice |
| International hotel limit | Incorrectly uses international per diem as hotel limit | Correctly states that international hotel limit is not specified |

### Retrieval Diagnostics

During investigation:

- The promotion policy evidence was previously ranked outside the required Top-K context.
- The probation policy was not consistently returned among the first relevant results.
- After hybrid reranking, the corresponding policy evidence appeared substantially higher in the inspected rankings.

These findings explain why retrieval configuration mattered.

### Evaluation Qualification

The before-and-after observations came from manual live tests.

They demonstrate improvements for the tested questions.

They do **not** constitute a complete controlled benchmark with aggregate before-and-after Hit@5, Recall@5 and MRR@5 values.

---

## 13. Additional TechNova HR Manual Testing

The following questions were also tested after the Phase 2 improvements.

| Question area | Observed answer |
|---|---|
| Annual leave | 20 working days |
| Maternity eligibility | Minimum six months of service |
| Maternity application | At least four weeks before expected delivery |
| G4 hospitalization limit | PKR 1,000,000 |
| G4 domestic hotel limit | PKR 30,000 |
| Performance bonus with PKR 150,000 basic salary and rating 4 | PKR 300,000, subject to eligibility |
| One Eid bonus on PKR 150,000 basic salary | PKR 150,000 |
| Employee provident fund contribution at 8% | PKR 12,000 |
| G4 resignation notice | 60 days |

These examples show that the service can combine information from policy text, tables and numerical rules.

However, not every answer's citations were independently audited.

---

## 14. Second PDF — Project Guide Testing

The RAG Project Guide was also used for live questions about:

- Golden-question distribution
- Ingestion configuration described in the guide
- Retrieval methods and comparison metrics
- API tests and performance requirements
- Existence of a numbered Step 13

The guide's numbered instructions ended at Step 12.

When asked about Step 13, the system returned an insufficient-evidence refusal.

This was a useful negative test because the requested section did not exist.

The remaining guide-related answers were observed during manual testing but were not included in a complete independent source-by-source audit.

### Important Distinction

The guide contains recommended technologies and settings.

These should not be confused with the project's actual implementation.

For example, the implementation uses ChromaDB and multilingual E5, regardless of alternative tools or chunking configurations described inside the uploaded guide.

---

## 15. Frontend Retrieval Verification

A successful frontend retrieval test was observed using the TechNova HR manual.

### Question

How many annual leave days are allowed?

### Generated Answer

20 working days

### Citations

- S1 — TechNova HR Policy Manual, page 5
- S4 — TechNova HR Policy Manual, page 5

### Retrieved Chunks

| Chunk | Similarity score | Source page |
|---|---:|---:|
| 1 | 83.53% | 5 |
| 2 | 80.31% | 4 |
| 3 | 83.87% | 5 |
| 4 | 83.51% | 5 |
| 5 | 79.24% | 14 |

The frontend displayed five retrieved chunks, their source text, filenames, page numbers and individual similarity scores.

The cited evidence on page 5 supported the annual leave answer.

The results also included less directly relevant chunks, indicating that retrieval precision can still improve.

This confirms the required frontend display functionality for the observed test case.

---

## 16. Evaluation Framework Selection

### Chosen Approach

The project uses custom Python retrieval-evaluation scripts and a question-aware LLM-as-a-Judge implementation.

### Reasons for Selection

- Integrates directly with the existing application code.
- Supports reproducible retrieval experiments.
- Allows question-level inspection.
- Saves machine-readable JSON and CSV outputs.
- Supports checkpointing and recovery.
- Provides traceable judge explanations.

### Alternative Frameworks

**RAGAS**

RAGAS offers standardized RAG evaluation metrics and would be useful for additional answer-quality measurement.

It is not claimed as an executed framework for the historical results in this report.

**Langfuse**

Langfuse offers tracing and observability for retrieval, model calls, latency and token usage.

It is not claimed as an implemented component of this project.

### Trade-offs

The custom evaluation approach provides implementation control but requires additional work to validate correctness, benchmark consistency and judge reliability.

A standardized evaluation framework can improve comparability, although it still requires high-quality source data and careful interpretation.

---

## 17. Testing Evidence

The latest previously reported automated regression result was:

**35 tests passed.**

The test suite covers implemented functionality across ingestion, retrieval, vector storage, generation and guardrails.

This result was reported after the Phase 2 retrieval modifications.

### Mandatory Jupyter Notebooks

Two Jupyter notebooks were subsequently created and pushed to the development branch.

**Notebook 1**

`notebooks/01_ingestion_pipeline.ipynb`

Covers extraction, chunking, metadata and embeddings.

Its successful execution reported:

- Three document embeddings
- 384-dimensional document vectors
- 384-dimensional query embedding
- `NOTEBOOK 1: PASSED`

**Notebook 2**

`notebooks/02_retrieval_generation.ipynb`

Covers document indexing, retrieval, answer generation, citations and refusal behavior.

The saved notebook was checked and reported:

- Seven code cells
- Seven executed cells
- Zero saved cell errors

A Windows-specific ChromaDB temporary-file cleanup issue was identified and the final cleanup step was adjusted to defer deletion while database files remained open.

The notebook results were committed in development commit:

`523c30a`

### Verification Limitations

Executed notebook cells are evidence of pipeline execution, but do not independently establish general answer quality.

The exact Groq answer and source correctness from Notebook 2 require separate review if used as evaluation evidence.

---

## 18. Error Analysis

### Failure 1 — Relevant Evidence Missing from Final Top-K

**Observed behavior:** Questions about existing HR policies were refused.

**Cause:** Relevant chunks did not consistently rank within the final context.

**Improvement:** Broader semantic candidate retrieval and hybrid keyword reranking.

### Failure 2 — Confusion Between Related Table Values

**Observed behavior:** International per diem allowance was interpreted as an international hotel limit.

**Cause:** Incorrect interpretation of related values in a structured table.

**Improvement:** Better structured extraction and more precise generation instructions.

### Failure 3 — Less Relevant Retrieved Chunks

**Observed behavior:** Some retrieved chunks contained information only indirectly related to the question.

**Cause:** Similarity retrieval and reranking are approximate.

**Remaining work:** Improve relevance calibration and benchmark retrieval precision.

### Failure 4 — Evaluation Limitations

**Observed issue:** Strong historical results did not fully represent the newer multi-document hybrid retrieval configuration.

**Remaining work:** Use a controlled evaluation with the same questions and corpus for both retrieval strategies.

---

## 19. Reproducibility

### Python Environment

Install the project's pinned dependencies:

```bash
python -m pip install -r requirements.txt
```

### Run Automated Tests

```bash
python -m pytest -q
```

### Run Chunking Experiments

```bash
python evals/run_chunk_experiments.py
```

### Run Faithfulness Evaluation

```bash
python evals/run_faithfulness.py
```

### Rejudge One Question

```bash
python evals/run_faithfulness.py --rejudge Q016
```

### Reproducibility Requirements

Before running the complete evaluation:

1. Configure the required environment variables.
2. Ensure the intended evaluation documents are available.
3. Ensure the vector database contains the correct indexed corpus.
4. Check that the golden question labels correspond to that corpus.
5. Record the current retrieval configuration.
6. Avoid reusing checkpoints produced under incompatible code or corpus configurations.
7. Save and review generated result files.

### Remaining Automation Gap

A single independently verified command that executes the complete retrieval, answer-quality and configuration-comparison evaluation has not yet been demonstrated.

The separate scripts above represent the documented existing workflow.

The latest hybrid implementation requires a fresh controlled evaluation before final comparative metrics can be reported.

---

## 20. Known Evaluation Limitations

The following limitations remain:

- Small initial evaluation corpus.
- Limited golden-question coverage.
- Provisional evidence relevance labels.
- Incomplete independent answer correctness verification.
- Incomplete validation of LLM judge reliability.
- No controlled aggregate semantic-only versus hybrid benchmark.
- No complete multi-document accuracy benchmark.
- No formal concurrency or load-testing results.
- No independent production scalability measurements.
- Citation IDs are checked, but not all individual claims are independently verified against cited text.
- OCR for scanned PDFs is not implemented.
- Retrieval performance can vary across languages, document formats and question phrasing.

These limitations are documented to prevent overstatement of system capabilities.

---

## 21. Recommended Future Evaluation

Future evaluation should use a fixed multi-document corpus and an expanded golden dataset.

It should compare:

- Semantic-only retrieval
- Hybrid semantic and keyword retrieval

Both configurations should use identical documents, reference answers and evaluation questions.

The comparison should report:

- Hit@5
- Recall@5
- MRR@5
- Answer correctness
- Faithfulness
- Unanswerable-question accuracy
- Retrieval latency
- End-to-end answer latency

A manually audited sample should be used to assess judge reliability.

The system should also be tested with contradictory documents, scanned PDFs, longer files and multilingual questions.

---

## 22. Evaluation Evidence and References

### Application Files

- `app/ingestion/chunker.py`
- `app/ingestion/extractor.py`
- `app/ingestion/service.py`
- `app/ingestion/embeddings.py`
- `app/retrieval/retriever.py`
- `app/vector_store/store.py`
- `app/generation/generator.py`

### Evaluation Files

- `evals/golden_questions.json`
- `evals/run_chunk_experiments.py`
- `evals/run_faithfulness.py`
- `evals/results/chunk_experiments.json`
- `evals/results/chunk_experiments.csv`
- `evals/results/faithfulness_results.json`

### Documentation

- `README.md`
- `DESIGN.md`
- `AI_USAGE.md`
- `DEVELOPMENT_LOG.md`
- `docs/phase2-history/2026-11-24.md`
- `docs/phase2-history/AI_PROMPT_HISTORY.md`
- `docs/phase2-history/TEST_REPORT.md`

### Jupyter Notebooks

- `notebooks/01_ingestion_pipeline.ipynb`
- `notebooks/02_retrieval_generation.ipynb`

---

## 23. Conclusion

The Production RAG Service has been evaluated using retrieval metrics, chunking experiments, automated faithfulness judgments and manual document-question testing.

The historical golden-set evaluation reported:

- **Hit@5: 100.00%**
- **Recall@5: 97.50%**
- **MRR@5: 0.7958**

The preliminary chunking comparison supported retaining the 800-character chunk size and 150-character overlap.

The question-aware LLM judge classified 20 of 20 evaluated answers as faithful, subject to the limitations of automated judging.

During Phase 2, a multi-document retrieval problem was identified after uploading a second PDF. The system sometimes prioritized evidence from a less relevant document, causing failures on questions whose answers existed in the collection.

The problem was investigated through retrieved chunk rankings and addressed through smart chunking, better source context, structured PDF extraction, hybrid reranking and improved generation instructions.

Manual testing demonstrated improvements in previously failing questions.

**The project therefore demonstrates a functioning, measured RAG implementation with documented improvements, while recognizing that the final hybrid system still requires a controlled quantitative benchmark and independent answer-quality validation before production-grade accuracy can be claimed.**
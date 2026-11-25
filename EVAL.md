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

Evaluation covers retrieval quality, answer faithfulness, chunking configurations, multi-document retrieval, failure analysis, and improvements made during development.

The work was completed in two main phases.

**Phase 1 — Initial RAG Implementation**

- PDF and DOCX ingestion
- Text extraction and overlapping chunking
- Multilingual E5 embeddings
- ChromaDB semantic retrieval
- Groq answer generation
- Citations and refusals
- Golden-question retrieval evaluation
- Chunking experiments
- LLM-as-a-Judge faithfulness evaluation

**Phase 2 — Multi-Document Retrieval Improvements**

- Investigation of retrieval failures across two uploaded PDFs
- Paragraph- and sentence-aware smart chunking
- Improved PDF headings and table extraction
- Dynamic source context
- Hybrid semantic and keyword reranking
- Improved grounded generation
- Before-and-after manual tests
- Controlled semantic-only versus hybrid retrieval comparison

The historical evaluation, chunking experiments, and new Phase 2 comparison are reported separately because they represent different experimental conditions.

---

## 2. Evaluation Objectives

The evaluation investigates:

1. Whether relevant evidence appears in the final Top-K results.
2. How accurately the retriever ranks relevant chunks.
3. How chunk size affects retrieval quality.
4. Whether generated answers are supported by retrieved evidence.
5. Whether unsupported questions produce appropriate refusals.
6. Whether retrieval works across multiple uploaded PDFs.
7. Whether hybrid retrieval improves performance compared with semantic-only retrieval.
8. Which limitations remain after Phase 2.

---

## 3. System Configuration

| Component | Configuration |
|---|---|
| Backend | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| PDF extraction | pypdf and pdfplumber |
| DOCX extraction | python-docx |
| Chunk size | 800 characters |
| Chunk overlap | Approximately 150 characters |
| Embedding model | `intfloat/multilingual-e5-small` |
| Embedding dimensions | 384 |
| Document embedding prefix | `passage:` |
| Query embedding prefix | `query:` |
| Vector database | ChromaDB |
| Similarity metric | Cosine |
| Final retrieval depth | Top-K = 5 |
| LLM | Groq `openai/gpt-oss-20b` |
| Faithfulness judge | Question-aware binary LLM judge |
| Judge version | `v2_question_aware` |

### Phase 2 Retrieval Configuration

The updated retrieval system uses semantic candidate search followed by keyword-aware hybrid reranking.

The retriever examines candidate chunks from the indexed collection and selects the final Top-K results based on its combined relevance calculation.

This approach was introduced to address cases where semantic similarity alone prioritized a less relevant document.

### Benchmark-Specific Configuration

The new comparison executed on 25 November 2026 used:

| Setting | Value |
|---|---|
| Top-K | 5 |
| Similarity threshold | 0.0 |
| Indexed PDFs | 2 |
| Indexed chunks | 42 |
| Semantic search | Direct ChromaDB vector retrieval |
| Hybrid search | Phase 2 production retrieval |
| Question set | Existing 25 golden questions |

The benchmark threshold of **0.0** is specific to this experiment and must not be confused with other application configurations.

---

## 4. Evaluation Dataset

The golden dataset is stored in:

`evals/golden_questions.json`

| Question category | Count |
|---|---:|
| Answerable | 20 |
| Unanswerable | 5 |
| Total | 25 |

The original relevance labels identify chunk positions associated with the RAG Project Guide.

### Test Document A — RAG Project Guide

**Filename:** `RAG_Project_Steps_Roman_Urdu.pdf`

- Two-page project guide
- Contains project requirements and implementation instructions
- Used in historical retrieval and chunking evaluation
- Provides the original golden-question relevance labels

### Test Document B — TechNova HR Policy Manual

**Filename:** `TechNova_HR_Policy_Manual.pdf`

- Fourteen-page simulated HR manual
- Contains leave policies, employment conditions, resignation rules, allowances, and structured tables
- Used for multi-document retrieval, calculations, eligibility checks, and manual testing

### Dataset Limitations

The 25-question golden dataset remains relatively small.

Although two PDFs were indexed during the new benchmark, the existing relevance labels refer to the **RAG Project Guide only**.

Consequently, the comparison measures retrieval of the labelled guide evidence in a collection containing two documents. It is not yet a balanced benchmark of labelled questions from both documents.

Furthermore, Phase 2 smart chunking may have changed the relationship between original chunk-position labels and the underlying evidence text. The latest evaluation script verifies that labelled positions exist, but this alone does not prove their semantic relevance.

An independent relevance-label audit remains necessary.

---

## 5. Retrieval Evaluation Metrics

### 5.1 Hit Rate@K

Hit Rate@K measures the proportion of answerable questions for which at least one labelled relevant chunk appears among the first K results.

\[
\text{Hit@K}=\frac{\text{Questions with at least one relevant result in Top-K}}{\text{Answerable questions}}
\]

### 5.2 Recall@K

Recall@K measures the proportion of labelled relevant chunks recovered within the first K results.

\[
\text{Recall@K}=\frac{\text{Relevant chunks retrieved in Top-K}}{\text{Total labelled relevant chunks}}
\]

The reported aggregate is the mean of per-question recall values.

### 5.3 Mean Reciprocal Rank (MRR@K)

MRR@K measures how early the first relevant chunk appears.

\[
\text{MRR@K}=\frac{1}{N}\sum_{i=1}^{N}\frac{1}{\text{rank}_i}
\]

A question receives a reciprocal rank of zero when no relevant result appears within Top-K.

The new evaluator preserves the original ranked positions of all retrieved chunks, including chunks belonging to other documents.

This avoids artificially improving MRR by first removing irrelevant-document results.

### Treatment of Unanswerable Questions

The five unanswerable questions are executed and their retrieval results are recorded.

However, Hit@5, Recall@5, and MRR@5 are averaged over the **20 answerable questions**.

Retrieval metrics alone cannot establish whether the generation system correctly refuses an unsupported question.

---

## 6. Original Golden-Set Retrieval Results

The historical corrected-label retrieval evaluation reported:

| Metric | Historical result |
|---|---:|
| Hit@5 | 100.00% |
| Recall@5 | 97.50% |
| MRR@5 | 0.7958 |

These results were reported before the final Phase 2 hybrid comparison.

They are retained as historical evaluation evidence.

They must not be presented as independently measured hybrid retrieval scores.

The matching semantic-only values observed in the new experiment are reported separately in Section 7.

---

## 7. Phase 2 — Semantic-Only vs Hybrid Retrieval Benchmark

### 7.1 Objective

The purpose of this experiment was to quantitatively compare the Phase 2 hybrid retriever with semantic-only retrieval under the same evaluation conditions.

Both methods were tested using:

- The same ChromaDB document collection
- The same embedding model
- The same 25 golden questions
- The same Top-K value
- The same retrieval threshold
- The same existing relevance labels

This comparison was executed on **25 November 2026**.

### 7.2 Indexed Corpus

The evaluation output confirmed:

| Property | Observed value |
|---|---|
| Indexed documents | 2 PDFs |
| Total indexed chunks | 42 |
| Golden questions | 25 |
| Answerable questions | 20 |
| Unanswerable questions | 5 |
| Top-K | 5 |
| Threshold | 0.0 |

The indexed PDFs were:

1. `RAG_Project_Steps_Roman_Urdu.pdf`
2. `TechNova_HR_Policy_Manual.pdf`

The evaluation log confirmed successful execution of both retrieval strategies.

### 7.3 Compared Retrieval Methods

**Method A — Semantic-Only**

The question is embedded with multilingual E5 and submitted directly to ChromaDB.

Results are ranked using vector similarity without the Phase 2 keyword-based reranking step.

**Method B — Hybrid**

The question is processed through the Phase 2 retrieval implementation.

Semantic candidates are retrieved and reranked using additional keyword relevance.

The final Top-K chunks are then evaluated against the same golden labels.

### 7.4 Actual Quantitative Results

| Metric | Semantic-only | Hybrid | Difference |
|---|---:|---:|---:|
| Hit@5 | 100.00% | 100.00% | 0.00 percentage points |
| Recall@5 | 97.50% | 100.00% | +2.50 percentage points |
| MRR@5 | 0.7958 | 0.8750 | +0.0792 |

**Measured result:** Hybrid retrieval achieved higher aggregate Recall@5 and MRR@5 on this evaluation set.

Hit@5 remained unchanged because both methods retrieved at least one labelled relevant chunk for every answerable question.

### 7.5 Interpretation

**Hit@5**

Both approaches achieved 100% Hit@5. Hybrid retrieval did not improve this metric because semantic-only retrieval already reached the maximum possible score on the current question set.

**Recall@5**

Semantic-only retrieval recovered 97.50% of labelled relevant evidence on average.

Hybrid retrieval recovered 100.00%.

This corresponds to a **2.50 percentage-point increase** in aggregate Recall@5.

**MRR@5**

Semantic-only retrieval achieved MRR@5 of 0.7958.

Hybrid retrieval achieved MRR@5 of 0.8750.

The increase of **0.0792** indicates that the first labelled relevant chunk generally appeared higher in the hybrid ranking.

The relative MRR increase is approximately 9.95%, based on the reported rounded scores.

### 7.6 Question-Level Findings

The improvement was not uniform across every question.

Examples of improved reciprocal ranking included:

| Question | Semantic-only RR | Hybrid RR |
|---|---:|---:|
| Q002 | 0.3333 | 1.0000 |
| Q003 | 0.2500 | 1.0000 |
| Q004 | 0.5000 | 1.0000 |
| Q005 | 0.5000 | 1.0000 |
| Q015 | 0.5000 | 1.0000 |
| Q019 | 0.5000 | 1.0000 |

Some questions experienced lower reciprocal ranking under hybrid retrieval:

| Question | Semantic-only RR | Hybrid RR |
|---|---:|---:|
| Q007 | 1.0000 | 0.5000 |
| Q008 | 1.0000 | 0.5000 |
| Q013 | 1.0000 | 0.5000 |
| Q020 | 1.0000 | 0.5000 |

This shows that hybrid reranking improved the aggregate score while occasionally moving relevant evidence down the result list.

Future tuning should investigate these ranking regressions.

### 7.7 Important Evaluation Limitation

The script produced valid numerical output, but its golden labels have not yet been manually revalidated against the final smart-chunked source text.

The evaluator checks whether expected chunk positions exist. It does not establish that those positions still correspond to the originally intended evidence.

Therefore, these scores are **measured results using the current position-based labels**, not independently validated evidence-relevance measurements.

Additionally, the golden questions primarily evaluate the project guide, even though the corpus contains a second HR document.

The experiment supports a limited comparison of the two retrieval methods but does not demonstrate comprehensive multi-document answer accuracy.

### 7.8 Evaluation Evidence

**Script:**

`evals/run_evals.py`

**Generated results:**

- `evals/results/retrieval_comparison.json`
- `evals/results/retrieval_comparison.csv`

**Command:**

```powershell
python evals/run_evals.py
```

**Additional configuration options:**

```powershell
python evals/run_evals.py --top-k 5 --threshold 0.0
```

The new result files are separate from historical retrieval results and do not overwrite the original evaluation evidence.

---

## 8. Chunking Configuration Experiments

### Objective

Three chunking configurations were compared on the same small source document using 20 answerable questions.

**Document:** `RAG_Project_Steps_Roman_Urdu.pdf`
**Embedding model:** `intfloat/multilingual-e5-small`
**Vector database:** Temporary ChromaDB collections
**Relevance labels:** Provisional evidence-phrase matching

### Compared Configurations

| Configuration | Chunk size | Overlap | Generated chunks |
|---|---:|---:|---:|
| A | 256 | 50 | 21 |
| B | 512 | 80 | 11 |
| C | 800 | 150 | 7 |

### Top-5 Results

| Configuration | Hit@5 | Recall@5 | MRR@5 |
|---|---:|---:|---:|
| A — 256/50 | 85.00% | 64.58% | 0.7225 |
| B — 512/80 | 100.00% | 86.25% | 0.7283 |
| C — 800/150 | 100.00% | 95.00% | 0.8583 |

### Top-3 Results

| Configuration | Hit@3 | Recall@3 | MRR@3 |
|---|---:|---:|---:|
| A — 256/50 | 75.00% | 57.08% | 0.7000 |
| B — 512/80 | 80.00% | 65.00% | 0.6833 |
| C — 800/150 | 100.00% | 92.50% | 0.8583 |

### Decision

Configuration C performed best in this preliminary experiment.

The project therefore retained:

- Chunk size: **800 characters**
- Chunk overlap: **150 characters**

The Phase 2 implementation subsequently improved chunk boundaries by considering paragraphs and sentences.

### Trade-offs

Smaller chunks can improve evidence precision but may fragment relevant context.

Larger chunks can preserve context but may contain unrelated material.

The experiment used only one small two-page document, so these findings should not be generalized to all document collections.

### Evidence

- `evals/run_chunk_experiments.py`
- `evals/results/chunk_experiments.json`
- `evals/results/chunk_experiments.csv`

---

## 9. Answer Faithfulness Evaluation

### Objective

Faithfulness evaluation checks whether generated answers are supported by their retrieved evidence.

The project uses a question-aware LLM-as-a-Judge implementation.

### Methodology

For each answerable question, the evaluator:

1. Retrieves supporting document chunks.
2. Generates an answer.
3. Submits the question, answer, and evidence to the judge.
4. Requests a structured JSON judgment.
5. Records whether the answer is faithful.
6. Saves the result and judge explanation.

The judge is instructed to reject answers that contradict the retrieved source or introduce unsupported factual claims.

### Judge Configuration

| Property | Value |
|---|---|
| Judge type | Binary LLM-as-a-Judge |
| Version | `v2_question_aware` |
| Provider | Groq |
| Model | `openai/gpt-oss-20b` |
| Output format | JSON |
| Judgment | `faithful: true/false` |
| Explanation field | `reason` |

### Previously Reported Results

| Metric | Result |
|---|---:|
| Answerable questions | 20 |
| Completed evaluations | 20 |
| Judged answers | 20 |
| Faithful answers | 20 |
| Refused answers | 0 |
| LLM-judged faithfulness | 100.00% |
| Mixed judge versions | False |

### Interpretation and Limitations

All 20 evaluated answers were classified as faithful by the automated judge.

This is a judge classification result, not an independent guarantee of factual correctness.

The judge was not fully calibrated against a human-annotated reference dataset.

The same model family was used for generation and judging, which introduces potential correlated errors.

Answer correctness against every reference answer was not independently measured.

### Commands

Run the evaluation:

```powershell
python evals/run_faithfulness.py
```

Rejudge a selected question:

```powershell
python evals/run_faithfulness.py --rejudge Q016
```

### Evidence

- `evals/golden_questions.json`
- `evals/run_faithfulness.py`
- `evals/results/faithfulness_results.json`

Checkpoint files may also exist locally. Their inclusion in Git must be verified before using them as submitted evidence.

---

## 10. Phase 2 — Multi-Document Retrieval Problem

### Initial Behavior

The RAG application initially answered questions about the uploaded document correctly.

After uploading another PDF, certain questions associated with the second document failed even though the information existed in the indexed collection.

### Diagnosis

Inspection of retrieval results showed that relevant evidence was sometimes absent from the final Top-K results.

The retriever occasionally preferred semantically similar content from another document.

When the answer evidence was absent from the final context, the generation model could incorrectly refuse the question.

### Root Cause

The principal observed issue was **retrieval ranking across multiple indexed documents**.

The second upload had not simply failed. The content existed in the collection, but it was not always prioritized appropriately.

### Example Failures

**Promotion eligibility:** A policy required 18 months in the current grade. A question involving 15 months of service initially failed to retrieve the necessary evidence consistently.

**Probation resignation:** The correct seven-day written notice policy was initially missing from the final retrieval context.

**International hotel limit:** The system confused an international per diem amount with a hotel limit, exposing a structured-table interpretation and grounding problem.

---

## 11. Phase 2 — Improvements Implemented

### 11.1 Smart Chunking

**File:** `app/ingestion/chunker.py`

The chunking algorithm was improved to consider paragraph and sentence boundaries.

The purpose was to preserve related policy statements and reduce fragmentation of eligibility conditions.

### 11.2 Dynamic Source Context

**File:** `app/ingestion/service.py`

The ingestion pipeline adds contextual information derived from the source document, including:

- Filename
- Page
- Section, when detected

The context is generated dynamically rather than being hardcoded for a specific PDF.

### 11.3 Improved PDF Extraction

**File:** `app/ingestion/extractor.py`

Improvements include:

- Numbered-section detection
- PDF table extraction
- Better page-level information
- Handling unreadable or scanned documents

During TechNova manual testing, extraction returned 20 sections and identified six structured tables.

### 11.4 Hybrid Retrieval and Reranking

**File:** `app/vector_store/store.py`

The retrieval pipeline:

1. Generates a query embedding.
2. Retrieves semantic candidates from ChromaDB.
3. Calculates keyword relevance.
4. Reranks candidates using semantic and keyword signals.
5. Returns the final Top-K evidence chunks.

The 25 November benchmark provides quantitative evidence of improved aggregate Recall@5 and MRR@5 under the stated evaluation conditions.

### 11.5 Grounded Generation

**File:** `app/generation/generator.py`

Generation instructions were improved for:

- Eligibility conditions
- Conditional reasoning
- Table interpretation
- Numeric calculations
- Currency and unit distinctions
- False premises
- Refusal when evidence is absent

These changes help reduce unsupported answers when relevant evidence is retrieved.

---

## 12. Updated Phase 2 Retrieval Flow

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
Final Top-K Evidence
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

This architecture improves evidence selection, but it does not guarantee perfect retrieval, reasoning, or citation correctness.

---

## 13. Phase 2 — Before-and-After Manual Testing

| Test case | Before improvements | After improvements |
|---|---|---|
| Promotion with 15 months in grade | Incorrect refusal | Correctly identifies unmet 18-month requirement |
| Resignation during probation | Incorrect refusal | Correctly identifies seven days' written notice |
| International hotel limit | Confused per diem with hotel limit | Correctly states the limit is unspecified |

These are manually observed examples.

They complement the quantitative retrieval comparison but do not replace a comprehensive question-answer accuracy benchmark.

---

## 14. Additional TechNova HR Manual Testing

| Question area | Observed answer |
|---|---|
| Annual leave | 20 working days |
| Maternity eligibility | Minimum six months of service |
| Maternity application | At least four weeks before expected delivery |
| G4 hospitalization limit | PKR 1,000,000 |
| G4 domestic hotel limit | PKR 30,000 |
| Rating 4 bonus on PKR 150,000 basic salary | PKR 300,000, subject to eligibility |
| One Eid bonus on PKR 150,000 basic salary | PKR 150,000 |
| Employee provident fund contribution at 8% | PKR 12,000 |
| G4 resignation notice | 60 days |

These tests demonstrate observed retrieval of policy facts, calculations, and table values.

Not every generated answer and citation has been independently audited.

---

## 15. Second PDF — Project Guide Testing

Manual questions included:

- Golden-question distribution
- Project ingestion requirements
- Retrieval methods and metrics
- API requirements
- Numbered project steps

The guide ended at Step 12.

When asked about Step 13, the service correctly refused because the requested step was not present.

This demonstrated appropriate behavior for the tested unsupported question.

The requirements described inside the uploaded project guide must not be confused with the application's actual implementation choices.

---

## 16. Frontend Retrieval Verification

### Question

How many annual leave days are allowed?

### Observed Answer

**20 working days**

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

The browser interface displayed:

- Generated answer
- Source citations
- Five retrieved chunks
- Source text
- Filename and page metadata
- Individual similarity scores

This verifies the required frontend display functionality for the observed test case.

Some retrieved chunks were less directly relevant, indicating remaining opportunities to improve retrieval precision.

---

## 17. Evaluation Framework Selection

### Chosen Approach

Custom Python evaluation scripts were selected because they integrate directly with the application.

They support:

- Controlled retrieval comparisons
- Per-question diagnostics
- JSON and CSV evidence
- Faithfulness judgments
- Checkpoints and resume functionality
- Explicit experimental configuration

### Alternative — RAGAS

RAGAS provides standardized RAG quality metrics.

It was considered a possible additional framework but is not claimed to have produced the reported results.

### Alternative — Langfuse

Langfuse offers tracing and observability for model calls, retrieval, latency, and costs.

It is not claimed as an implemented component.

### Trade-offs

The custom approach offers flexibility and direct control over metrics.

However, its labels, experimental setup, and judge reliability require independent validation.

---

## 18. Testing Evidence

The latest previously reported pytest regression result was:

**35 tests passed.**

Run:

```powershell
python -m pytest -q
```

### Jupyter Notebook 1

`notebooks/01_ingestion_pipeline.ipynb`

Covers extraction, chunking, metadata, and embeddings.

Previously observed:

- Three document embeddings
- 384-dimensional document vectors
- 384-dimensional query embedding
- `NOTEBOOK 1: PASSED`

### Jupyter Notebook 2

`notebooks/02_retrieval_generation.ipynb`

Covers indexing, retrieval, generation, citations, and refusal.

Previously reported:

- Seven code cells
- Seven executed cells
- Zero saved cell errors

A Windows-specific ChromaDB temporary-file cleanup issue was addressed by deferring deletion while database files were open.

**Notebook development commit:** `523c30a`

Successful notebook execution does not independently establish overall answer correctness.

---

## 19. Error Analysis

### Failure 1 — Missing Relevant Evidence

**Problem:** Existing HR policy questions sometimes received refusals.

**Cause:** Relevant evidence ranked outside the final context.

**Improvement:** Broader semantic candidates and keyword-aware hybrid reranking.

### Failure 2 — Table Value Confusion

**Problem:** International per diem was mistaken for a hotel limit.

**Cause:** Incorrect interpretation of related table values.

**Improvement:** Better structured extraction and grounded generation instructions.

### Failure 3 — Irrelevant Retrieved Chunks

**Problem:** Some returned chunks were only indirectly relevant.

**Cause:** Approximate ranking and incomplete relevance discrimination.

**Remaining work:** Better ranking calibration and precision evaluation.

### Failure 4 — Ranking Regressions

**Problem:** Hybrid retrieval ranked the first relevant result lower for Q007, Q008, Q013, and Q020.

**Evidence:** Question-level reciprocal ranks from the latest comparison.

**Remaining work:** Investigate keyword-weight effects and improve reranking.

### Failure 5 — Golden Label Validity

**Problem:** Position-based relevance labels may no longer correspond perfectly to evidence after smart chunking.

**Remaining work:** Inspect source text for each labelled chunk and update the golden dataset where required.

---

## 20. Reproducibility

### Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Run Automated Tests

```powershell
python -m pytest -q
```

### Run Semantic vs Hybrid Retrieval Evaluation

```powershell
python evals/run_evals.py
```

### Run Chunking Experiments

```powershell
python evals/run_chunk_experiments.py
```

### Run Faithfulness Evaluation

```powershell
python evals/run_faithfulness.py
```

### Rejudge One Question

```powershell
python evals/run_faithfulness.py --rejudge Q016
```

### Reproducibility Conditions

For meaningful comparisons:

1. Use the intended PDF documents.
2. Use the same embedding model.
3. Keep the indexed corpus unchanged between retrieval methods.
4. Use the same question set.
5. Use the same Top-K and threshold.
6. Validate golden relevance labels against the indexed chunks.
7. Record retrieval configuration and evaluation output.
8. Avoid mixing checkpoints from incompatible experiments.

### Automation Status

The retrieval comparison now has a working command:

`python evals/run_evals.py`

Separate scripts remain necessary for chunking experiments and LLM faithfulness evaluation.

A single independently verified command executing every evaluation category has not yet been demonstrated.

---

## 21. Known Evaluation Limitations

The project has quantitative retrieval results and manually observed functional improvements.

However, limitations remain:

- Only 25 original golden questions.
- Original relevance labels belong to one source document.
- Chunk-position labels require a post-chunking audit.
- No balanced labelled evaluation across both PDFs.
- No independently verified reference-answer correctness score.
- Incomplete calibration of the LLM faithfulness judge.
- No aggregate generation/refusal accuracy for all unanswerable questions.
- No formal retrieval latency distribution.
- No end-to-end p50/p95 latency benchmark.
- No formal concurrency or load-testing results.
- No independent production scalability measurements.
- Not every citation claim has been checked against its evidence text.
- No OCR support for scanned PDFs.
- Retrieval accuracy may vary across languages, layouts, and question styles.

The new comparison is useful measured evidence, but its methodological limitations must remain visible.

---

## 22. Recommended Future Evaluation

Future work should expand the benchmark to include labelled questions for both the RAG Project Guide and the TechNova HR Manual.

The expanded evaluation should compare semantic-only and hybrid retrieval on identical questions and documents.

Metrics should include:

- Hit@5
- Recall@5
- MRR@5
- Precision@5
- Answer correctness
- Answer faithfulness
- Unanswerable-question refusal accuracy
- Retrieval latency
- End-to-end generation latency

The evaluation should also include manually audited relevance labels and judge calibration.

Additional test cases should cover contradictory documents, scanned PDFs, larger files, multilingual questions, and prompt injection.

---

## 23. Evaluation Evidence and References

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
- `evals/run_evals.py`
- `evals/run_chunk_experiments.py`
- `evals/run_faithfulness.py`
- `evals/results/retrieval_comparison.json`
- `evals/results/retrieval_comparison.csv`
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

## 24. Conclusion

The Production RAG Service has been evaluated using golden-question retrieval metrics, chunking comparisons, automated faithfulness judgments, manual document testing, and a controlled semantic-only versus hybrid retrieval experiment.

The historical retrieval evaluation reported:

- Hit@5: **100.00%**
- Recall@5: **97.50%**
- MRR@5: **0.7958**

The preliminary chunking experiment supported an 800-character chunk size with 150-character overlap.

The question-aware automated judge classified 20 of 20 evaluated answers as faithful, subject to the limitations of LLM-based judging.

Phase 2 investigated and improved a multi-document retrieval problem through smart chunking, better source metadata, PDF table extraction, hybrid reranking, and stronger grounding instructions.

The **25 November 2026 retrieval comparison** produced:

| Metric | Semantic-only | Hybrid |
|---|---:|---:|
| Hit@5 | 100.00% | 100.00% |
| Recall@5 | 97.50% | 100.00% |
| MRR@5 | 0.7958 | 0.8750 |

These results show improved aggregate recall and ranking under the tested conditions.

However, the existing golden questions primarily evaluate one document, and the chunk-position relevance labels require independent verification after Phase 2 chunking changes.

**Overall conclusion:** The project demonstrates a functioning, tested RAG pipeline with measurable retrieval improvements. Broader multi-document evaluation and independently validated answer quality remain necessary before production-grade accuracy can be claimed.
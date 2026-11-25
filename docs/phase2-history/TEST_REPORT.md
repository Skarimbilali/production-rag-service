# Phase 2 - Live Testing Report

Date: 24 November 2026
Branch: development

## Test Documents

1. TechNova HR Policy Manual - 14 pages
2. RAG Project Step-by-Step Guide - 2 pages

## TechNova Manual

| Test | Result |
|---|---|
| Promotion: 15 months, rating 5 | PASS after retrieval improvement |
| Probation resignation notice | PASS after retrieval improvement |
| International hotel limit unspecified | PASS after prompt/retrieval improvement |
| Annual leave 20 working days | PASS |
| Maternity minimum service and application | PASS |
| G4 hospitalization and domestic hotel | PASS |
| Performance bonus, Eid bonus and PF | PASS |
| G4 notice and final settlement | PASS |

## Second PDF

| Test | Result |
|---|---|
| Golden question-set distribution | Answer returned; source audit pending |
| Ingestion configuration | Answer returned; source audit pending |
| Retrieval methods and metrics | Answer returned; source audit pending |
| API tests and latency target | Answer returned; source audit pending |
| Nonexistent Step 13 | Correct refusal |

## Automated Regression

Latest reported result:
35 passed in 27.68 seconds.

## Limitations

- These results are specific to the tested PDFs.
- Citation correctness has not been independently
  verified for every answer.
- Wider benchmark of hybrid versus baseline is pending.
- OCR for scanned PDFs is not implemented.
- A correct answer does not prove every retrieval
  result was relevant.
- No overall accuracy percentage is claimed
  for arbitrary PDFs.

## Conclusion

Phase 2 produced improvements in multi-document
retrieval and document-grounded answering.
Further evaluation is necessary before production use.


"""
Evaluate retrieval quality using the golden question dataset.

Metrics:
    Hit@K
    Recall@K
    MRR@K

Results:
    evals/results/retrieval_results.json
    evals/results/retrieval_results.csv

Run:
    python evals/run_evals.py
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow direct execution from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.retrieval.retriever import RetrievalService
from app.vector_store.store import VectorStoreService


EVAL_DIR = PROJECT_ROOT / "evals"
GOLDEN_FILE = EVAL_DIR / "golden_questions.json"
RESULTS_DIR = EVAL_DIR / "results"

TOP_K = 5
THRESHOLD = 0.0

# Golden labels belong to this uploaded document.
EXPECTED_FILENAME = "RAG_Project_Steps_Roman_Urdu.pdf"


def load_golden_questions():
    """Read and validate the golden dataset."""

    with GOLDEN_FILE.open("r", encoding="utf-8") as file:
        questions = json.load(file)

    if not isinstance(questions, list) or not questions:
        raise ValueError("Golden question dataset is empty.")

    required_fields = {
        "id",
        "question",
        "answerable",
        "relevant_chunk_positions",
    }

    for item in questions:
        if not isinstance(item, dict):
            raise ValueError("Each question must be an object.")

        missing = required_fields - item.keys()

        if missing:
            raise ValueError(
                f"Question is missing fields: {sorted(missing)}"
            )

        if not isinstance(item["answerable"], bool):
            raise ValueError(
                f"{item['id']}: answerable must be boolean."
            )

        relevant = item["relevant_chunk_positions"]

        if not isinstance(relevant, list):
            raise ValueError(
                f"{item['id']}: relevant chunks must be a list."
            )

        if item["answerable"] and not relevant:
            raise ValueError(
                f"{item['id']}: missing relevant chunk labels."
            )

        if not item["answerable"] and relevant:
            raise ValueError(
                f"{item['id']}: unanswerable question has labels."
            )

    return questions


def get_retrieved_positions(chunks):
    """
    Return chunk positions from the expected source document.

    Using filename prevents matching the same position
    from a different uploaded document.
    """

    positions = []

    for chunk in chunks:
        metadata = chunk.get("metadata") or {}

        if metadata.get("filename") != EXPECTED_FILENAME:
            continue

        position = metadata.get("chunk_position")

        if position is not None:
            positions.append(int(position))

    return positions


def calculate_metrics(expected_positions, retrieved_positions):
    """Calculate Hit@K, Recall@K and reciprocal rank."""

    expected = set(expected_positions)

    hit = 0
    recall = 0.0
    reciprocal_rank = 0.0

    if not expected:
        return hit, recall, reciprocal_rank

    for rank, position in enumerate(
        retrieved_positions,
        start=1
    ):
        if position in expected:
            hit = 1
            reciprocal_rank = 1.0 / rank
            break

    retrieved_relevant = expected.intersection(
        retrieved_positions
    )

    recall = len(retrieved_relevant) / len(expected)

    return hit, recall, reciprocal_rank


def evaluate():
    """Run retrieval and calculate real evaluation metrics."""

    questions = load_golden_questions()

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vector_store = VectorStoreService()
    retriever = RetrievalService(vector_store)

    if vector_store.count_chunks() == 0:
        raise RuntimeError(
            "Vector database is empty. Upload the PDF first."
        )

    results = []

    print("=" * 60)
    print("PRODUCTION RAG SERVICE - RETRIEVAL EVALUATION")
    print("=" * 60)

    for item in questions:
        question_id = item["id"]
        question = item["question"]
        answerable = item["answerable"]

        retrieved_chunks = retriever.retrieve(
            question=question,
            top_k=TOP_K,
            threshold=THRESHOLD
        )

        retrieved_positions = get_retrieved_positions(
            retrieved_chunks
        )

        expected_positions = item[
            "relevant_chunk_positions"
        ]

        if answerable:
            hit, recall, reciprocal_rank = calculate_metrics(
                expected_positions,
                retrieved_positions
            )
        else:
            # Retrieval metrics do not apply to unanswerable
            # questions with no relevant source labels.
            hit = None
            recall = None
            reciprocal_rank = None

        result = {
            "id": question_id,
            "question": question,
            "answerable": answerable,
            "expected_positions": expected_positions,
            "retrieved_positions": retrieved_positions,
            "retrieved_count": len(retrieved_chunks),
            "hit_at_k": hit,
            "recall_at_k": recall,
            "reciprocal_rank": reciprocal_rank,
        }

        results.append(result)

        if answerable:
            print(
                f"{question_id} | "
                f"Hit={hit} | "
                f"Recall={recall:.2f} | "
                f"RR={reciprocal_rank:.2f}"
            )
        else:
            print(
                f"{question_id} | "
                "Unanswerable - retrieval recorded"
            )

    answerable_results = [
        result
        for result in results
        if result["answerable"]
    ]

    total_answerable = len(answerable_results)

    if total_answerable == 0:
        raise ValueError("No answerable questions found.")

    hit_rate = sum(
        result["hit_at_k"]
        for result in answerable_results
    ) / total_answerable

    recall_at_k = sum(
        result["recall_at_k"]
        for result in answerable_results
    ) / total_answerable

    mrr_at_k = sum(
        result["reciprocal_rank"]
        for result in answerable_results
    ) / total_answerable

    summary = {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "configuration": {
            "top_k": TOP_K,
            "threshold": THRESHOLD,
            "expected_filename": EXPECTED_FILENAME,
        },
        "total_questions": len(questions),
        "answerable_questions": total_answerable,
        "unanswerable_questions": (
            len(questions) - total_answerable
        ),
        "hit_at_k": round(hit_rate, 4),
        "recall_at_k": round(recall_at_k, 4),
        "mrr_at_k": round(mrr_at_k, 4),
    }

    json_path = RESULTS_DIR / "retrieval_results.json"
    csv_path = RESULTS_DIR / "retrieval_results.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "summary": summary,
                "questions": results,
            },
            file,
            ensure_ascii=False,
            indent=2
        )

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Questions: {len(questions)}")
    print(f"Answerable: {total_answerable}")
    print(
        f"Unanswerable: "
        f"{len(questions) - total_answerable}"
    )
    print(f"Hit@{TOP_K}: {hit_rate:.4f}")
    print(f"Recall@{TOP_K}: {recall_at_k:.4f}")
    print(f"MRR@{TOP_K}: {mrr_at_k:.4f}")

    print("\nResults saved:")
    print(json_path)
    print(csv_path)


if __name__ == "__main__":
    evaluate()


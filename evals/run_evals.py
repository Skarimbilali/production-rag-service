
"""
Production RAG Service - Retrieval Evaluation

Compare semantic-only retrieval with Phase 2 hybrid
retrieval on the SAME indexed document collection.

Metrics:
    Hit@K
    Recall@K
    MRR@K

Outputs:
    evals/results/retrieval_comparison.json
    evals/results/retrieval_comparison.csv

Usage:
    python evals/run_evals.py
    python evals/run_evals.py --top-k 5
    python evals/run_evals.py --db-path data/chroma_db

Notes:
    - Existing historical results are NOT overwritten.
    - Golden labels must match the currently indexed chunks.
    - Unanswerable questions are recorded separately.
    - No LLM is called during retrieval evaluation.
"""

import argparse
import csv
import json
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.embeddings import EmbeddingService
from app.vector_store.store import VectorStoreService


EVAL_DIR = PROJECT_ROOT / "evals"

GOLDEN_FILE = EVAL_DIR / "golden_questions.json"

RESULTS_DIR = EVAL_DIR / "results"

EXPECTED_FILENAME = "RAG_Project_Steps_Roman_Urdu.pdf"

DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.0
DEFAULT_DB_PATH = "data/chroma_db"


def load_golden_questions() -> list[dict[str, Any]]:
    """Load and validate the existing 25-question dataset."""

    with GOLDEN_FILE.open("r", encoding="utf-8") as file:
        questions = json.load(file)

    if not isinstance(questions, list) or not questions:
        raise ValueError("Golden question dataset is empty.")

    required = {
        "id",
        "question",
        "answerable",
        "relevant_chunk_positions",
    }

    seen_ids = set()

    for item in questions:
        if not isinstance(item, dict):
            raise ValueError("Invalid golden question record.")

        missing = required - set(item)

        if missing:
            raise ValueError(
                f"Missing fields: {sorted(missing)}"
            )

        question_id = item["id"]

        if question_id in seen_ids:
            raise ValueError(
                f"Duplicate question ID: {question_id}"
            )

        seen_ids.add(question_id)

        if not isinstance(item["question"], str):
            raise ValueError(
                f"{question_id}: question must be text."
            )

        if not isinstance(item["answerable"], bool):
            raise ValueError(
                f"{question_id}: answerable must be boolean."
            )

        positions = item["relevant_chunk_positions"]

        if not isinstance(positions, list):
            raise ValueError(
                f"{question_id}: invalid relevance labels."
            )

        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for value in positions
        ):
            raise ValueError(
                f"{question_id}: invalid chunk positions."
            )

        if item["answerable"] and not positions:
            raise ValueError(
                f"{question_id}: answerable question "
                "requires relevance labels."
            )

        if not item["answerable"] and positions:
            raise ValueError(
                f"{question_id}: unanswerable question "
                "must not contain relevance labels."
            )

    return questions


def load_index_information(
    store: VectorStoreService,
) -> dict[str, Any]:
    """Inspect indexed document metadata."""

    metadata_result = store.collection.get(
        include=["metadatas"]
    )

    document_names = set()
    expected_positions = set()
    expected_document_ids = set()

    for metadata in metadata_result["metadatas"]:
        metadata = metadata or {}

        filename = metadata.get("filename")

        if filename:
            document_names.add(str(filename))

        if filename != EXPECTED_FILENAME:
            continue

        position = metadata.get("chunk_position")

        if position is not None:
            expected_positions.add(int(position))

        document_id = metadata.get("document_id")

        if document_id:
            expected_document_ids.add(str(document_id))

    return {
        "indexed_document_names": sorted(document_names),
        "indexed_document_count": len(document_names),
        "expected_positions": expected_positions,
        "expected_document_ids": expected_document_ids,
    }


def validate_golden_labels(
    questions: list[dict[str, Any]],
    index_info: dict[str, Any],
) -> None:
    """
    Ensure every labelled position exists in the
    currently indexed expected document.

    Position existence does NOT prove that the text is
    still semantically relevant after rechunking.
    """

    indexed_positions = index_info["expected_positions"]

    if not indexed_positions:
        raise RuntimeError(
            f"Expected PDF is not indexed: "
            f"{EXPECTED_FILENAME}"
        )

    if len(index_info["expected_document_ids"]) > 1:
        raise RuntimeError(
            "Multiple indexed document IDs share the "
            "expected filename. Resolve duplicates before "
            "using chunk-position relevance labels."
        )

    missing_positions = set()

    for question in questions:
        for position in question[
            "relevant_chunk_positions"
        ]:
            if position not in indexed_positions:
                missing_positions.add(position)

    if missing_positions:
        raise RuntimeError(
            "Golden labels do not match the indexed corpus. "
            f"Missing positions: {sorted(missing_positions)}. "
            "Re-audit the dataset after chunking changes."
        )


def semantic_search(
    store: VectorStoreService,
    question: str,
    top_k: int,
    threshold: float,
) -> list[dict[str, Any]]:
    """
    Search ChromaDB directly without hybrid reranking.

    Uses the existing multilingual E5 query embedding,
    collection and cosine distance metric.
    """

    total = store.collection.count()

    if total == 0:
        return []

    query_vector = EmbeddingService.embed_query(question)

    result = store.collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, total),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    retrieved = []

    for chunk_id, text, metadata, distance in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        similarity = 1.0 - float(distance)

        if similarity < threshold:
            continue

        retrieved.append({
            "id": chunk_id,
            "text": text,
            "metadata": metadata or {},
            "similarity_score": similarity,
        })

    return retrieved


def hybrid_search(
    store: VectorStoreService,
    question: str,
    top_k: int,
    threshold: float,
) -> list[dict[str, Any]]:
    """
    Use the actual Phase 2 production hybrid retrieval.

    Do not duplicate or approximate reranking logic.
    """

    chunks = store.search_chunks(
        question=question,
        top_k=top_k,
    )

    return [
        chunk
        for chunk in chunks
        if float(chunk["similarity_score"]) >= threshold
    ]


def retrieved_keys(
    chunks: list[dict[str, Any]],
) -> list[tuple[str, int | None]]:
    """
    Preserve the ORIGINAL ranking, including chunks
    retrieved from unrelated uploaded documents.

    Do not filter first: doing that would incorrectly
    improve MRR when other PDFs occupy higher ranks.
    """

    keys = []

    for chunk in chunks:
        metadata = chunk.get("metadata") or {}

        filename = str(
            metadata.get("filename", "")
        )

        position = metadata.get("chunk_position")

        if position is not None:
            position = int(position)

        keys.append((filename, position))

    return keys


def calculate_metrics(
    expected_positions: list[int],
    chunks: list[dict[str, Any]],
) -> dict[str, float]:
    """Calculate retrieval metrics for one question."""

    expected = {
        (EXPECTED_FILENAME, int(position))
        for position in expected_positions
    }

    if not expected:
        return {
            "hit_at_k": 0.0,
            "recall_at_k": 0.0,
            "reciprocal_rank": 0.0,
        }

    ranked_keys = retrieved_keys(chunks)

    relevant_found = expected.intersection(
        ranked_keys
    )

    reciprocal_rank = 0.0

    for rank, key in enumerate(ranked_keys, start=1):
        if key in expected:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "hit_at_k": float(bool(relevant_found)),
        "recall_at_k": (
            len(relevant_found) / len(expected)
        ),
        "reciprocal_rank": reciprocal_rank,
    }


def summarize(
    rows: list[dict[str, Any]],
    method: str,
) -> dict[str, float]:
    """Calculate macro averages over answerable questions."""

    answerable_rows = [
        row
        for row in rows
        if row["answerable"] is True
        and row["method"] == method
    ]

    if not answerable_rows:
        raise ValueError(
            f"No answerable results for {method}"
        )

    count = len(answerable_rows)

    return {
        "hit_at_k": round(
            sum(row["hit_at_k"] for row in answerable_rows)
            / count,
            4,
        ),
        "recall_at_k": round(
            sum(row["recall_at_k"] for row in answerable_rows)
            / count,
            4,
        ),
        "mrr_at_k": round(
            sum(
                row["reciprocal_rank"]
                for row in answerable_rows
            ) / count,
            4,
        ),
    }


def save_results(
    output: dict[str, Any],
    rows: list[dict[str, Any]],
) -> None:
    """Save separate comparison results, preserving old runs."""

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        RESULTS_DIR / "retrieval_comparison.json"
    )

    csv_path = (
        RESULTS_DIR / "retrieval_comparison.csv"
    )

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    csv_fields = [
        "id",
        "method",
        "question",
        "answerable",
        "expected_positions",
        "retrieved_sources",
        "retrieved_positions",
        "retrieved_count",
        "hit_at_k",
        "recall_at_k",
        "reciprocal_rank",
    ]

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=csv_fields,
        )

        writer.writeheader()

        for row in rows:
            csv_row = dict(row)

            for field in [
                "expected_positions",
                "retrieved_sources",
                "retrieved_positions",
            ]:
                csv_row[field] = json.dumps(
                    csv_row[field],
                    ensure_ascii=False,
                )

            writer.writerow(csv_row)

    print("\nResults saved:")
    print(json_path)
    print(csv_path)


def evaluate(
    db_path: str = DEFAULT_DB_PATH,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = DEFAULT_THRESHOLD,
) -> None:
    """Run a controlled semantic-versus-hybrid comparison."""

    questions = load_golden_questions()

    store = VectorStoreService(db_path=db_path)

    if store.count_chunks() == 0:
        raise RuntimeError(
            "Vector database is empty. "
            "Upload the evaluation document first."
        )

    index_info = load_index_information(store)

    validate_golden_labels(
        questions,
        index_info,
    )

    print("=" * 65)
    print("SEMANTIC VS HYBRID RETRIEVAL EVALUATION")
    print("=" * 65)

    print("Indexed document filenames:")
    for filename in index_info[
        "indexed_document_names"
    ]:
        print(" -", filename)

    print("Total chunks:", store.count_chunks())
    print("Questions:", len(questions))
    print("Top-K:", top_k)
    print("Threshold:", threshold)

    if index_info["indexed_document_count"] < 2:
        print(
            "WARNING: Only one distinct document filename "
            "is indexed. This is not a multi-document test."
        )

    print(
        "WARNING: Position labels must be manually "
        "rechecked after smart chunking changes."
    )

    rows = []
    methods = {
        "semantic_only": semantic_search,
        "hybrid": hybrid_search,
    }

    for item in questions:
        question_id = item["id"]
        question = item["question"]
        answerable = item["answerable"]

        for method_name, search_function in methods.items():
            chunks = search_function(
                store=store,
                question=question,
                top_k=top_k,
                threshold=threshold,
            )

            if answerable:
                metrics = calculate_metrics(
                    item["relevant_chunk_positions"],
                    chunks,
                )
            else:
                # Retrieval alone cannot verify that the
                # generator will correctly refuse.
                metrics = {
                    "hit_at_k": None,
                    "recall_at_k": None,
                    "reciprocal_rank": None,
                }

            keys = retrieved_keys(chunks)

            row = {
                "id": question_id,
                "method": method_name,
                "question": question,
                "answerable": answerable,
                "expected_positions": item[
                    "relevant_chunk_positions"
                ],
                "retrieved_sources": [
                    filename
                    for filename, _ in keys
                ],
                "retrieved_positions": [
                    position
                    for _, position in keys
                ],
                "retrieved_count": len(chunks),
                **metrics,
            }

            rows.append(row)

            if answerable:
                print(
                    f"{question_id} | {method_name} | "
                    f"Hit={metrics['hit_at_k']:.0f} | "
                    f"Recall={metrics['recall_at_k']:.2f} | "
                    f"RR={metrics['reciprocal_rank']:.2f}"
                )
            else:
                print(
                    f"{question_id} | {method_name} | "
                    "unanswerable: retrieval recorded"
                )

    semantic = summarize(rows, "semantic_only")
    hybrid = summarize(rows, "hybrid")

    delta = {
        key: round(hybrid[key] - semantic[key], 4)
        for key in semantic
    }

    summary = {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "configuration": {
            "top_k": top_k,
            "threshold": threshold,
            "db_path": db_path,
            "expected_filename": EXPECTED_FILENAME,
            "embedding_model": (
                "intfloat/multilingual-e5-small"
            ),
        },
        "indexed_document_names": index_info[
            "indexed_document_names"
        ],
        "total_questions": len(questions),
        "answerable_questions": sum(
            item["answerable"]
            for item in questions
        ),
        "unanswerable_questions": sum(
            not item["answerable"]
            for item in questions
        ),
        "semantic_only": semantic,
        "hybrid": hybrid,
        "hybrid_minus_semantic": delta,
        "limitations": [
            "Original positional labels may have changed "
            "after Phase 2 smart chunking.",
            "Position existence is not independent "
            "evidence relevance validation.",
            "The golden set contains questions labelled "
            "for one expected source document.",
            "Unanswerable answer-generation accuracy "
            "is not measured by this retrieval script.",
            "Historical baseline figures are not "
            "automatically reused.",
        ],
    }

    output = {
        "summary": summary,
        "questions": rows,
    }

    save_results(output, rows)

    print("\n" + "=" * 65)
    print("FINAL RETRIEVAL COMPARISON")
    print("=" * 65)

    print(
        f"{'Metric':<15}"
        f"{'Semantic':>12}"
        f"{'Hybrid':>12}"
        f"{'Delta':>12}"
    )

    for key, label in [
        ("hit_at_k", f"Hit@{top_k}"),
        ("recall_at_k", f"Recall@{top_k}"),
        ("mrr_at_k", f"MRR@{top_k}"),
    ]:
        print(
            f"{label:<15}"
            f"{semantic[key]:>12.4f}"
            f"{hybrid[key]:>12.4f}"
            f"{delta[key]:>+12.4f}"
        )

    print(
        "\nIMPORTANT: Review golden relevance labels "
        "against the current smart-chunked corpus."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Compare semantic-only and hybrid RAG retrieval."
        )
    )

    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
    )

    args = parser.parse_args()

    if args.top_k < 1:
        parser.error("--top-k must be at least 1")

    if not 0 <= args.threshold <= 1:
        parser.error(
            "--threshold must be between 0 and 1"
        )

    evaluate(
        db_path=args.db_path,
        top_k=args.top_k,
        threshold=args.threshold,
    )


"""
Production RAG Service - Chunk Size Experiments

Compare:
    A: 256 characters / 50 overlap
    B: 512 characters / 80 overlap
    C: 800 characters / 150 overlap

Uses:
    Existing chunker
    Hugging Face multilingual-e5-small
    Temporary ChromaDB collections

Does not modify the production vector database.

Run:
    python evals/run_chunk_experiments.py

Or:
    python evals/run_chunk_experiments.py --pdf "path/to/file.pdf"
"""

import argparse
import csv
import json
import re
import sys
import unicodedata

from pathlib import Path

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.chunker import split_text


GOLDEN_FILE = PROJECT_ROOT / "evals" / "golden_questions.json"
RESULTS_DIR = PROJECT_ROOT / "evals" / "results"

MODEL_NAME = "intfloat/multilingual-e5-small"

CONFIGURATIONS = [
    {"name": "A", "chunk_size": 256, "overlap": 50},
    {"name": "B", "chunk_size": 512, "overlap": 80},
    {"name": "C", "chunk_size": 800, "overlap": 150},
]

TOP_K_VALUES = [3, 5]

PDF_FILENAME = "RAG_Project_Steps_Roman_Urdu.pdf"


# Short evidence phrases taken from the source excerpts.
# These are provisional labels and must be manually audited.
EVIDENCE_PHRASES = {
    "Q001": ["step 0 setup"],
    "Q002": ["step 0 setup", "step 1 data"],
    "Q003": ["notebooks", "backend", "frontend"],
    "Q004": ["har step ke baad", "output save"],
    "Q005": ["docker se qdrant"],
    "Q006": ["bge-m3"],
    "Q007": ["qdrant mein store"],
    "Q008": ["file ka naam", "page number"],
    "Q009": ["dense", "hybrid", "rerank"],
    "Q010": ["hit rate", "recall", "mrr"],
    "Q011": ["not found in your documents"],
    "Q012": ["citations ke saath"],
    "Q013": ["faithfulness", "answer relevancy"],
    "Q014": ["50 hand-label answers"],
    "Q015": ["chunk size 256/512/1024"],
    "Q016": ["30 injection aur jailbreak"],
    "Q017": ["endpoints: upload", "ask"],
    "Q018": ["retrieved chunks", "score"],
    "Q019": ["latency", "cost"],
    "Q020": ["512/80 chunk size"],
}


def normalize(text):
    """Normalize extracted text for evidence matching."""

    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[^\w]+", " ", text)
    return " ".join(text.split())


def find_pdf(explicit_path=None):
    """Find the local source PDF without changing stored data."""

    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {path}")

        return path

    candidates = list(
        (PROJECT_ROOT / "data" / "documents").rglob("*.pdf")
    )

    candidates += list(
        PROJECT_ROOT.glob("*.pdf")
    )

    for path in candidates:
        if path.name == PDF_FILENAME:
            return path

    if len(candidates) == 1:
        return candidates[0]

    raise FileNotFoundError(
        "Source PDF not found automatically. "
        "Run with --pdf followed by the source PDF path."
    )


def extract_pages(pdf_path):
    """Extract text separately from each PDF page."""

    reader = PdfReader(str(pdf_path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if text.strip():
            pages.append({
                "page": page_number,
                "text": text
            })

    if not pages:
        raise ValueError("PDF contains no extractable text.")

    return pages


def create_experiment_chunks(pages, chunk_size, overlap):
    """Create chunks using the production chunker."""

    chunks = []

    for page in pages:
        pieces = split_text(
            text=page["text"],
            chunk_size=chunk_size,
            overlap=overlap
        )

        for piece in pieces:
            chunks.append({
                "id": f"chunk-{len(chunks)}",
                "text": piece,
                "page": page["page"]
            })

    return chunks


def label_relevant_chunks(question_id, chunks):
    """
    Identify chunks containing source-evidence phrases.

    This is an evidence-phrase proxy, not independently
    annotated relevance ground truth.
    """

    phrases = EVIDENCE_PHRASES.get(question_id, [])

    normalized_phrases = [
        normalize(phrase)
        for phrase in phrases
    ]

    relevant_ids = set()

    for chunk in chunks:
        normalized_text = normalize(chunk["text"])

        if any(
            phrase in normalized_text
            for phrase in normalized_phrases
        ):
            relevant_ids.add(chunk["id"])

    return relevant_ids


def compute_metrics(expected_ids, retrieved_ids):
    """Calculate Hit@K, Recall@K and Reciprocal Rank."""

    if not expected_ids:
        return None

    matching = expected_ids.intersection(retrieved_ids)

    hit = int(bool(matching))
    recall = len(matching) / len(expected_ids)

    reciprocal_rank = 0.0

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in expected_ids:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "hit": hit,
        "recall": recall,
        "rr": reciprocal_rank
    }


def evaluate_configuration(
    model,
    client,
    pages,
    questions,
    configuration
):
    """Create a temporary vector index and evaluate retrieval."""

    name = configuration["name"]
    chunk_size = configuration["chunk_size"]
    overlap = configuration["overlap"]

    print(
        f"\nConfiguration {name}: "
        f"size={chunk_size}, overlap={overlap}"
    )

    chunks = create_experiment_chunks(
        pages,
        chunk_size,
        overlap
    )

    if not chunks:
        raise ValueError("No chunks created.")

    print(f"Chunks created: {len(chunks)}")

    documents = [
        "passage: " + chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    collection = client.create_collection(
        name=f"experiment_{name.lower()}",
        metadata={"hnsw:space": "cosine"}
    )

    collection.add(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        embeddings=embeddings.tolist()
    )

    chunk_lookup = {
        chunk["id"]: chunk
        for chunk in chunks
    }

    question_embeddings = model.encode(
        [
            "query: " + question["question"]
            for question in questions
        ],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    evaluations = []
    summaries = []

    for top_k in TOP_K_VALUES:
        scores = []
        unlabelled = []

        for question, embedding in zip(
            questions,
            question_embeddings
        ):
            question_id = question["id"]

            expected_ids = label_relevant_chunks(
                question_id,
                chunks
            )

            response = collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=min(top_k, len(chunks))
            )

            retrieved_ids = response["ids"][0]

            metrics = compute_metrics(
                expected_ids,
                retrieved_ids
            )

            if metrics is None:
                unlabelled.append(question_id)
            else:
                scores.append(metrics)

            evaluations.append({
                "configuration": name,
                "chunk_size": chunk_size,
                "overlap": overlap,
                "top_k": top_k,
                "question_id": question_id,
                "relevant_chunk_count": len(expected_ids),
                "retrieved_ids": retrieved_ids,
                "retrieved_pages": [
                    chunk_lookup[chunk_id]["page"]
                    for chunk_id in retrieved_ids
                ],
                "hit": metrics["hit"] if metrics else None,
                "recall": (
                    metrics["recall"] if metrics else None
                ),
                "rr": metrics["rr"] if metrics else None
            })

        count = len(scores)

        summary = {
            "configuration": name,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "top_k": top_k,
            "total_chunks": len(chunks),
            "total_questions": len(questions),
            "labelled_questions": count,
            "unlabelled_questions": unlabelled,
            "hit_at_k": (
                sum(s["hit"] for s in scores) / count
                if count else None
            ),
            "recall_at_k": (
                sum(s["recall"] for s in scores) / count
                if count else None
            ),
            "mrr_at_k": (
                sum(s["rr"] for s in scores) / count
                if count else None
            )
        }

        summaries.append(summary)

        if count:
            print(
                f"Top-{top_k} | "
                f"Hit={summary['hit_at_k']:.4f} | "
                f"Recall={summary['recall_at_k']:.4f} | "
                f"MRR={summary['mrr_at_k']:.4f} | "
                f"Labelled={count}/{len(questions)}"
            )
        else:
            print(f"Top-{top_k}: no evidence labels matched")

        if unlabelled:
            print(
                "Needs label review:",
                ", ".join(unlabelled)
            )

    return summaries, evaluations


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pdf",
        default=None,
        help="Path to the source PDF"
    )

    args = parser.parse_args()

    pdf_path = find_pdf(args.pdf)

    print("=" * 60)
    print("PRODUCTION RAG - CHUNK SIZE EXPERIMENTS")
    print("=" * 60)
    print(f"PDF: {pdf_path}")
    print(f"Embedding model: {MODEL_NAME}")

    pages = extract_pages(pdf_path)

    with GOLDEN_FILE.open("r", encoding="utf-8") as file:
        all_questions = json.load(file)

    questions = [
        question
        for question in all_questions
        if question["answerable"] is True
    ]

    model = SentenceTransformer(MODEL_NAME)

    # Ephemeral means no persistent production DB changes.
    client = chromadb.EphemeralClient()

    all_summaries = []
    all_evaluations = []

    for config in CONFIGURATIONS:
        summaries, evaluations = evaluate_configuration(
            model,
            client,
            pages,
            questions,
            config
        )

        all_summaries.extend(summaries)
        all_evaluations.extend(evaluations)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = RESULTS_DIR / "chunk_experiments.json"
    csv_path = RESULTS_DIR / "chunk_experiments.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "source_pdf": str(pdf_path),
                "embedding_model": MODEL_NAME,
                "label_method": "provisional_evidence_phrases",
                "summary": all_summaries,
                "questions": all_evaluations
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
            fieldnames=list(all_summaries[0].keys())
        )

        writer.writeheader()
        writer.writerows(all_summaries)

    print("\n" + "=" * 60)
    print("EXPERIMENTS COMPLETED")
    print("=" * 60)
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")
    print(
        "Note: Evidence-phrase labels are provisional. "
        "Review unmatched questions before selecting a winner."
    )


if __name__ == "__main__":
    main()

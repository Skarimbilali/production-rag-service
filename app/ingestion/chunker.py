
from typing import Any
from uuid import UUID


CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """
    Split text into overlapping character-based chunks.

    This is our baseline chunking strategy.
    Evaluation will compare it with another configuration.
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def create_chunks(
    document_id: UUID,
    filename: str,
    extracted_sections: list[dict[str, Any]],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[dict[str, Any]]:
    """
    Convert extracted document sections into chunks
    with source metadata.
    """
    all_chunks = []
    chunk_position = 0

    for section in extracted_sections:
        text = section.get("text", "")

        section_chunks = split_text(
            text=text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for section_position, chunk_text in enumerate(
            section_chunks
        ):
            all_chunks.append({
                "id": f"{document_id}-{chunk_position}",
                "text": chunk_text,
                "metadata": {
                    "document_id": str(document_id),
                    "filename": filename,
                    "page": section.get("page"),
                    "section": section.get("section"),
                    "chunk_position": chunk_position,
                    "section_chunk_position": section_position
                }
            })

            chunk_position += 1

    return all_chunks

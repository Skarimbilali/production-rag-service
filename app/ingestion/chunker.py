
import re
from typing import Any
from uuid import UUID


CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def _normalize_text(text: str) -> tuple[str, list[int]]:
    """
    Normalize whitespace while recording paragraph boundaries.

    Returns:
        Normalized text and paragraph ending positions.
    """
    if not text or not text.strip():
        return "", []

    paragraphs = re.split(r"\n\s*\n", text)

    normalized_parts = []
    paragraph_ends = []
    current_position = 0

    for paragraph in paragraphs:
        cleaned = " ".join(paragraph.split())

        if not cleaned:
            continue

        if normalized_parts:
            current_position += 1

        normalized_parts.append(cleaned)
        current_position += len(cleaned)

        paragraph_ends.append(current_position)

    return " ".join(normalized_parts), paragraph_ends


def _find_chunk_end(
    text: str,
    start: int,
    chunk_size: int,
    overlap: int,
    paragraph_ends: list[int]
) -> int:
    """
    Prefer paragraph, sentence, then word boundaries.

    A hard character split is used only when a long
    uninterrupted sequence cannot fit into a chunk.
    """
    maximum_end = min(start + chunk_size, len(text))

    if maximum_end == len(text):
        return maximum_end

    # Avoid very short chunks just to reach a boundary.
    minimum_end = start + max(
        1,
        int(chunk_size * 0.65)
    )

    # 1. Prefer a paragraph boundary.
    paragraph_candidates = [
        position
        for position in paragraph_ends
        if minimum_end <= position <= maximum_end
    ]

    if paragraph_candidates:
        return max(paragraph_candidates)

    # 2. Prefer sentence boundaries.
    # Sentence ending punctuation followed by whitespace.
    sentence_candidates = [
        match.end()
        for match in re.finditer(
            r"[.!?۔؟]+(?=\s|$)",
            text[start:maximum_end]
        )
        if start + match.end() >= minimum_end
    ]

    if sentence_candidates:
        return start + max(sentence_candidates)

    # 3. Fall back to the last whitespace boundary.
    whitespace_position = text.rfind(
        " ",
        minimum_end,
        maximum_end
    )

    if whitespace_position > start:
        return whitespace_position

    # 4. Extremely long uninterrupted text.
    return maximum_end


def _find_next_start(
    text: str,
    previous_start: int,
    previous_end: int,
    overlap: int
) -> int:
    """
    Move backward from the previous chunk's end to
    preserve overlapping context.

    Prefer starting at a word boundary.
    """
    if overlap == 0:
        return previous_end

    target_start = max(
        previous_start + 1,
        previous_end - overlap
    )

    # If target is already at a word boundary, use it.
    if (
        target_start <= 0
        or text[target_start - 1].isspace()
    ):
        return target_start

    # Try to find the next word boundary nearby.
    next_space = text.find(
        " ",
        target_start,
        min(target_start + 40, previous_end)
    )

    if next_space != -1:
        candidate = next_space + 1

        if candidate < previous_end:
            return candidate

    # Otherwise include the full preceding word.
    previous_space = text.rfind(
        " ",
        previous_start,
        target_start
    )

    if previous_space != -1:
        candidate = previous_space + 1

        if previous_start < candidate < previous_end:
            return candidate

    # Last resort: guarantee forward progress.
    return target_start


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """
    Split text into overlapping, boundary-aware chunks.

    Priorities:
        1. Paragraph boundary
        2. Sentence boundary
        3. Word boundary
        4. Character boundary as final fallback

    Each chunk is limited to chunk_size characters.
    Overlap is approximate when adjusted to word
    boundaries.

    This implementation preserves the existing
    public function signature.
    """
    if chunk_size <= 0:
        raise ValueError(
            "Chunk size must be positive."
        )

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and "
            "smaller than chunk size."
        )

    normalized_text, paragraph_ends = (
        _normalize_text(text)
    )

    if not normalized_text:
        return []

    chunks = []
    start = 0
    text_length = len(normalized_text)

    while start < text_length:
        end = _find_chunk_end(
            text=normalized_text,
            start=start,
            chunk_size=chunk_size,
            overlap=overlap,
            paragraph_ends=paragraph_ends
        )

        if end <= start:
            raise RuntimeError(
                "Chunking failed to make progress."
            )

        chunk = normalized_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = _find_next_start(
            text=normalized_text,
            previous_start=start,
            previous_end=end,
            overlap=overlap
        )

        if next_start <= start:
            next_start = start + 1

        start = next_start

    return chunks


def create_chunks(
    document_id: UUID,
    filename: str,
    extracted_sections: list[dict[str, Any]],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[dict[str, Any]]:
    """
    Convert extracted document sections into
    boundary-aware chunks with source metadata.

    Existing chunk structure and metadata fields
    are preserved for application compatibility.
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
                "id": (
                    f"{document_id}-{chunk_position}"
                ),
                "text": chunk_text,
                "metadata": {
                    "document_id": str(document_id),
                    "filename": filename,
                    "page": section.get("page"),
                    "section": section.get("section"),
                    "chunk_position": chunk_position,
                    "section_chunk_position": (
                        section_position
                    )
                }
            })

            chunk_position += 1

    return all_chunks

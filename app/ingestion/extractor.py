
from io import BytesIO

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader


def extract_pdf(content: bytes) -> list[dict]:
    """
    Extract text from PDF pages, preserving page numbers.
    """
    try:
        reader = PdfReader(BytesIO(content))
        extracted_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                extracted_pages.append({
                    "page": page_number,
                    "text": text.strip()
                })

        if not extracted_pages:
            raise HTTPException(
                status_code=400,
                detail="PDF contains no extractable text."
            )

        return extracted_pages

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from PDF."
        ) from exc


def extract_docx(content: bytes) -> list[dict]:
    """
    Extract text from DOCX paragraphs and tables.
    DOCX does not provide reliable fixed page numbers,
    so a section identifier is used instead.
    """
    try:
        document = Document(BytesIO(content))
        blocks = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                blocks.append(text)

        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    blocks.append(" | ".join(cells))

        if not blocks:
            raise HTTPException(
                status_code=400,
                detail="DOCX contains no extractable text."
            )

        return [{
            "section": "document",
            "text": "\n".join(blocks)
        }]

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from DOCX."
        ) from exc


def extract_document(
    filename: str,
    content: bytes
) -> list[dict]:
    """
    Select the appropriate extractor using file extension.
    """
    extension = filename.lower().rsplit(".", 1)[-1]

    if extension == "pdf":
        return extract_pdf(content)

    if extension == "docx":
        return extract_docx(content)

    raise HTTPException(
        status_code=415,
        detail="Unsupported document format."
    )

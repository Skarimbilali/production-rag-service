
import logging
import re
from io import BytesIO

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader


logger = logging.getLogger(__name__)

# Generic numbered headings:
# "3. Leave Policy", "10.2 Daily Allowance"
HEADING_PATTERN = re.compile(
    r"^\d+(?:\.\d+)*\.?\s+[A-Za-z\u0600-\u06FF].{2,100}$"
)


def _detect_section(text: str) -> str | None:
    """
    Find a likely numbered section heading.

    This is heuristic-based: it does not guarantee
    heading detection for every PDF layout.
    """
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines[:12]:
        if HEADING_PATTERN.match(line):
            return line

    return None


def _extract_pdf_tables(content: bytes) -> dict[int, list[str]]:
    """
    Extract tables as searchable row-wise text.

    pdfplumber is optional. If unavailable or unable
    to parse tables, standard pypdf extraction remains
    available.

    Returns:
        {page_number: [table_text, ...]}
    """
    try:
        import pdfplumber
    except ImportError:
        logger.info(
            "pdfplumber unavailable; using standard PDF extraction."
        )
        return {}

    page_tables: dict[int, list[str]] = {}

    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables() or []

                for table_number, table in enumerate(tables, start=1):
                    if not table:
                        continue

                    cleaned_rows = []

                    for row in table:
                        if not row:
                            continue

                        cells = [
                            " ".join(str(cell or "").split())
                            for cell in row
                        ]

                        if any(cells):
                            cleaned_rows.append(cells)

                    if len(cleaned_rows) < 2:
                        continue

                    headers = cleaned_rows[0]
                    formatted_rows = []

                    for row in cleaned_rows[1:]:
                        fields = []

                        for index, value in enumerate(row):
                            if not value:
                                continue

                            header = (
                                headers[index]
                                if index < len(headers)
                                else ""
                            )

                            if header and header != value:
                                fields.append(f"{header}: {value}")
                            else:
                                fields.append(value)

                        if fields:
                            formatted_rows.append(
                                " | ".join(fields)
                            )

                    if formatted_rows:
                        table_text = (
                            f"Table {table_number}\n"
                            + "\n".join(formatted_rows)
                        )

                        page_tables.setdefault(
                            page_number, []
                        ).append(table_text)

    except Exception:
        # Table extraction is an enhancement.
        # Do not reject an otherwise readable PDF.
        logger.warning(
            "Structured PDF table extraction failed.",
            exc_info=True
        )
        return {}

    return page_tables


def extract_pdf(content: bytes) -> list[dict]:
    """
    Extract PDF text with page numbers, optional
    numbered section headings and structured tables.

    Scanned and encrypted PDFs receive clear errors.
    """
    try:
        reader = PdfReader(BytesIO(content))

        if reader.is_encrypted:
            try:
                unlocked = reader.decrypt("")
            except Exception:
                unlocked = 0

            if not unlocked:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "PDF is password-protected. "
                        "Please upload an unlocked PDF."
                    )
                )

        extracted_pages = []
        page_sections: dict[int, str | None] = {}

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                continue

            section = _detect_section(text)
            page_sections[page_number] = section

            page_data = {
                "page": page_number,
                "text": text.strip()
            }

            if section:
                page_data["section"] = section

            extracted_pages.append(page_data)

        if not extracted_pages:
            raise HTTPException(
                status_code=400,
                detail=(
                    "PDF contains no extractable text. "
                    "It may be scanned or image-based. "
                    "OCR is not currently enabled."
                )
            )

        # Keep normal page extraction intact and add
        # separately searchable structured table rows.
        tables_by_page = _extract_pdf_tables(content)

        for page_number, tables in tables_by_page.items():
            for table_number, table_text in enumerate(
                tables, start=1
            ):
                parent_section = page_sections.get(
                    page_number
                )

                section_name = (
                    f"{parent_section} | Table {table_number}"
                    if parent_section
                    else f"Table {table_number}"
                )

                extracted_pages.append({
                    "page": page_number,
                    "section": section_name,
                    "text": table_text
                })

        logger.info(
            "PDF extraction completed: %d text/table sections",
            len(extracted_pages)
        )

        return extracted_pages

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("PDF text extraction failed")

        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from PDF."
        ) from exc


def extract_docx(content: bytes) -> list[dict]:
    """
    Extract DOCX paragraphs and tables.

    DOCX has no reliable fixed page numbering,
    so section metadata is used.
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
                cells = [
                    cell.text.strip()
                    for cell in row.cells
                ]

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
    Select the appropriate extractor by file extension.
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


from pathlib import Path

from fastapi import HTTPException, UploadFile


ALLOWED_EXTENSIONS = {".pdf", ".docx"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def validate_document(file: UploadFile) -> bytes:
    """
    Validate an uploaded PDF or DOCX document.

    Checks:
    - Supported file extension
    - Empty uploads
    - Maximum file size
    - Basic file signature
    """

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Only PDF and DOCX files are supported."
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum allowed file size is 10 MB."
        )

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file."
        )

    if extension == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail="Invalid DOCX file."
        )

    return content

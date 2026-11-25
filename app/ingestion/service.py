
import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.logger import AppLogger
from app.guardrails.guardrails import GuardrailService
from app.ingestion.validator import validate_document
from app.ingestion.extractor import extract_document
from app.ingestion.chunker import create_chunks
from app.vector_store.store import VectorStoreService


logger = AppLogger.get_logger(__name__)


class DocumentService:
    """
    Manage document ingestion and source-aware chunks.

    Responsibilities:
        - Validate PDF/DOCX uploads
        - Detect duplicate documents
        - Extract document text
        - Apply document-level security guardrails
        - Create smart chunks with source context
        - Store embeddings and metadata
        - List and delete documents
    """

    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store

    def document_exists(self, file_hash: str) -> bool:
        """Identify duplicate documents by SHA-256 hash."""
        result = self.vector_store.collection.get(
            where={"file_hash": file_hash},
            limit=1,
        )

        return bool(result["ids"])

    @staticmethod
    def validate_extracted_sections(sections: list) -> None:
        """
        Scan extracted PDF/DOCX sections before indexing.

        Reject the entire upload when a section contains
        a recognized prompt-injection instruction.

        Raises:
            HTTPException(400): Empty or unsafe content.
        """
        if not sections:
            raise HTTPException(
                status_code=400,
                detail="Document contains no extractable text.",
            )

        checked_sections = 0

        for section in sections:
            if isinstance(section, dict):
                text = section.get("text", "")
            else:
                text = getattr(section, "text", "")

            if not isinstance(text, str) or not text.strip():
                continue

            try:
                GuardrailService.validate_document_text(text)
            except ValueError as exc:
                logger.warning(
                    "Document security validation failed"
                )

                raise HTTPException(
                    status_code=400,
                    detail=str(exc),
                ) from exc

            checked_sections += 1

        if checked_sections == 0:
            raise HTTPException(
                status_code=400,
                detail="Document contains no extractable text.",
            )

        logger.info(
            "Document security validation passed | sections=%d",
            checked_sections,
        )

    @staticmethod
    def add_source_context(chunks: list[dict]) -> list[dict]:
        """
        Prefix each chunk with its source information.

        The original body is preserved.
        """
        for chunk in chunks:
            metadata = chunk["metadata"]

            filename = str(
                metadata.get("filename") or "Unknown"
            )

            page = metadata.get("page")
            section = metadata.get("section")

            source_parts = [f"File: {filename}"]

            if page is not None:
                source_parts.append(f"Page: {page}")

            if section is not None and str(section).strip():
                source_parts.append(
                    f"Section: {str(section).strip()}"
                )

            source_header = (
                "[" + " | ".join(source_parts) + "]"
            )

            original_text = chunk["text"]

            if not original_text.startswith(source_header):
                chunk["text"] = (
                    f"{source_header}\n{original_text}"
                )

        return chunks

    async def upload_document(self, file: UploadFile) -> dict:
        """
        Validate, scan, chunk, embed and store a document.

        HTTP 400: Invalid, empty or unsafe document
        HTTP 409: Duplicate document
        HTTP 415: Unsupported file type
        """
        logger.info("Document ingestion started")

        try:
            # 1. Validate file.
            content = await validate_document(file)

            filename = Path(
                file.filename or ""
            ).name

            # 2. Calculate SHA-256 fingerprint.
            file_hash = hashlib.sha256(
                content
            ).hexdigest()

            # 3. Reject duplicate uploads.
            if self.document_exists(file_hash):
                logger.warning(
                    "Duplicate document rejected"
                )

                raise HTTPException(
                    status_code=409,
                    detail="Document already exists.",
                )

            # 4. Extract content and metadata.
            sections = extract_document(
                filename,
                content,
            )

            # 5. Apply document-level guardrails BEFORE
            # creating embeddings or storing vectors.
            self.validate_extracted_sections(sections)

            # 6. Generate document identifier.
            document_id = uuid4()

            # 7. Create smart document chunks.
            chunks = create_chunks(
                document_id=document_id,
                filename=filename,
                extracted_sections=sections,
            )

            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail="Document contains no extractable text.",
                )

            # 8. Add dynamic source information.
            chunks = self.add_source_context(chunks)

            # 9. Attach fingerprint for duplicate detection.
            for chunk in chunks:
                chunk["metadata"]["file_hash"] = file_hash

            # 10. Embed and store document chunks.
            stored_count = self.vector_store.add_chunks(
                chunks
            )

            logger.info(
                "Document ingestion completed: %d chunks",
                stored_count,
            )

            return {
                "document_id": str(document_id),
                "filename": filename,
                "chunk_count": stored_count,
                "message": "Document uploaded successfully.",
            }

        except HTTPException:
            raise

        except Exception:
            logger.exception(
                "Document ingestion failed"
            )
            raise

        finally:
            await file.close()

    def list_documents(self) -> list[dict]:
        """Return unique stored documents and chunk counts."""
        result = self.vector_store.collection.get(
            include=["metadatas"]
        )

        documents = {}

        for metadata in result["metadatas"]:
            if not metadata:
                continue

            document_id = metadata.get("document_id")

            if not document_id:
                continue

            if document_id not in documents:
                documents[document_id] = {
                    "document_id": document_id,
                    "filename": metadata.get("filename"),
                    "chunk_count": 0,
                }

            documents[document_id]["chunk_count"] += 1

        logger.info(
            "Listed %d documents",
            len(documents),
        )

        return list(documents.values())

    def delete_document(self, document_id: str) -> None:
        """Delete vectors for the specified document."""
        deleted_count = self.vector_store.delete_document(
            document_id
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        logger.info(
            "Deleted document with %d chunks",
            deleted_count,
        )

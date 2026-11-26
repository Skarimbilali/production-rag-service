
"""
Secure document ingestion and management.

Features:
- PDF/DOCX validation and extraction
- SHA-256 duplicate detection per user
- Document prompt-injection guardrails
- Smart chunking and source context
- User-owned ChromaDB documents
- User-specific document listing and deletion
"""

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
    Manage document ingestion and storage.

    All document operations require a trusted user_id.
    User identity must come from the verified JWT.
    """

    def __init__(
        self,
        vector_store: VectorStoreService,
    ):
        self.vector_store = vector_store

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        if (
            not isinstance(user_id, str)
            or not user_id.strip()
        ):
            raise ValueError(
                "A valid user_id is required"
            )

        return user_id

    def document_exists(
        self,
        file_hash: str,
        user_id: str,
    ) -> bool:
        """
        Detect duplicates within the same user's documents.

        Two different users may upload the same file.
        """
        user_id = self._validate_user_id(user_id)

        result = self.vector_store.collection.get(
            where={
                "$and": [
                    {"file_hash": file_hash},
                    {"user_id": user_id},
                ]
            },
            limit=1,
        )

        return bool(result["ids"])

    @staticmethod
    def validate_extracted_sections(
        sections: list,
    ) -> None:
        """
        Reject empty or unsafe document content.
        """
        if not sections:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Document contains no extractable text."
                ),
            )

        checked_sections = 0

        for section in sections:
            if isinstance(section, dict):
                text = section.get("text", "")
            else:
                text = getattr(
                    section,
                    "text",
                    "",
                )

            if (
                not isinstance(text, str)
                or not text.strip()
            ):
                continue

            try:
                GuardrailService.validate_document_text(
                    text
                )

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
                detail=(
                    "Document contains no extractable text."
                ),
            )

        logger.info(
            "Document security validation passed | "
            "sections=%d",
            checked_sections,
        )

    @staticmethod
    def add_source_context(
        chunks: list[dict],
    ) -> list[dict]:
        """
        Prefix chunks with filename, page and section.

        Preserve original chunk text.
        """
        for chunk in chunks:
            metadata = chunk["metadata"]

            filename = str(
                metadata.get("filename")
                or "Unknown"
            )

            page = metadata.get("page")
            section = metadata.get("section")

            source_parts = [
                f"File: {filename}"
            ]

            if page is not None:
                source_parts.append(
                    f"Page: {page}"
                )

            if (
                section is not None
                and str(section).strip()
            ):
                source_parts.append(
                    f"Section: {str(section).strip()}"
                )

            source_header = (
                "[" + " | ".join(source_parts) + "]"
            )

            original_text = chunk["text"]

            if not original_text.startswith(
                source_header
            ):
                chunk["text"] = (
                    f"{source_header}\n"
                    f"{original_text}"
                )

        return chunks

    async def upload_document(
        self,
        file: UploadFile,
        user_id: str,
    ) -> dict:
        """
        Validate, chunk and store one user's document.

        HTTP 400: Invalid, empty or unsafe document
        HTTP 409: Duplicate within the same account
        HTTP 415: Unsupported file type
        """
        user_id = self._validate_user_id(
            user_id
        )

        logger.info(
            "Authenticated document ingestion started"
        )

        try:
            # 1. Validate uploaded document.
            content = await validate_document(
                file
            )

            filename = Path(
                file.filename or ""
            ).name

            # 2. Calculate SHA-256 fingerprint.
            file_hash = hashlib.sha256(
                content
            ).hexdigest()

            # 3. Check duplicates only for this user.
            if self.document_exists(
                file_hash=file_hash,
                user_id=user_id,
            ):
                logger.warning(
                    "Duplicate user document rejected"
                )

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Document already exists "
                        "in your account."
                    ),
                )

            # 4. Extract document content.
            sections = extract_document(
                filename,
                content,
            )

            # 5. Apply security guardrails.
            self.validate_extracted_sections(
                sections
            )

            # 6. Generate unique document ID.
            document_id = uuid4()

            # 7. Generate source-aware chunks.
            chunks = create_chunks(
                document_id=document_id,
                filename=filename,
                extracted_sections=sections,
            )

            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Document contains no "
                        "extractable text."
                    ),
                )

            # 8. Preserve source context.
            chunks = self.add_source_context(
                chunks
            )

            # 9. Attach document fingerprint.
            for chunk in chunks:
                chunk["metadata"]["file_hash"] = (
                    file_hash
                )

            # 10. Store under trusted user identity.
            # VectorStoreService also enforces ownership.
            stored_count = (
                self.vector_store.add_chunks(
                    chunks=chunks,
                    user_id=user_id,
                )
            )

            logger.info(
                "Document ingestion completed | "
                "chunks=%d",
                stored_count,
            )

            return {
                "document_id": str(document_id),
                "filename": filename,
                "chunk_count": stored_count,
                "message": (
                    "Document uploaded successfully."
                ),
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

    def list_documents(
        self,
        user_id: str,
    ) -> list[dict]:
        """
        List only documents owned by this user.

        Legacy documents without user_id are excluded.
        """
        user_id = self._validate_user_id(
            user_id
        )

        result = self.vector_store.collection.get(
            where={
                "user_id": user_id
            },
            include=["metadatas"],
        )

        documents = {}

        for metadata in result["metadatas"]:
            if not metadata:
                continue

            document_id = metadata.get(
                "document_id"
            )

            if not document_id:
                continue

            if document_id not in documents:
                documents[document_id] = {
                    "document_id": document_id,
                    "filename": metadata.get(
                        "filename"
                    ),
                    "chunk_count": 0,
                }

            documents[document_id][
                "chunk_count"
            ] += 1

        logger.info(
            "Listed %d user documents",
            len(documents),
        )

        return list(
            documents.values()
        )

    def delete_document(
        self,
        document_id: str,
        user_id: str,
    ) -> None:
        """
        Delete only documents owned by this user.

        Return 404 for missing or unowned documents
        to avoid revealing another user's resources.
        """
        user_id = self._validate_user_id(
            user_id
        )

        deleted_count = (
            self.vector_store.delete_document(
                document_id=document_id,
                user_id=user_id,
            )
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        logger.info(
            "Deleted user document | chunks=%d",
            deleted_count,
        )

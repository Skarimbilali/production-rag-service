
import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.logger import AppLogger
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
        - Extract and chunk document text
        - Attach source context to every chunk
        - Store embeddings and metadata
        - List and delete documents
    """

    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store

    def document_exists(self, file_hash: str) -> bool:
        """
        Identify duplicate documents by SHA-256 hash.
        """
        result = self.vector_store.collection.get(
            where={"file_hash": file_hash},
            limit=1
        )

        return bool(result["ids"])

    @staticmethod
    def add_source_context(chunks: list[dict]) -> list[dict]:
        """
        Prefix each chunk with its source information.

        The original body is preserved in full.
        Source metadata remains available separately.

        The configured 800-character chunk limit applies
        to body text. The source prefix adds extra
        characters to the stored searchable text.
        """
        for chunk in chunks:
            metadata = chunk["metadata"]

            filename = str(
                metadata.get("filename") or "Unknown"
            )

            page = metadata.get("page")
            section = metadata.get("section")

            source_parts = [
                f"File: {filename}"
            ]

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

            # Avoid adding the same prefix twice.
            if not original_text.startswith(source_header):
                chunk["text"] = (
                    f"{source_header}\n{original_text}"
                )

        return chunks

    async def upload_document(self, file: UploadFile) -> dict:
        """
        Validate, extract, chunk, enrich and store a file.

        Raises:
            HTTP 400: Invalid or empty document
            HTTP 409: Duplicate document
            HTTP 415: Unsupported file type
        """
        logger.info("Document ingestion started")

        try:
            # 1. Validate uploaded file.
            content = await validate_document(file)

            filename = Path(
                file.filename or ""
            ).name

            # 2. Calculate document fingerprint.
            file_hash = hashlib.sha256(
                content
            ).hexdigest()

            # 3. Reject duplicates.
            if self.document_exists(file_hash):
                logger.warning(
                    "Duplicate document rejected"
                )

                raise HTTPException(
                    status_code=409,
                    detail="Document already exists."
                )

            # 4. Extract PDF/DOCX content.
            sections = extract_document(
                filename,
                content
            )

            # 5. Create document identifier.
            document_id = uuid4()

            # 6. Apply smart chunking.
            chunks = create_chunks(
                document_id=document_id,
                filename=filename,
                extracted_sections=sections
            )

            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Document contains no "
                        "extractable text."
                    )
                )

            # 7. Add searchable source context.
            chunks = self.add_source_context(chunks)

            # 8. Attach fingerprint to chunk metadata.
            for chunk in chunks:
                chunk["metadata"]["file_hash"] = file_hash

            # 9. Embed and store document chunks.
            stored_count = self.vector_store.add_chunks(
                chunks
            )

            logger.info(
                "Document ingestion completed: %d chunks",
                stored_count
            )

            return {
                "document_id": str(document_id),
                "filename": filename,
                "chunk_count": stored_count,
                "message": "Document uploaded successfully."
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
        """
        Return unique stored documents and chunk counts.
        """
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
                    "chunk_count": 0
                }

            documents[document_id]["chunk_count"] += 1

        logger.info(
            "Listed %d documents",
            len(documents)
        )

        return list(documents.values())

    def delete_document(self, document_id: str) -> None:
        """
        Delete all vectors associated with a document.

        Raises:
            HTTP 404: Document does not exist
        """
        deleted_count = self.vector_store.delete_document(
            document_id
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        logger.info(
            "Deleted document with %d chunks",
            deleted_count
        )

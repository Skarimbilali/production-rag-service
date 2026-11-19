
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
    Manage the document ingestion lifecycle.

    Responsibilities:
        1. Validate uploaded documents.
        2. Detect duplicate files using SHA-256.
        3. Extract PDF or DOCX text.
        4. Split extracted text into chunks.
        5. Store chunks and embeddings in ChromaDB.
        6. List uploaded documents.
        7. Delete document vectors.

    This service keeps business logic outside API routes.
    """

    def __init__(self, vector_store: VectorStoreService):
        """
        Reuse an existing vector store instance.

        Args:
            vector_store: Initialized ChromaDB service.
        """
        self.vector_store = vector_store

    def document_exists(self, file_hash: str) -> bool:
        """
        Detect duplicate document content.

        SHA-256 identifies identical files regardless
        of their filenames.
        """
        result = self.vector_store.collection.get(
            where={"file_hash": file_hash},
            limit=1
        )

        return len(result["ids"]) > 0

    async def upload_document(self, file: UploadFile) -> dict:
        """
        Validate, extract, chunk and store a document.

        Returns:
            Document information including ID and chunk count.

        Raises:
            HTTP 400: Invalid or empty document.
            HTTP 409: Duplicate document.
            HTTP 415: Unsupported file format.
        """
        logger.info("Document ingestion started")

        try:
            # Step 1: Validate file content and format.
            content = await validate_document(file)

            filename = Path(file.filename or "").name

            # Step 2: Generate unique content fingerprint.
            file_hash = hashlib.sha256(content).hexdigest()

            # Step 3: Reject an already uploaded document.
            if self.document_exists(file_hash):
                logger.warning("Duplicate document rejected")

                raise HTTPException(
                    status_code=409,
                    detail="Document already exists."
                )

            # Step 4: Extract text from PDF/DOCX.
            sections = extract_document(filename, content)

            # Step 5: Assign a unique document ID.
            document_id = uuid4()

            # Step 6: Generate chunks and source metadata.
            chunks = create_chunks(
                document_id=document_id,
                filename=filename,
                extracted_sections=sections
            )

            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail="Document contains no extractable text."
                )

            # Step 7: Attach the file fingerprint to each chunk.
            for chunk in chunks:
                chunk["metadata"]["file_hash"] = file_hash

            # Step 8: Generate embeddings and persist chunks.
            stored_count = self.vector_store.add_chunks(chunks)

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
            logger.exception("Document ingestion failed")
            raise

        finally:
            await file.close()

    def list_documents(self) -> list[dict]:
        """
        Return unique documents stored in ChromaDB.

        A document can contain multiple chunks,
        but appears only once in the response.
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
        Remove all vectors belonging to a document.

        Raises:
            HTTP 404 if the document does not exist.
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

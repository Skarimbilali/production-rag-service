
from fastapi import APIRouter, File, UploadFile, status

from app.core.logger import AppLogger
from app.ingestion.service import DocumentService
from app.vector_store.store import VectorStoreService


logger = AppLogger.get_logger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

# Share one initialized service across API requests.
vector_store = VectorStoreService()
document_service = DocumentService(vector_store)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF or DOCX document"
)
async def upload_document(
    file: UploadFile = File(...)
) -> dict:
    """
    Validate, extract, chunk, embed and store a document.

    Returns:
        Document ID, filename and number of stored chunks.
    """
    logger.info("Document upload request received")
    return await document_service.upload_document(file)


@router.get(
    "",
    summary="List uploaded documents"
)
def list_documents() -> list[dict]:
    """List unique documents stored in ChromaDB."""
    return document_service.list_documents()


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document and its vectors"
)
def delete_document(document_id: str) -> None:
    """Delete all stored chunks belonging to a document."""
    document_service.delete_document(document_id)


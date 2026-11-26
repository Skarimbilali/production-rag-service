
"""
JWT-protected document management API.

Features:
- Authenticated PDF/DOCX upload
- User-specific document listing
- Secure document deletion
- User identity extracted from verified JWT
"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    status,
)

from app.auth.router import get_current_user
from app.core.logger import AppLogger
from app.ingestion.service import DocumentService
from app.vector_store.store import VectorStoreService


logger = AppLogger.get_logger(__name__)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# Share initialized services across API requests.
vector_store = VectorStoreService()
document_service = DocumentService(vector_store)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF or DOCX document",
    responses={
        401: {
            "description": "Authentication required",
        },
        409: {
            "description": "Duplicate document",
        },
    },
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Validate, extract, chunk, embed and store a document.

    Document ownership is derived from the JWT.
    The client cannot supply another user's ID.
    """
    logger.info(
        "Authenticated document upload request received"
    )

    return await document_service.upload_document(
        file=file,
        user_id=current_user["id"],
    )


@router.get(
    "",
    summary="List current user's documents",
    responses={
        401: {
            "description": "Authentication required",
        },
    },
)
def list_documents(
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """List only documents owned by the authenticated user."""
    return document_service.list_documents(
        user_id=current_user["id"],
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user's document",
    responses={
        401: {
            "description": "Authentication required",
        },
        404: {
            "description": "Document not found or not owned by user",
        },
    },
)
def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Delete document vectors only when owned by current user.

    Unknown and unowned document IDs both return 404.
    """
    document_service.delete_document(
        document_id=document_id,
        user_id=current_user["id"],
    )

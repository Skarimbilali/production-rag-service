# Development Log

## 2026-11-19

Branch: development

### Verified
- Project directory structure created
- Python 3.11 virtual environment activated
- Dependencies installed and checked
- FastAPI health endpoint returned HTTP 200
- Swagger UI tested successfully
- PDF/DOCX extraction modules imported
- Chunking test generated 4 chunks
- Git main and development branches configured
- Multilingual E5 model loaded successfully
- Query embedding returned 384 dimensions
- Centralized logging produced expected messages

### Errors and Corrections
1. Git example output accidentally executed as commands.
   Resolution: Used actual Git commands.
2. VS Code branch indicator was inconsistent.
   Resolution: Verified active branch with Git commands.
3. ImportError for embed_query.
   Cause: embeddings.py was empty.
   Resolution: Implemented EmbeddingService.

### Pending
- ChromaDB storage testing
- Complete upload and deletion endpoints
- Retrieval and answer generation
- Guardrails and frontend
- Automated tests and evaluation
- Full assignment documentation

## 2026-11-19 - Vector Store Testing
- ChromaDB insert, search and delete: 3 tests passed.
- pytest.ini configuration error: fixed.
- Final test execution: 25.20 seconds, no warnings.

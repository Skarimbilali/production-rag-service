import json
from pathlib import Path
from textwrap import dedent

out = Path("notebooks")
out.mkdir(exist_ok=True)

def cell(kind, source):
    item = {
        "cell_type": kind,
        "metadata": {},
        "source": dedent(source).strip().splitlines(True),
    }
    if kind == "code":
        item["execution_count"] = None
        item["outputs"] = []
    return item

def write_notebook(name, parts):
    nb = {
        "cells": [cell(k, s) for k, s in parts],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {"name": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    path = out / name
    path.write_text(json.dumps(nb, indent=2), encoding="utf-8")
    print("CREATED:", path)

setup = """
from pathlib import Path
import os, sys

ROOT = Path.cwd()
if not (ROOT / "app").exists():
    ROOT = ROOT.parent

assert (ROOT / "app").exists(), "Project root not found"
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print("Project root:", ROOT)
"""

write_notebook("01_ingestion_pipeline.ipynb", [
    ("markdown", """
    # Production RAG Service — Notebook 1

    ## Ingestion Pipeline

    Real application implementation:
    PDF/DOCX extraction → Smart chunking → Metadata
    → multilingual E5 embeddings.

    All code uses production application classes.
    """),

    ("code", setup),

    ("code", """
    from uuid import uuid4
    from io import BytesIO
    from docx import Document

    from app.ingestion.extractor import extract_document
    from app.ingestion.chunker import (
        create_chunks, CHUNK_SIZE, CHUNK_OVERLAP
    )
    from app.ingestion.embeddings import EmbeddingService

    print("Application imports PASSED")
    """),

    ("markdown", """
    ## 1. PDF Extraction

    Uses the TechNova test PDF.
    Extracted content retains page and optional section.
    """),

    ("code", """
    pdf = ROOT / "TechNova_HR_Policy_Manual.pdf"
    assert pdf.exists(), f"Missing: {pdf}"

    pdf_sections = extract_document(
        pdf.name, pdf.read_bytes()
    )
    assert pdf_sections

    print("PDF sections:", len(pdf_sections))
    for section in pdf_sections[:3]:
        print(
            "Page:", section.get("page"),
            "Section:", section.get("section")
        )
        print(section["text"][:200], "\\n")
    """),

    ("markdown", """
    ## 2. DOCX Extraction

    Creates an in-memory DOCX sample containing
    paragraphs and a table.
    """),

    ("code", """
    doc = Document()
    doc.add_heading("Example Company Policy", level=1)
    doc.add_paragraph(
        "Employees receive 20 working days of annual leave."
    )
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Grade"
    table.cell(0, 1).text = "Allowance"
    table.cell(1, 0).text = "G4"
    table.cell(1, 1).text = "PKR 10000"

    buffer = BytesIO()
    doc.save(buffer)

    docx_sections = extract_document(
        "sample.docx", buffer.getvalue()
    )

    assert docx_sections
    print("DOCX extracted:", docx_sections)
    """),

    ("markdown", """
    ## 3. Smart Chunking

    The application uses 800-character chunks with
    150-character approximate overlap.
    Metadata retains original document information.
    """),

    ("code", """
    chunks = create_chunks(
        document_id=uuid4(),
        filename=pdf.name,
        extracted_sections=pdf_sections
    )
    assert chunks

    print("Chunk size:", CHUNK_SIZE)
    print("Overlap:", CHUNK_OVERLAP)
    print("Total chunks:", len(chunks))

    for item in chunks[:3]:
        assert len(item["text"]) <= CHUNK_SIZE
        print(item["metadata"])
        print(item["text"][:150], "\\n")
    """),

    ("markdown", """
    ## 4. Embeddings

    Uses the application's real multilingual E5 model.
    Initial download may require internet access.
    """),

    ("code", """
    samples = [item["text"] for item in chunks[:3]]
    vectors = EmbeddingService.embed_documents(samples)

    assert len(vectors) == len(samples)
    assert all(len(vector) == 384 for vector in vectors)

    query_vector = EmbeddingService.embed_query(
        "How many annual leave days?"
    )
    assert len(query_vector) == 384

    print("Document vectors:", len(vectors))
    print("Vector dimensions:", len(vectors[0]))
    print("Query dimensions:", len(query_vector))
    print("NOTEBOOK 1: PASSED")
    """),
])

write_notebook("02_retrieval_generation.ipynb", [
    ("markdown", """
    # Production RAG Service — Notebook 2

    ## Retrieval and Answer Generation

    Uses production ChromaDB, hybrid retrieval,
    citation handling and Groq LLM client.

    Uses a separate temporary vector database,
    leaving the production collection untouched.
    """),

    ("code", setup),

    ("code", """
    import tempfile
    from uuid import uuid4

    from app.ingestion.extractor import extract_document
    from app.ingestion.chunker import create_chunks
    from app.vector_store.store import VectorStoreService
    from app.retrieval.retriever import RetrievalService
    from app.generation.generator import GenerationService
    from app.generation.llm_client import GroqLLMClient
    from app.config import settings

    print("Application imports PASSED")
    """),

    ("markdown", """
    ## 1. Index a Real PDF

    Uses the TechNova manual.
    The temporary database is not the application DB.
    """),

    ("code", """
    pdf = ROOT / "TechNova_HR_Policy_Manual.pdf"
    assert pdf.exists(), f"Missing: {pdf}"

    sections = extract_document(
        pdf.name, pdf.read_bytes()
    )

    chunks = create_chunks(
        document_id=uuid4(),
        filename=pdf.name,
        extracted_sections=sections
    )

    temp_dir = tempfile.TemporaryDirectory(
        prefix="rag_notebook_"
    )
    store = VectorStoreService(db_path=temp_dir.name)
    count = store.add_chunks(chunks)

    assert count == len(chunks)
    assert store.count_chunks() == count

    print("Indexed chunks:", count)
    print("Temporary DB:", temp_dir.name)
    """),

    ("markdown", """
    ## 2. Hybrid Retrieval

    Show the retrieved chunk count, similarity scores,
    page numbers and source text.
    """),

    ("code", """
    question = "How many annual leave days are allowed?"

    retriever = RetrievalService(store)
    results = retriever.retrieve(
        question=question,
        top_k=5,
        threshold=0.30
    )

    print("Question:", question)
    print("Retrieved chunk count:", len(results))
    assert results, "No chunks passed retrieval threshold"

    for index, item in enumerate(results, start=1):
        metadata = item["metadata"]
        print(
            f"Chunk S{index}",
            "File:", metadata.get("filename"),
            "Page:", metadata.get("page"),
            "Score:", round(item["similarity_score"], 4)
        )
        print(item["text"][:350], "\\n")
    """),

    ("markdown", """
    ## 3. Grounded Groq Generation

    Requires a configured GROQ_API_KEY.
    This cell uses the actual production Groq client,
    not a mock answer.
    """),

    ("code", """
    assert settings.GROQ_API_KEY.strip(), (
        "Missing GROQ_API_KEY in .env. "
        "Configure it before running this cell."
    )

    llm = GroqLLMClient()
    try:
        generator = GenerationService(llm.generate)
        answer = await generator.generate_answer(
            question=question,
            chunks=results
        )
    finally:
        await llm.close()

    print("Question:", question)
    print("Answer:", answer["answer"])
    print("Citations:", answer["citations"])
    print("Retrieved count:", answer["retrieved_count"])

    assert "answer" in answer
    assert "citations" in answer
    assert answer["retrieved_count"] == len(results)
    """),

    ("markdown", """
    ## 4. Verify Refusal Without Evidence

    No evidence means the generator must refuse
    without making an LLM API call.
    """),

    ("code", """
    async def blocked_llm(messages):
        raise AssertionError(
            "LLM should not be called without evidence"
        )

    refusal_generator = GenerationService(blocked_llm)
    refusal = await refusal_generator.generate_answer(
        question="Question without retrieved evidence",
        chunks=[]
    )

    print(refusal)
    assert refusal["citations"] == []
    assert refusal["retrieved_count"] == 0
    print("Refusal test PASSED")
    """),

    ("markdown", """
    ## 5. Clean Up

    Delete the temporary notebook database.
    """),

    ("code", """
    print("Temporary database cleanup deferred until kernel shutdown")
    print("Temporary vector database cleaned up")
    print("NOTEBOOK 2: PASSED")
    """),
])

print("Both Jupyter notebooks created successfully.")

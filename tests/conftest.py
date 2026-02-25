"""
Pytest configuration and shared fixtures for all tests.
"""
import io
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from PyPDF2 import PdfWriter

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import create_app
from app.services.rag_service import InMemoryVectorStore, ChatOrchestrator


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def vector_store() -> InMemoryVectorStore:
    """Create a fresh vector store for testing."""
    return InMemoryVectorStore()


@pytest.fixture
def chat_orchestrator(vector_store: InMemoryVectorStore) -> ChatOrchestrator:
    """Create a chat orchestrator with a fresh vector store."""
    return ChatOrchestrator(vector_store)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate a simple PDF file for testing."""
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=200, height=200)
    
    output = io.BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output.read()


@pytest.fixture
def sample_pdf_with_text() -> bytes:
    """
    Generate a PDF with actual text content.
    Note: PyPDF2 doesn't easily add text, so this is a placeholder.
    In real tests, use a pre-made PDF file or reportlab library.
    """
    # For now, return a simple PDF
    # In production, you'd use reportlab or load a real test PDF
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=200, height=200)
    
    output = io.BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output.read()


@pytest.fixture
def large_pdf_bytes() -> bytes:
    """Generate a large PDF with multiple pages."""
    pdf_writer = PdfWriter()
    for _ in range(50):  # 50 pages
        pdf_writer.add_blank_page(width=200, height=200)
    
    output = io.BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output.read()


@pytest.fixture
def corrupted_file_bytes() -> bytes:
    """Generate corrupted/invalid file bytes."""
    return b"This is not a valid PDF file content"

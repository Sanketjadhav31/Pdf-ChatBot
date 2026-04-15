# Test Suite for PDF Chatbot RAG System

## Overview
Comprehensive test suite covering all aspects of the PDF chatbot system including API endpoints, PDF processing, vector store operations, and end-to-end workflows.

## Test Structure

```
backend/tests/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Shared fixtures and test configuration
├── test_pdf_upload.py             # PDF upload endpoint tests (8 tests)
├── test_chat_api.py               # Chat API endpoint tests (10 tests)
├── test_pdf_processing.py         # PDF chunking and extraction tests (7 tests)
├── test_vector_store.py           # Vector store and similarity search tests (9 tests)
├── test_chat_orchestrator.py      # Chat orchestrator logic tests (6 tests)
├── test_integration.py            # End-to-end integration tests (5 tests)
├── test_edge_cases.py             # Edge cases and boundary conditions (9 tests)
└── README.md                      # This file
```

## Test Categories

### 1. PDF Upload Tests (`test_pdf_upload.py`)
- ✅ Valid PDF upload
- ✅ Non-PDF file rejection
- ✅ Large PDF handling
- ✅ Corrupted file handling
- ✅ Empty PDF handling
- ✅ Special characters in filename
- ✅ Multiple PDF uploads
- ✅ Missing file parameter

### 2. Chat API Tests (`test_chat_api.py`)
- ✅ Chat without documents
- ✅ Chat with uploaded documents
- ✅ Response format validation
- ✅ Empty question handling
- ✅ Very long question handling
- ✅ Session ID persistence
- ✅ New session creation
- ✅ Special characters in questions
- ✅ Missing question field
- ✅ Irrelevant question handling

### 3. PDF Processing Tests (`test_pdf_processing.py`)
- ✅ Text extraction from PDF
- ✅ Chunk metadata validation
- ✅ Empty page skipping
- ✅ Sequential page numbering
- ✅ Unique chunk IDs
- ✅ Corrupted PDF error handling
- ✅ Chunk content type validation

### 4. Vector Store Tests (`test_vector_store.py`)
- ✅ Adding chunks to store
- ✅ Embedding generation
- ✅ Consistent embedding dimensions
- ✅ Relevant chunk retrieval
- ✅ Top-k parameter respect
- ✅ Similarity threshold filtering
- ✅ Empty store handling
- ✅ Cosine similarity calculation
- ✅ High similarity for identical text

### 5. Chat Orchestrator Tests (`test_chat_orchestrator.py`)
- ✅ No documents handling
- ✅ Session ID creation
- ✅ Session ID preservation
- ✅ Chat with documents
- ✅ Reference generation
- ✅ Irrelevant question handling

### 6. Integration Tests (`test_integration.py`)
- ✅ Complete upload and chat flow
- ✅ Multiple documents handling
- ✅ Session persistence across chats
- ✅ Sequential upload and chat
- ✅ Error recovery after failed upload

### 7. Edge Cases Tests (`test_edge_cases.py`)
- ✅ Unicode filename handling
- ✅ Unicode question handling
- ✅ Very long session ID
- ✅ Whitespace-only questions
- ✅ SQL injection pattern safety
- ✅ HTML tag safety
- ✅ Very long filename
- ✅ Null value rejection
- ✅ Missing content-type header

## Running Tests

### Install Dependencies
```bash
cd backend
poetry install --with dev
```

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_pdf_upload.py
pytest tests/test_chat_api.py
```

### Run with Coverage Report
```bash
pytest tests/ --cov=backend/app --cov-report=html
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

### Run Specific Test Case
```bash
pytest tests/test_pdf_upload.py::TestPDFUpload::test_upload_valid_pdf_success
```

## Test Fixtures

### Available Fixtures (in `conftest.py`)
- `client`: FastAPI TestClient for API testing
- `vector_store`: Fresh InMemoryVectorStore instance
- `chat_orchestrator`: ChatOrchestrator with fresh vector store
- `sample_pdf_bytes`: Simple PDF for basic testing
- `sample_pdf_with_text`: PDF with text content
- `large_pdf_bytes`: Large PDF with 50+ pages
- `corrupted_file_bytes`: Invalid file bytes for error testing

## Expected Test Results

Total Tests: 54 test cases
- PDF Upload: 8 tests
- Chat API: 10 tests
- PDF Processing: 7 tests
- Vector Store: 9 tests
- Chat Orchestrator: 6 tests
- Integration: 5 tests
- Edge Cases: 9 tests

## Notes

1. **Mock Data**: Some tests use mock PDF data. For production testing, use real PDF files with actual content.

2. **Async Tests**: If your endpoints are async, ensure pytest-asyncio is installed.

3. **Database**: Tests use in-memory vector store. No external database required.

4. **Isolation**: Each test is isolated and doesn't affect others.

5. **CI/CD**: These tests can be integrated into CI/CD pipelines for automated testing.

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running tests from the backend directory:
```bash
cd backend
pytest tests/
```

### Fixture Not Found
Make sure `conftest.py` is in the tests directory and properly configured.

### PDF Generation Issues
If PDF generation fails, install reportlab for better PDF creation:
```bash
poetry add --group dev reportlab
```

## Future Enhancements

- Add performance/load testing
- Add tests for real LLM integration
- Add tests for external vector databases (FAISS, Pinecone)
- Add tests for authentication/authorization
- Add tests for rate limiting
- Add stress tests for concurrent requests

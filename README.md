# PDF Chatbot with RAG

A full-stack intelligent PDF chatbot application that enables natural conversations with your documents using Retrieval-Augmented Generation (RAG). Upload PDFs, ask questions, and receive accurate answers with precise page references.

> **Note**: This project now uses Poetry for dependency management. See [QUICKSTART_POETRY.md](QUICKSTART_POETRY.md) for quick setup or [POETRY_MIGRATION.md](POETRY_MIGRATION.md) for detailed migration guide.

## Features

- 🔐 **User Authentication** - Secure JWT-based registration and login system
- 📄 **PDF Upload & Processing** - Automatic text extraction and intelligent chunking
- 💬 **Interactive Chat Interface** - Real-time conversations with document context
- 🔍 **Semantic Search** - Vector-based similarity search using Google embeddings (3072 dimensions)
- 🤖 **AI-Powered Responses** - Google Gemini 2.5 Flash for accurate, context-aware answers
- 📚 **Multi-Document Support** - Upload and chat with multiple PDFs simultaneously
- 📖 **Built-in PDF Viewer** - View documents with page navigation directly in the app
- 🎯 **Smart References** - Clickable page references that jump to exact locations
- 💾 **Chat History** - Persistent conversation sessions with automatic saving
- 🎨 **Modern UI** - Dark/light theme with responsive design using React and Tailwind CSS
- ⚡ **Batch Processing** - Parallel embedding generation for faster uploads
- 🗑️ **Document Management** - Delete documents and their associated vector embeddings

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL toolkit and ORM for database management
- **SQLite/MySQL/PostgreSQL** - Flexible database support
- **Google Generative AI** - Gemini 2.5 Flash for LLM and embeddings
- **PyPDF2** - PDF text extraction
- **NumPy** - Efficient vector operations and similarity calculations
- **JWT (python-jose)** - Secure token-based authentication
- **bcrypt** - Password hashing

### Frontend
- **React 18** - Modern UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **Vite** - Lightning-fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework

## Architecture

### RAG Pipeline
1. **Document Processing**: PDFs are chunked into semantic segments with metadata
2. **Embedding Generation**: Text chunks are converted to 3072-dimensional vectors using Google's embedding model
3. **Vector Storage**: In-memory vector store with cosine similarity search
4. **Query Processing**: User questions are embedded and matched against document chunks
5. **Context Retrieval**: Top-k most relevant chunks are retrieved (with similarity threshold)
6. **Answer Generation**: Google Gemini generates responses based on retrieved context
7. **Reference Tracking**: Page numbers and document metadata are preserved for citations

### Database Schema
- **Users**: Authentication and user management
- **ChatSessions**: Conversation threads with titles and timestamps
- **ChatMessages**: Individual messages (user/assistant) within sessions
- **UploadedDocuments**: Metadata for uploaded PDFs with file paths

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Google AI API Key (for embeddings and LLM)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pdf-chatbot-rag
```

### 2. Backend Setup

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install Python dependencies
poetry install

# Activate the virtual environment (optional, Poetry handles this automatically)
poetry shell
```

Create a `.env` file in the project root:

```env
# Google AI API Key (REQUIRED)
GOOGLE_API_KEY=your_google_api_key_here

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database Configuration (SQLite by default)
DATABASE_URL=sqlite:///./pdf_chatbot.db

# For MySQL (optional)
# DATABASE_URL=mysql+pymysql://username:password@localhost:3306/pdf_chatbot

# For PostgreSQL (optional)
# DATABASE_URL=postgresql://username:password@localhost:5432/pdf_chatbot
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
# From project root
poetry run uvicorn main:app --reload --port 5000

# Or use the Poetry script
poetry run start
```

The API will be available at `http://localhost:5000`
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Documentation

### Authentication Endpoints

#### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Document Endpoints

#### Upload PDF
```http
POST /api/v1/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <pdf-file>
```

Response:
```json
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "total_chunks": 150
}
```

#### List Documents
```http
GET /api/v1/documents
Authorization: Bearer <token>
```

#### View PDF
```http
GET /api/v1/documents/{document_id}/view
```

#### Delete Document
```http
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <token>
```

### Chat Endpoints

#### Send Message
```http
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "optional-session-id",
  "question": "What is this document about?"
}
```

Response:
```json
{
  "answer": "This document discusses...",
  "references": [
    {
      "document_id": "uuid",
      "page_number": 5,
      "document_heading": "Introduction",
      "paragraph_heading": "Overview"
    }
  ],
  "session_id": "session-uuid"
}
```

#### List Chat Sessions
```http
GET /api/v1/chat/sessions
Authorization: Bearer <token>
```

#### Get Chat History
```http
GET /api/v1/chat/sessions/{session_id}
Authorization: Bearer <token>
```

#### Delete Chat Session
```http
DELETE /api/v1/chat/sessions/{session_id}
Authorization: Bearer <token>
```

## Project Structure

```
.
├── api/
│   └── v1/
│       ├── auth.py              # Authentication endpoints
│       ├── chat.py              # Chat endpoints with RAG
│       ├── document_upload.py   # PDF upload and management
│       └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthForm.tsx     # Login/register form
│   │   │   ├── ChatInput.tsx    # Message input with attachments
│   │   │   ├── ChatMessage.tsx  # Message display with references
│   │   │   ├── PdfUpload.tsx    # File upload component
│   │   │   ├── PdfViewer.tsx    # Embedded PDF viewer
│   │   │   ├── Sidebar.tsx      # Navigation and document list
│   │   │   └── UploadProgress.tsx # Upload progress indicator
│   │   ├── App.tsx              # Main application component
│   │   ├── main.tsx             # Entry point
│   │   └── styles.css           # Global styles
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.cjs
├── models/
│   └── schemas.py               # Pydantic models and schemas
├── services/
│   ├── embedding_service.py     # Google embeddings (3072-dim)
│   ├── llm_service.py           # Google Gemini 2.5 Flash
│   ├── pdf_loader.py            # PDF text extraction
│   └── rag_service.py           # Vector store and RAG orchestration
├── tests/                       # Comprehensive test suite
│   ├── conftest.py
│   ├── test_chat_api.py
│   ├── test_integration.py
│   ├── test_pdf_processing.py
│   └── ...
├── uploads/                     # Uploaded PDF storage
├── database.py                  # SQLAlchemy models and auth helpers
├── main.py                      # FastAPI application entry point
├── pyproject.toml               # Poetry dependencies and configuration
├── poetry.lock                  # Poetry lock file (auto-generated)
├── requirements.txt             # Legacy pip dependencies (deprecated)
├── .env                         # Environment configuration
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google AI API key for embeddings and LLM | - | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT token signing | - | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | 60 | No |
| `DATABASE_URL` | Database connection string | `sqlite:///./pdf_chatbot.db` | No |

### Database Options

The application supports multiple database backends:

1. **SQLite** (default, no setup required)
   ```env
   DATABASE_URL=sqlite:///./pdf_chatbot.db
   ```

2. **MySQL**
   ```env
   DATABASE_URL=mysql+pymysql://username:password@localhost:3306/pdf_chatbot
   ```

3. **PostgreSQL**
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/pdf_chatbot
   ```

### RAG Configuration

Key parameters in `services/rag_service.py`:

- **Similarity Threshold**: `0.2` (adjustable for stricter/looser matching)
- **Top-K Results**: `10` chunks retrieved per query
- **Reference Threshold**: `0.5` (minimum similarity for page references)
- **Max Chunks**: `200` per document (auto-downsampling for large PDFs)
- **Embedding Dimension**: `3072` (Google gemini-embedding-001)

## Development

### Running Tests

```bash
# Install test dependencies (included in dev group)
poetry install --with dev

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=. --cov-report=html

# Run specific test file
poetry run pytest tests/test_chat_api.py -v
```

### Frontend Development

```bash
cd frontend

# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality

```bash
# Format Python code (install black first)
poetry add --group dev black
poetry run black .

# Lint Python code (install flake8 first)
poetry add --group dev flake8
poetry run flake8 .

# Type checking (install mypy first)
poetry add --group dev mypy
poetry run mypy .
```

## Usage Guide

### Getting Started

1. **Register/Login**: Create an account or sign in
2. **Upload PDF**: Click "Upload PDF" button and select a document
3. **Wait for Processing**: The app will extract text and generate embeddings
4. **Start Chatting**: Ask questions about your document
5. **View References**: Click page numbers to jump to exact locations in the PDF

### Tips for Best Results

- **Specific Questions**: Ask targeted questions for more accurate answers
- **Use Keywords**: Include specific terms from the document
- **Request Summaries**: Ask for "key points" or "summary" for overviews
- **Word Count**: Specify "in 100 words" for concise answers
- **Multiple Documents**: Upload related PDFs for cross-document queries

### Example Questions

- "Summarize this PDF and provide key points"
- "What are the main topics covered in this document?"
- "Explain [specific concept] in simple terms"
- "List the most important points from page 5"
- "What does the document say about [topic]?"
- "Provide a summary in 200 words"

## Troubleshooting

### Backend Issues

**Import errors**
```bash
poetry install
```

**API key errors**
- Verify `GOOGLE_API_KEY` is set in `.env`
- Check API key is valid at https://aistudio.google.com/app/apikey

**Database errors**
- Ensure database file has write permissions
- For MySQL/PostgreSQL, verify connection credentials

**Embedding quota exceeded**
- Wait a few minutes before retrying
- Use smaller PDFs (under 200 chunks)
- The app auto-downsamples large documents

### Frontend Issues

**Build errors**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**CORS errors**
- Ensure backend is running on port 5000
- Check CORS origins in `main.py` match frontend URL

**Authentication issues**
- Clear browser localStorage
- Check JWT token expiration settings

**PDF viewer not loading**
- Verify document ID is correct
- Check backend `/documents/{id}/view` endpoint is accessible

## Performance Optimization

### Backend
- Batch embedding generation (4 parallel workers)
- In-memory vector store for fast similarity search
- Automatic chunk downsampling for large PDFs
- Connection pooling for database queries

### Frontend
- React component memoization
- Lazy loading for PDF viewer
- Debounced search inputs
- Optimized re-renders with proper state management

## Security

- JWT-based authentication with bcrypt password hashing
- Token expiration and refresh mechanisms
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for allowed origins
- File type validation for uploads
- User-scoped data access (documents and chats)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Google Generative AI** for powerful embeddings and LLM capabilities
- **FastAPI** for the excellent async web framework
- **React** and **Vite** for modern frontend tooling
- **Tailwind CSS** for beautiful, responsive design
- **SQLAlchemy** for robust database management

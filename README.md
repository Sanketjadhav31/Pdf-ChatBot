# PDF Chatbot with RAG

A full-stack intelligent PDF chatbot application that enables natural conversations with your documents using Retrieval-Augmented Generation (RAG). Upload PDFs, ask questions, and receive accurate answers with precise page references.

> **Note**: This project now uses Poetry for dependency management. See [QUICKSTART_POETRY.md](QUICKSTART_POETRY.md) for quick setup or [POETRY_MIGRATION.md](POETRY_MIGRATION.md) for detailed migration guide.

## Features

### Core Features
- 🔐 **User Authentication** - Secure JWT-based registration and login system
- 📄 **PDF Upload & Processing** - Automatic text extraction and intelligent chunking
- 💬 **Interactive Chat Interface** - Real-time streaming conversations with document context
- 🔍 **Semantic Search** - Vector-based similarity search using embeddings
- 🤖 **Dual LLM Support** - Choose between Google Gemini or Ollama (local LLM)
- 📚 **Multi-Document Support** - Upload and chat with multiple PDFs simultaneously
- 📖 **Built-in PDF Viewer** - View documents with page navigation directly in the app
- 🎯 **Smart References** - Clickable page references that jump to exact locations
- 💾 **Chat History** - Persistent conversation sessions with automatic saving
- 🎨 **Modern UI** - Dark/light theme with responsive design using React and Tailwind CSS
- ⚡ **Batch Processing** - Parallel embedding generation for faster uploads
- 🗑️ **Document Management** - Delete documents and their associated vector embeddings

### Advanced Features
- 🧠 **Real-Time Thinking Display** - See the LLM's reasoning process as it generates answers
- 📖 **Read Mode** - Interactive PDF reading with text selection and contextual chat
- 🎯 **Text Selection Popup** - Highlight PDF text to get instant explanations or ask questions
- 🔄 **Split View Layout** - Side-by-side PDF viewer and chat interface
- 💭 **Thinking + Answer Separation** - Collapsible thinking process with smooth streaming
- 🚀 **Server-Sent Events (SSE)** - Real-time streaming for smooth ChatGPT-like experience
- 🗨️ **Message Classification** - AI routes messages to SOCIAL/PDF_QUESTION/OUT_OF_SCOPE paths
- 🔄 **Query Rewriting** - Resolves follow-up references into self-contained search queries
- 💬 **Conversational Context** - Last 3 Q&A exchanges sent to LLM for continuity
- 🎭 **Social Response Handler** - Warm responses for greetings/thanks using user's first name
- 🚫 **Refusal Poisoning Prevention** - Filters refusal messages from history
- 📊 **Redis Caching** - Fast chat history retrieval with LRU-style message limiting
- 🔗 **Session-Document Linking** - Tracks which PDFs belong to each chat session
- 🎨 **Snippet Display** - Shows text evidence with header deduplication
- 📱 **Responsive Design** - Works seamlessly on desktop, tablet, and mobile

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework with async support
- **MongoDB** - NoSQL database for flexible document storage
- **Redis** - In-memory cache for fast chat history retrieval
- **Google Generative AI** - Gemini 2.5 Flash for LLM and embeddings
- **Ollama** - Local LLM support (qwen2.5:3b, llama3, etc.)
- **Qdrant** - Production-grade vector database for semantic search
- **PyPDF2** - PDF text extraction and processing
- **NumPy** - Efficient vector operations and similarity calculations
- **JWT (python-jose)** - Secure token-based authentication
- **bcrypt** - Password hashing
- **Motor** - Async MongoDB driver for Python

### Frontend
- **React 18** - Modern UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **Vite** - Lightning-fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **PDF.js** - PDF rendering and text selection
- **Server-Sent Events (SSE)** - Real-time streaming communication

## Architecture

### RAG Pipeline with Real-Time Streaming
1. **Document Processing**: PDFs are chunked into semantic segments with metadata
2. **Embedding Generation**: Text chunks are converted to vectors using Google's embedding model or Ollama
3. **Vector Storage**: Qdrant vector database with cosine similarity search
4. **Query Processing**: User questions are embedded and matched against document chunks
5. **Context Retrieval**: Top-k most relevant chunks are retrieved (with similarity threshold)
6. **Real-Time Streaming**: LLM generates responses with Server-Sent Events (SSE)
7. **Thinking Display**: LLM's reasoning process is shown separately from the final answer
8. **Answer Generation**: Google Gemini or Ollama generates responses based on retrieved context
9. **Reference Tracking**: Page numbers and document metadata are preserved for citations

### LLM Options

The application supports two LLM backends:

- **Google Gemini** (default): Cloud-based, powerful, requires API key
  - Model: gemini-2.0-flash-exp
  - Embedding: text-embedding-004 (768 dimensions)
  - Best for: Production, high accuracy
  - Setup: Set `GOOGLE_API_KEY` in `.env`

- **Ollama**: Local LLM, privacy-focused, no API key needed
  - Models: qwen2.5:3b, llama3, mistral, etc.
  - Embedding: nomic-embed-text:latest
  - Best for: Development, privacy, offline use
  - Setup: Install Ollama and set `USE_OLLAMA=true`

Switch between them using the `USE_OLLAMA` environment variable. See [README_OLLAMA.md](README_OLLAMA.md) for Ollama setup.

### Database Architecture
- **MongoDB**: User data, chat sessions, messages, documents
- **Redis**: Chat history caching with LRU-style message limiting
- **Qdrant**: Vector embeddings for semantic search
- **GridFS**: Large PDF file storage in MongoDB

### Real-Time Streaming Architecture
- **Server-Sent Events (SSE)**: Unidirectional streaming from server to client
- **Structured Markers**: `<<<THINKING_START>>>`, `<<<ANSWER_START>>>`, etc.
- **Word-by-Word Animation**: Smooth ChatGPT-like text display (50ms interval)
- **Status Updates**: Real-time progress indicators during processing

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- MongoDB (local or cloud)
- Redis (local or cloud)
- Qdrant (Docker or cloud)
- Google AI API Key (for Gemini) OR Ollama (for local LLM)
- Docker (optional, for containerized deployment)

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
# LLM Configuration (choose one)
# Option 1: Google Gemini (cloud-based)
USE_OLLAMA=false
GOOGLE_API_KEY=your_google_api_key_here

# Option 2: Ollama (local LLM)
# USE_OLLAMA=true
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen2.5:3b
# OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# MongoDB Configuration (REQUIRED)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=pdf_chatbot

# Redis Configuration (REQUIRED)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_USERNAME=
REDIS_MAX_MESSAGES=6
REDIS_TTL_HOURS=24

# Qdrant Configuration (REQUIRED)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=pdf_chunks

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Server Configuration
BACKEND_PORT=10000
FRONTEND_URL=http://localhost:3000
```

### Optional: Setup Ollama (for local LLM)

If you want to use Ollama instead of Google Gemini:

```bash
# Install Ollama (visit https://ollama.ai)
# Windows: Download installer from website
# Mac: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull qwen2.5:3b
ollama pull nomic-embed-text:latest

# Update .env
USE_OLLAMA=true
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
```

See [README_OLLAMA.md](README_OLLAMA.md) for detailed Ollama setup instructions.

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
# From project root
poetry run uvicorn main:app --reload --port 10000

# Or use the Poetry script
poetry run start
```

The API will be available at `http://localhost:10000`
- Swagger UI: `http://localhost:10000/docs`
- ReDoc: `http://localhost:10000/redoc`
- Health Check: `http://localhost:10000/api/v1/health`

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

#### Send Message (Streaming)
```http
POST /api/v1/chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "optional-session-id",
  "question": "What is this document about?"
}
```

Response (Server-Sent Events):
```
data: {"type": "metadata", "session_id": "uuid", "provider": "Ollama", "model": "qwen2.5:3b"}

data: {"type": "status", "message": "🔍 Analyzing your question..."}

data: {"type": "classification", "value": "PDF_QUESTION"}

data: {"type": "status", "message": "📚 Searching document..."}

data: {"type": "references", "data": [...]}

data: {"type": "status", "message": "🧠 Generating response..."}

data: {"type": "thinking", "text": "I need to analyze the context..."}

data: {"type": "status", "message": "✍️ Generating answer..."}

data: {"type": "content", "text": "This document discusses..."}

data: {"type": "done", "answer": "...", "references": [...]}
```

#### Send Message (Non-Streaming - Legacy)
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
│       ├── chat.py              # Chat endpoints (legacy)
│       ├── chat_stream.py       # Streaming chat with SSE
│       ├── document_upload.py   # PDF upload and management
│       ├── health.py            # Health check endpoint
│       ├── read_mode.py         # Read mode endpoints
│       └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthForm.tsx           # Login/register form
│   │   │   ├── ChatInput.tsx          # Message input with attachments
│   │   │   ├── ChatMessage.tsx        # Message display with thinking/answer
│   │   │   ├── PdfUpload.tsx          # File upload component
│   │   │   ├── PdfViewer.tsx          # Embedded PDF viewer
│   │   │   ├── ReadModeChat.tsx       # Read mode chat interface
│   │   │   ├── ReadModePdfViewer.tsx  # PDF viewer with text selection
│   │   │   ├── ReadModeSelector.tsx   # Mode selection modal
│   │   │   ├── ReadModeSplitView.tsx  # Split view layout
│   │   │   ├── Sidebar.tsx            # Navigation and document list
│   │   │   ├── TextSelectionPopup.tsx # Text selection actions
│   │   │   ├── Toast.tsx              # Toast notifications
│   │   │   └── UploadProgress.tsx     # Upload progress indicator
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
│   ├── embedding_service.py     # Embedding generation (Google/Ollama)
│   ├── llm_service.py           # LLM service (Gemini/Ollama)
│   ├── pdf_loader.py            # PDF text extraction
│   ├── qdrant_service.py        # Qdrant vector database
│   ├── rag_service.py           # RAG orchestration
│   ├── read_mode_service.py     # Read mode logic
│   ├── redis_service.py         # Redis caching
│   └── __init__.py
├── tests/                       # Comprehensive test suite
│   ├── conftest.py
│   ├── test_chat_api.py
│   ├── test_integration.py
│   ├── test_pdf_processing.py
│   └── ...
├── database.py                  # MongoDB connection and auth helpers
├── logger_config.py             # Logging configuration
├── main.py                      # FastAPI application entry point
├── list_ollama_models.py        # Utility to list Ollama models
├── pyproject.toml               # Poetry dependencies and configuration
├── poetry.lock                  # Poetry lock file (auto-generated)
├── requirements.txt             # Pip dependencies
├── .env                         # Environment configuration
├── .env.example                 # Example environment file
├── README.md                    # This file
├── README_OLLAMA.md             # Ollama setup guide
└── command_list.txt             # Docker commands reference
```

### Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| **LLM Configuration** |
| `USE_OLLAMA` | Use Ollama instead of Google Gemini | `false` | No |
| `GOOGLE_API_KEY` | Google AI API key (if using Gemini) | - | Conditional |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | No |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5:3b` | No |
| `OLLAMA_EMBEDDING_MODEL` | Ollama embedding model | `nomic-embed-text:latest` | No |
| **Database Configuration** |
| `MONGODB_URI` | MongoDB connection string | - | Yes |
| `MONGODB_DB_NAME` | MongoDB database name | `pdf_chatbot` | Yes |
| `REDIS_HOST` | Redis server host | `localhost` | Yes |
| `REDIS_PORT` | Redis server port | `6379` | Yes |
| `REDIS_PASSWORD` | Redis password | - | No |
| `REDIS_MAX_MESSAGES` | Max messages per session in cache | `6` | No |
| `REDIS_TTL_HOURS` | Cache expiration time (hours) | `24` | No |
| **Vector Database** |
| `QDRANT_URL` | Qdrant server URL | - | Yes |
| `QDRANT_API_KEY` | Qdrant API key | - | Yes |
| `QDRANT_COLLECTION` | Qdrant collection name | `pdf_chunks` | No |
| **Authentication** |
| `JWT_SECRET_KEY` | Secret key for JWT signing | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `60` | No |
| **Server** |
| `BACKEND_PORT` | Backend server port | `10000` | No |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` | No |

### Database Options

The application uses MongoDB for data storage and Redis for caching:

1. **MongoDB** (required)
   - Stores user data, chat sessions, messages, and documents
   - Supports local or cloud (MongoDB Atlas)
   ```env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_DB_NAME=pdf_chatbot
   ```

2. **Redis** (required)
   - Caches chat history for fast retrieval
   - LRU-style message limiting per session
   - Supports local or cloud (Redis Cloud, Upstash)
   ```env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=your_password
   ```

3. **Qdrant** (required)
   - Vector database for semantic search
   - Supports local Docker or cloud (Qdrant Cloud)
   ```env
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_api_key
   ```

### RAG Configuration

Key parameters in `services/llm_service.py` and `services/rag_service.py`:

- **Similarity Threshold**: `0.2` (adjustable for stricter/looser matching)
- **Top-K Results**: `10` chunks retrieved per query
- **Reference Threshold**: `0.5` (minimum similarity for page references)
- **Max Chunks**: `200` per document (auto-downsampling for large PDFs)
- **Embedding Dimensions**: 
  - Google: `768` (text-embedding-004)
  - Ollama: `768` (nomic-embed-text)
- **Streaming**: Real-time SSE with thinking + answer separation
- **Context Window**: Last 3 Q&A exchanges (6 messages) for conversation continuity
- **Redis Cache**: 6 messages per session, 24-hour TTL

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
5. **View Thinking**: See the LLM's reasoning process in the collapsible thinking box
6. **View References**: Click page numbers to jump to exact locations in the PDF
7. **Try Read Mode**: Click "Read Mode" button to read PDFs with text selection and contextual chat

### Chat Mode Features

- **Real-Time Streaming**: See responses generate word-by-word like ChatGPT
- **Thinking Display**: Collapsible box shows LLM's reasoning process
- **Smart References**: Click page numbers to open PDF viewer at exact location
- **Chat History**: All conversations are saved and accessible from sidebar
- **Multi-Document**: Upload multiple PDFs and ask cross-document questions

### Read Mode Features

- **Text Selection**: Highlight any text in the PDF
- **Instant Actions**: Get explanations, summaries, or ask custom questions
- **Split View**: PDF viewer and chat side-by-side
- **Context-Aware**: Selected text is automatically included in queries
- **Seamless Reading**: Read and chat without switching modes

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

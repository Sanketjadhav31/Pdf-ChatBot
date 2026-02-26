# PDF Chatbot with RAG

A full-stack application that enables intelligent conversations with PDF documents using Retrieval-Augmented Generation (RAG). Upload PDFs, ask questions, and get accurate answers based on the document content.

## Features

- 📄 PDF document upload and processing
- 💬 Interactive chat interface with document context
- 🔍 Vector-based semantic search using embeddings
- 🤖 Support for multiple LLM providers (Google Gemini, Ollama)
- ⚡ Real-time streaming responses
- 🎨 Modern, responsive UI built with React and Tailwind CSS
- 📊 Document management with sidebar navigation

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration and RAG pipeline
- **Google Generative AI** - Embeddings and LLM
- **Ollama** - Local LLM support
- **PyPDF2** - PDF text extraction
- **NumPy** - Vector operations

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first styling

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- (Optional) Ollama for local LLM

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Configure your `.env` file:

```env
# Google AI API Key (required for embeddings)
GOOGLE_API_KEY=your_google_api_key_here

# Ollama Configuration (optional)
OLLAMA_BASE_URL=http://localhost:11434
USE_OLLAMA=true
OLLAMA_MODEL=gpt-oss:120b-cloud
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
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Upload Document
```http
POST /api/v1/upload
Content-Type: multipart/form-data

file: <pdf-file>
```

#### Chat with Document
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "What is this document about?",
  "document_id": "doc_123"
}
```

## Project Structure

```
.
├── api/
│   └── v1/
│       ├── chat.py              # Chat endpoint
│       ├── document_upload.py   # Upload endpoint
│       └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── App.tsx             # Main app component
│   │   └── main.tsx            # Entry point
│   └── package.json
├── models/
│   └── schemas.py              # Pydantic models
├── services/
│   ├── embedding_service.py    # Vector embeddings
│   ├── llm_service.py          # LLM integration
│   ├── pdf_loader.py           # PDF processing
│   └── rag_service.py          # RAG orchestration
├── tests/                      # Test suite
├── uploads/                    # Uploaded PDFs storage
├── main.py                     # FastAPI application
├── requirements.txt            # Python dependencies
└── README.md
```

## Configuration

### LLM Provider Selection

The application supports two LLM providers:

1. **Google Gemini** (default)
   - Set `USE_OLLAMA=false` in `.env`
   - Requires `GOOGLE_API_KEY`

2. **Ollama** (local)
   - Set `USE_OLLAMA=true` in `.env`
   - Configure `OLLAMA_BASE_URL` and `OLLAMA_MODEL`
   - Requires Ollama running locally

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key for embeddings | Yes |
| `USE_OLLAMA` | Use Ollama instead of Google LLM | No (default: false) |
| `OLLAMA_BASE_URL` | Ollama server URL | If using Ollama |
| `OLLAMA_MODEL` | Ollama model name | If using Ollama |

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r tests/test_requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## Usage

1. **Upload a PDF**: Click the upload button and select a PDF file
2. **Wait for Processing**: The document will be processed and embedded
3. **Ask Questions**: Type your question in the chat input
4. **Get Answers**: Receive contextual answers based on the document content

## Troubleshooting

### Backend Issues

- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **API key errors**: Verify your `GOOGLE_API_KEY` is set correctly in `.env`
- **Ollama connection**: Check that Ollama is running if `USE_OLLAMA=true`

### Frontend Issues

- **Build errors**: Delete `node_modules` and run `npm install` again
- **CORS errors**: Ensure backend is running and CORS origins are configured correctly

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LangChain for RAG framework
- Google for Generative AI APIs
- FastAPI for the excellent web framework
- React and Vite teams for frontend tools

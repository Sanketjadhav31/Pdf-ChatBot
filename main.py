from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import chat_router, document_upload_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PDF Chatbot RAG Backend",
        version="0.1.0",
        description="Backend API for the PDF Chatbot using RAG.",
    )

    # CORS – allow local frontend during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(document_upload_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    return app


app = create_app()


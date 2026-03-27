from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from api.v1 import chat_router, document_upload_router
from api.v1.auth import router as auth_router
from database import connect_to_mongodb, close_mongodb_connection, ensure_embedding_index_metadata
from services.embedding_service import embedding_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up application...")
    await connect_to_mongodb()
    await ensure_embedding_index_metadata(
        embedding_model_name=embedding_service.model_name,
        embedding_dimension=embedding_service.dimension,
    )
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    await close_mongodb_connection()
    print("✅ Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="PDF Chatbot RAG Backend",
        version="0.2.0",
        description="Backend API for the PDF Chatbot using RAG.",
        lifespan=lifespan,
    )

    # CORS – allow local frontend during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(document_upload_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    return app


app = create_app()


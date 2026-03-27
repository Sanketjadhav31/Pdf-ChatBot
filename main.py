from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request, Response
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

    # CORS – MUST be added before routes
    frontend_url = os.getenv("FRONTEND_URL", "https://pdfchatbot1.netlify.app")
    print(f"🔒 CORS: Allowing origins: {frontend_url} and all origins")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_url, "*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )
    
    # Add middleware to handle CORS headers on all responses
    @app.middleware("http")
    async def add_cors_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(document_upload_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    return app


app = create_app()


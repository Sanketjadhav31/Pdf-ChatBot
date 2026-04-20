from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from api.v1 import chat_router, document_upload_router
from api.v1.auth import router as auth_router
from api.v1.read_mode import router as read_mode_router
from database import connect_to_mongodb, close_mongodb_connection, ensure_embedding_index_metadata
from services.embedding_service import embedding_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: connect to MongoDB, load vector store, and cleanup on shutdown"""
    # Startup
    print("🚀 Starting up application...")
    await connect_to_mongodb()
    await ensure_embedding_index_metadata(
        embedding_model_name=embedding_service.model_name,
        embedding_dimension=embedding_service.dimension,
    )
    
    # Reload vector store from database on startup
    print("🔄 Checking vector store status...")
    try:
        from database import database, get_gridfs
        from services.rag_service import vector_store
        from services.pdf_loader import extract_chunks_from_pdf
        
        # Check if FAISS already has data loaded from disk
        if vector_store.size > 0:
            print(f"✅ Vector store already loaded from disk: {vector_store.size} chunks")
            print("⚡ Skipping database reload (FAISS persistence active)")
        elif database is None:
            print("⚠️  Database not initialized, skipping vector store reload")
        else:
            print("📂 Vector store empty, reloading from database...")
            docs = await database.uploaded_documents.find({}).to_list(length=None)
            
            if not docs:
                print("✅ No documents to reload")
            else:
                print(f"📚 Found {len(docs)} documents in database")
                gridfs = get_gridfs()
                reloaded_count = 0
                
                for doc in docs:
                    doc_id = doc["_id"]
                    filename = doc.get("filename", "unknown")
                    gridfs_file_id = doc.get("gridfs_file_id")
                    
                    if not gridfs_file_id:
                        print(f"   ⚠️  Skipping {filename}: No GridFS file ID")
                        continue
                    
                    try:
                        # Download PDF from GridFS
                        from bson import ObjectId
                        grid_out = await gridfs.open_download_stream(ObjectId(gridfs_file_id))
                        file_data = await grid_out.read()
                        
                        # Extract chunks
                        chunks = extract_chunks_from_pdf(
                            document_id=doc_id,
                            filename=filename,
                            file_bytes=file_data,
                        )
                        
                        # Add to vector store
                        vector_store.add_chunks(chunks)
                        reloaded_count += 1
                        print(f"   ✅ Reloaded: {filename} ({len(chunks)} chunks)")
                        
                    except Exception as e:
                        print(f"   ⚠️  Failed to reload {filename}: {e}")
                
                print(f"✅ Reloaded {reloaded_count}/{len(docs)} documents into vector store")
                print(f"📊 Total chunks in vector store: {vector_store.size}")
    except Exception as e:
        print(f"⚠️  Failed to check/reload vector store: {e}")
    
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    await close_mongodb_connection()
    print("✅ Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application with CORS, middleware, and route handlers"""
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
    app.include_router(read_mode_router, prefix="/api/v1")

    return app


app = create_app()


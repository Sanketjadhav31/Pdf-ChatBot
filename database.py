import os
import socket
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError


# Custom DNS Configuration
USE_CUSTOM_DNS = os.getenv("USE_CUSTOM_DNS", "false").lower() == "true"
DNS_SERVERS = os.getenv("DNS_SERVERS", "8.8.8.8,8.8.4.4").split(",")
FORCE_IPV4 = os.getenv("FORCE_IPV4", "false").lower() == "true"


def configure_custom_dns():
    """Configure custom DNS servers if enabled to resolve MongoDB connection issues"""
    if not USE_CUSTOM_DNS:
        return
    
    print(f"🔧 Configuring custom DNS: {DNS_SERVERS}")
    
    # Store original getaddrinfo
    original_getaddrinfo = socket.getaddrinfo
    
    def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        """Custom DNS resolver using specified DNS servers"""
        if FORCE_IPV4:
            family = socket.AF_INET
        
        try:
            return original_getaddrinfo(host, port, family, type, proto, flags)
        except socket.gaierror as e:
            print(f"⚠️ DNS resolution failed for {host}: {e}")
            print(f"🔄 Retrying with custom DNS servers...")
            
            # Fallback to custom DNS
            import dns.resolver
            resolver = dns.resolver.Resolver()
            resolver.nameservers = DNS_SERVERS
            
            try:
                answers = resolver.resolve(host, 'A' if FORCE_IPV4 else 'AAAA')
                ip = str(answers[0])
                print(f"✅ Resolved {host} to {ip}")
                return [(family or socket.AF_INET, type, proto, '', (ip, port))]
            except Exception as dns_error:
                print(f"❌ Custom DNS resolution failed: {dns_error}")
                raise e
    
    # Monkey patch socket.getaddrinfo
    socket.getaddrinfo = custom_getaddrinfo
    print("✅ Custom DNS configured successfully")


# Configure DNS before MongoDB connection
configure_custom_dns()


# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_URI_STANDARD = os.getenv("MONGODB_URI_STANDARD")

# Global MongoDB client
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None
gridfs_bucket: Optional[AsyncIOMotorGridFSBucket] = None


async def connect_to_mongodb():
    """Initialize MongoDB connection with SRV and standard URI fallback support"""
    global mongodb_client, database, gridfs_bucket
    
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI environment variable is required")
    
    try:
        print("🔌 Connecting to MongoDB (SRV)...")
        mongodb_client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        # Test connection
        await mongodb_client.admin.command('ping')
        print("✅ Connected to MongoDB successfully (SRV)")
        
    except Exception as e:
        print(f"⚠️ SRV connection failed: {e}")
        
        if MONGODB_URI_STANDARD:
            try:
                print("🔄 Trying fallback standard connection...")
                mongodb_client = AsyncIOMotorClient(
                    MONGODB_URI_STANDARD,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                )
                await mongodb_client.admin.command('ping')
                print("✅ Connected to MongoDB successfully (Standard)")
            except Exception as fallback_error:
                print(f"❌ Fallback connection failed: {fallback_error}")
                raise
        else:
            raise
    
    # Extract database name from URI
    db_name = MONGODB_URI.split('/')[-1].split('?')[0]
    database = mongodb_client[db_name]
    
    # Initialize GridFS bucket for file storage
    gridfs_bucket = AsyncIOMotorGridFSBucket(database)
    
    # Create indexes
    await create_indexes()
    print(f"✅ Using database: {db_name}")
    print(f"✅ GridFS initialized for file storage")


async def close_mongodb_connection():
    """Close MongoDB connection and cleanup resources"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("🔌 MongoDB connection closed")


async def create_indexes():
    """Create database indexes for users, sessions, messages, and documents to optimize queries"""
    if database is None:
        return
    
    # Users collection indexes
    await database.users.create_index([("email", ASCENDING)], unique=True)
    await database.users.create_index([("created_at", DESCENDING)])
    
    # Chat sessions indexes
    await database.chat_sessions.create_index([("user_id", ASCENDING)])
    await database.chat_sessions.create_index([("created_at", DESCENDING)])
    await database.chat_sessions.create_index([("updated_at", DESCENDING)])
    
    # Chat messages indexes
    await database.chat_messages.create_index([("session_id", ASCENDING)])
    await database.chat_messages.create_index([("user_id", ASCENDING)])
    await database.chat_messages.create_index([("created_at", DESCENDING)])
    
    # Chat session documents indexes
    await database.chat_session_documents.create_index([("session_id", ASCENDING)])
    await database.chat_session_documents.create_index([("document_id", ASCENDING)])
    
    # Uploaded documents indexes
    await database.uploaded_documents.create_index([("user_id", ASCENDING)])
    await database.uploaded_documents.create_index([("created_at", DESCENDING)])
    
    # Embedding index metadata
    await database.embedding_index_metadata.create_index([("index_name", ASCENDING)], unique=True)
    
    # Read mode sessions indexes
    await database.read_mode_sessions.create_index([("user_id", ASCENDING)])
    await database.read_mode_sessions.create_index([("document_id", ASCENDING)])
    await database.read_mode_sessions.create_index([("created_at", DESCENDING)])
    
    # Read mode messages indexes
    await database.read_mode_messages.create_index([("session_id", ASCENDING)])
    await database.read_mode_messages.create_index([("user_id", ASCENDING)])
    await database.read_mode_messages.create_index([("created_at", DESCENDING)])
    
    print("✅ Database indexes created")


def get_database():
    """FastAPI dependency to inject database instance into route handlers"""
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not established"
        )
    return database


def get_gridfs():
    """FastAPI dependency to inject GridFS bucket for PDF file storage"""
    if gridfs_bucket is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GridFS not initialized"
        )
    return gridfs_bucket


# --- Auth helpers (JWT + password hashing) ---

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hashed password"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for password storage"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token with expiration time"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) + timedelta(hours=5, minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class TokenData(BaseModel):
    sub: Optional[str] = None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database)
) -> Dict[str, Any]:
    """Decode JWT token and return authenticated user from database"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str | None = payload.get("sub")
        if subject is None:
            raise credentials_exception
        token_data = TokenData(sub=subject)
    except JWTError:
        raise credentials_exception

    user = await db.users.find_one({"_id": token_data.sub})
    if user is None:
        raise credentials_exception
    return user


async def ensure_embedding_index_metadata(
    embedding_model_name: str,
    embedding_dimension: int,
    index_name: str = "in_memory_default",
) -> None:
    """Validate embedding model compatibility and clear incompatible embeddings on dimension mismatch"""
    if database is None:
        return
    
    existing = await database.embedding_index_metadata.find_one({"index_name": index_name})

    if existing is None:
        await database.embedding_index_metadata.insert_one({
            "index_name": index_name,
            "embedding_model_name": embedding_model_name,
            "embedding_dimension": embedding_dimension,
            "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
            "updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
        })
        print(
            f"Created embedding index metadata: index={index_name}, "
            f"model={embedding_model_name}, dimension={embedding_dimension}"
        )
        return

    if existing["embedding_dimension"] != embedding_dimension:
        print(
            f"⚠️ Embedding dimension changed for index '{index_name}': "
            f"existing={existing['embedding_dimension']}, current={embedding_dimension}"
        )
        print("🔄 Clearing all document embeddings and updating index metadata...")
        
        # Clear all embeddings from documents since they're incompatible
        await database.documents.update_many(
            {},
            {
                "$set": {
                    "chunks": [],
                    "updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30)
                }
            }
        )
        
        # Update the index metadata with new dimensions
        await database.embedding_index_metadata.update_one(
            {"index_name": index_name},
            {
                "$set": {
                    "embedding_model_name": embedding_model_name,
                    "embedding_dimension": embedding_dimension,
                    "updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30)
                }
            }
        )
        
        print(f"✅ Index metadata updated. Users will need to re-upload their documents.")
        return

    if existing["embedding_model_name"] != embedding_model_name:
        print(
            "⚠️ Embedding model changed while dimension stayed compatible: "
            f"existing={existing['embedding_model_name']}, current={embedding_model_name}"
        )
        await database.embedding_index_metadata.update_one(
            {"index_name": index_name},
            {
                "$set": {
                    "embedding_model_name": embedding_model_name,
                    "updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30)
                }
            }
        )

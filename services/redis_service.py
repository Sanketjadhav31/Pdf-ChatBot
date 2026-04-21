"""
Redis service for managing chat session history with user isolation.
Implements LRU-style cache with configurable message limits per session.
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
from logger_config import setup_logger

logger = setup_logger(__name__)


class RedisService:
    """
    Manages chat history caching in Redis with per-user session isolation.
    
    Features:
    - User-specific session keys for isolation
    - LRU-style message limiting (FIFO when limit reached)
    - Automatic expiration (24 hours default)
    - Graceful fallback on connection errors
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_messages_per_session: Optional[int] = None,
        session_ttl_hours: Optional[int] = None,
    ):
        """
        Initialize Redis connection with configuration from environment or parameters.
        
        Args:
            host: Redis server hostname (defaults to env REDIS_HOST)
            port: Redis server port (defaults to env REDIS_PORT)
            username: Redis username (defaults to env REDIS_USERNAME)
            password: Redis password (defaults to env REDIS_PASSWORD)
            max_messages_per_session: Maximum messages to store per session (defaults to env REDIS_MAX_MESSAGES or 6)
            session_ttl_hours: Hours before session cache expires (defaults to env REDIS_TTL_HOURS or 24)
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.username = username or os.getenv("REDIS_USERNAME", "")
        self.password = password or os.getenv("REDIS_PASSWORD", "")
        self.max_messages = max_messages_per_session or int(os.getenv("REDIS_MAX_MESSAGES", "6"))
        self.ttl_seconds = (session_ttl_hours or int(os.getenv("REDIS_TTL_HOURS", "24"))) * 3600
        self._client: Optional[Redis] = None
        
        logger.info(
            f"Redis service initialized: {self.host}:{self.port}, "
            f"max_messages={self.max_messages}, ttl={self.ttl_seconds//3600}h"
        )
    
    async def connect(self) -> bool:
        """
        Establish connection to Redis server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            # Test connection
            await self._client.ping()
            logger.info(f"✅ Connected to Redis: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self._client = None
            return False
    
    async def disconnect(self):
        """Close Redis connection gracefully."""
        if self._client:
            try:
                await self._client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None
    
    def _get_session_key(self, user_id: str, session_id: str) -> str:
        """
        Generate Redis key for user session.
        
        Format: chat:history:{user_id}:{session_id}
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            
        Returns:
            str: Redis key for this session
        """
        return f"chat:history:{user_id}:{session_id}"
    
    async def get_chat_history(
        self, 
        user_id: str, 
        session_id: str
    ) -> List[Dict[str, str]]:
        """
        Retrieve chat history from Redis cache.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            
        Returns:
            List of message dicts with 'role' and 'content' keys.
            Returns empty list if cache miss or error.
        """
        if not self._client:
            logger.warning("Redis client not connected, skipping cache read")
            return []
        
        try:
            key = self._get_session_key(user_id, session_id)
            messages_json = await self._client.lrange(key, 0, -1)
            
            if not messages_json:
                logger.debug(f"Cache miss: {key}")
                return []
            
            messages = [json.loads(msg) for msg in messages_json]
            logger.info(
                f"✅ Cache hit: {key} - Retrieved {len(messages)} messages"
            )
            return messages
            
        except Exception as e:
            logger.error(f"Error reading from Redis: {e}")
            return []
    
    async def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> bool:
        """
        Add a single message to session history with LRU behavior.
        
        When max_messages limit is reached, oldest message is removed (FIFO).
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._client:
            logger.warning("Redis client not connected, skipping cache write")
            return False
        
        try:
            key = self._get_session_key(user_id, session_id)
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }
            message_json = json.dumps(message)
            
            # Use pipeline for atomic operations
            async with self._client.pipeline(transaction=True) as pipe:
                # Add message to end of list
                pipe.rpush(key, message_json)
                
                # Trim to max size (keep only last N messages)
                pipe.ltrim(key, -self.max_messages, -1)
                
                # Set expiration
                pipe.expire(key, self.ttl_seconds)
                
                await pipe.execute()
            
            logger.debug(f"✅ Added {role} message to cache: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to Redis: {e}")
            return False
    
    async def set_chat_history(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, str]],
    ) -> bool:
        """
        Replace entire chat history for a session (used when loading from DB).
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._client:
            logger.warning("Redis client not connected, skipping cache write")
            return False
        
        try:
            key = self._get_session_key(user_id, session_id)
            
            # Delete existing key and set new history atomically
            async with self._client.pipeline(transaction=True) as pipe:
                pipe.delete(key)
                
                # Add messages (limit to max_messages)
                limited_messages = messages[-self.max_messages:]
                for msg in limited_messages:
                    # Ensure timestamp exists
                    if "timestamp" not in msg:
                        msg["timestamp"] = datetime.utcnow().isoformat()
                    message_json = json.dumps(msg)
                    pipe.rpush(key, message_json)
                
                # Set expiration
                pipe.expire(key, self.ttl_seconds)
                
                await pipe.execute()
            
            logger.info(
                f"✅ Set chat history in cache: {key} - "
                f"{len(limited_messages)} messages"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error setting chat history in Redis: {e}")
            return False
    
    async def clear_session(self, user_id: str, session_id: str) -> bool:
        """
        Clear chat history for a specific session.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._client:
            logger.warning("Redis client not connected, skipping cache clear")
            return False
        
        try:
            key = self._get_session_key(user_id, session_id)
            await self._client.delete(key)
            logger.info(f"✅ Cleared session cache: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing session from Redis: {e}")
            return False
    
    async def get_session_size(self, user_id: str, session_id: str) -> int:
        """
        Get number of messages in session cache.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            
        Returns:
            int: Number of messages in cache, 0 if error
        """
        if not self._client:
            return 0
        
        try:
            key = self._get_session_key(user_id, session_id)
            size = await self._client.llen(key)
            return size
            
        except Exception as e:
            logger.error(f"Error getting session size from Redis: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self._client:
            return False
        
        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()

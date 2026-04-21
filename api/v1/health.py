"""
Health check endpoints for monitoring application status.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from services.redis_service import redis_service
from database import database

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    redis: dict
    mongodb: dict


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Check health status of all services (Redis, MongoDB).
    Returns detailed status for monitoring and debugging.
    """
    # Check Redis
    redis_healthy = await redis_service.health_check()
    redis_status = {
        "connected": redis_healthy,
        "host": redis_service.host,
        "port": redis_service.port,
        "max_messages": redis_service.max_messages,
        "ttl_hours": redis_service.ttl_seconds // 3600,
    }
    
    # Check MongoDB
    mongodb_healthy = False
    mongodb_status = {"connected": False}
    
    try:
        if database is not None:
            # Ping MongoDB
            await database.command("ping")
            mongodb_healthy = True
            mongodb_status = {
                "connected": True,
                "database": database.name,
            }
    except Exception as e:
        mongodb_status = {
            "connected": False,
            "error": str(e),
        }
    
    # Overall status
    overall_status = "healthy" if (redis_healthy and mongodb_healthy) else "degraded"
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        redis=redis_status,
        mongodb=mongodb_status,
    )


@router.get("/health/redis")
async def redis_health():
    """Quick Redis health check endpoint."""
    healthy = await redis_service.health_check()
    return {
        "service": "redis",
        "status": "healthy" if healthy else "unhealthy",
        "connected": healthy,
    }


@router.get("/health/mongodb")
async def mongodb_health():
    """Quick MongoDB health check endpoint."""
    try:
        if database is not None:
            await database.command("ping")
            return {
                "service": "mongodb",
                "status": "healthy",
                "connected": True,
            }
    except Exception as e:
        return {
            "service": "mongodb",
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }
    
    return {
        "service": "mongodb",
        "status": "unhealthy",
        "connected": False,
        "error": "Database not initialized",
    }

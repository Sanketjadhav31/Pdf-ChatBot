"""
API v1 endpoints.

This module exports all v1 routers for easy inclusion in the main app.
"""

from .chat import router as chat_router
from .document_upload import router as document_upload_router

__all__ = ["chat_router", "document_upload_router"]

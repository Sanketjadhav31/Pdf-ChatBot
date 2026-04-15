"""
Read Mode Service - Handles text selection-based PDF reading assistance.

This service is completely separate from the RAG pipeline. It provides
context-aware assistance based on user-selected text from PDFs without
using vector search or embeddings.
"""

from io import BytesIO
from typing import List, Dict, Optional
from PyPDF2 import PdfReader
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId

from logger_config import setup_logger

logger = setup_logger(__name__)


class ReadModeService:
    """Service for Read Mode operations"""
    
    @staticmethod
    async def extract_page_text(
        gridfs: AsyncIOMotorGridFSBucket,
        gridfs_file_id: str,
        page_number: int
    ) -> tuple[str, int]:
        """
        Extract text from a specific page of a PDF stored in GridFS.
        
        Args:
            gridfs: GridFS bucket instance
            gridfs_file_id: GridFS file ID
            page_number: Page number (1-indexed)
            
        Returns:
            Tuple of (page_text, total_pages)
        """
        try:
            # Download PDF from GridFS
            grid_out = await gridfs.open_download_stream(ObjectId(gridfs_file_id))
            file_data = await grid_out.read()
            
            # Extract text from specific page
            pdf_reader = PdfReader(BytesIO(file_data))
            total_pages = len(pdf_reader.pages)
            
            if page_number < 1 or page_number > total_pages:
                raise ValueError(f"Page number {page_number} out of range (1-{total_pages})")
            
            # PyPDF2 uses 0-indexed pages
            page = pdf_reader.pages[page_number - 1]
            text = page.extract_text() or ""
            
            logger.info(f"Extracted {len(text)} characters from page {page_number}/{total_pages}")
            return text.strip(), total_pages
            
        except Exception as e:
            logger.error(f"Error extracting page text: {e}", exc_info=True)
            raise
    
    @staticmethod
    def build_read_mode_context(
        selected_text: Optional[str],
        page_text: str,
        history: List[Dict[str, str]],
        max_history_turns: int = 3
    ) -> Dict[str, str]:
        """
        Build the 3-layer context for Read Mode:
        1. Selected text (highest priority)
        2. Page context (supporting layer)
        3. Conversation history (continuity layer)
        
        Args:
            selected_text: Text the user highlighted
            page_text: Full text of the current page
            history: Recent conversation messages
            max_history_turns: Maximum number of conversation turns to include
            
        Returns:
            Dictionary with context layers
        """
        # Layer 1: Selected text
        selection_context = selected_text.strip() if selected_text else ""
        
        # Layer 2: Page context (limit to reasonable size)
        MAX_PAGE_CHARS = 3000
        page_context = page_text[:MAX_PAGE_CHARS]
        if len(page_text) > MAX_PAGE_CHARS:
            page_context += "..."
        
        # Layer 3: Conversation history (last N turns)
        history_context = []
        for msg in history[-max_history_turns * 2:]:  # *2 because each turn has user + assistant
            role = msg.get("role", "").capitalize()
            content = msg.get("content", "").strip()
            selected = msg.get("selected_text", "")
            page_num = msg.get("page_number")
            
            if role == "User" and selected:
                history_context.append(f"[Page {page_num} — User selected: \"{selected[:100]}...\"]")
            history_context.append(f"{role}: {content}")
        
        return {
            "selected_text": selection_context,
            "page_text": page_context,
            "history": "\n".join(history_context) if history_context else "(no recent history)"
        }
    
    @staticmethod
    def format_read_mode_prompt(
        question: str,
        context: Dict[str, str],
        username: str = "User"
    ) -> str:
        """
        Format the Read Mode prompt for the LLM.
        
        This prompt enforces strict adherence to the provided context
        and prevents the LLM from using external knowledge.
        """
        first_name = username.strip().split()[0] if username.strip() else "User"
        
        selected_text_block = ""
        if context["selected_text"]:
            selected_text_block = f"""
SELECTED TEXT (user's primary focus):
\"\"\"{context['selected_text']}\"\"\"
"""
        
        prompt = f"""You are a reading assistant. The user is actively reading a document and needs help understanding specific parts.

{selected_text_block}
SURROUNDING PAGE CONTEXT (for understanding only, not primary):
\"\"\"{context['page_text']}\"\"\"

CONVERSATION HISTORY:
{context['history']}

USER QUESTION: {question}

CRITICAL RULES:
- Answer strictly from the selected text and page context above
- Never use external knowledge or information not in the document
- If the answer is not in the provided context, say: "This is not mentioned in the visible text."
- Be concise unless the user asks for detail
- Use simple English
- If selected text is provided, prioritize it over page context

Response formatting:
- Default: 3-5 sentences maximum
- Use numbered points ONLY when explaining a process or list
- Give one real-world example per explanation (when helpful)
- Never use jargon without explaining it immediately after
"""
        return prompt.strip()


read_mode_service = ReadModeService()

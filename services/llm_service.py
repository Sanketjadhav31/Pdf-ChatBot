import os
from typing import Dict, List, Optional, Tuple
from google import genai
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """Service to handle LLM calls with Google Gemini"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        print(f"Initialized Google Gemini model: {self.model_name}")

    @staticmethod
    def _first_name_from_username(username: str) -> str:
        return (username or "User").strip().split()[0] if (username or "").strip() else "User"

    async def classify_message(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Classify a message into exactly one of:
        SOCIAL | PDF_QUESTION | OUT_OF_SCOPE
        """
        import re

        safe_message = (user_message or "").replace('"', '\\"').strip()

        history_block_lines: List[str] = []
        if history:
            # Only include a small amount of recent context for better reference resolution.
            for msg in history[-4:]:
                role = (msg.get("role", "") or "").strip().lower()
                content = (msg.get("content", "") or "").strip()
                if not content:
                    continue
                history_block_lines.append(f"{role.capitalize()}: {content}")

        history_block = "\n".join(history_block_lines) if history_block_lines else "(no recent history)"
        full_prompt = f"""
You are a message classifier for a PDF document assistant.

Classify the user's message into EXACTLY ONE of these three categories:

SOCIAL
- Greetings: hi, hello, hey, good morning, good evening, hii, heyy, etc.
- Farewells: bye, goodbye, see you, take care, etc.
- Gratitude: thanks, thank you, appreciate it, etc.
- Status questions: how are you, what's up, how's it going, etc.
- General small talk with no document intent

PDF_QUESTION
- Any question or request about document content
- Summaries, explanations, comparisons from the document
- Questions that reference "this document", "the PDF", specific topics likely in a PDF
- Mixed messages that contain BOTH document-related parts AND unrelated real-world facts
- Follow-up references (like "the 4th point", "previous item", "it") that depend on earlier PDF discussion

OUT_OF_SCOPE
- Questions about real-world facts not related to any document
- Questions about people, places, events, general knowledge
- Anything that requires external knowledge beyond small talk

Respond with ONLY the category word. Nothing else. No punctuation. No explanation.

If you are uncertain between PDF_QUESTION and SOCIAL, choose PDF_QUESTION.
If you are uncertain between PDF_QUESTION and OUT_OF_SCOPE, choose PDF_QUESTION.
When in doubt, lean toward PDF_QUESTION.

Conversation history (may include references like "4th point"):
{history_block}

User message: "{safe_message}"
""".strip()

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )

            raw = (response.text or "").strip()
            first_line = raw.splitlines()[0].strip().upper() if raw else ""
            category = re.sub(r"[^A-Z_]", "", first_line)
            if category not in {"SOCIAL", "PDF_QUESTION", "OUT_OF_SCOPE"}:
                category = "PDF_QUESTION"  # safe default
            return category
        except Exception:
            return "PDF_QUESTION"

    async def rewrite_search_query(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Rewrite follow-up questions into a self-contained PDF search query.

        This is used to improve RAG retrieval for references like "the 4th point"
        or pronouns like "it/that/this" that depend on prior conversation context.
        """
        history_lines: List[str] = []
        if history:
            for msg in history[-6:]:
                role = (msg.get("role", "") or "").strip().lower()
                content = (msg.get("content", "") or "").strip()
                if not content:
                    continue
                history_lines.append(f"{role.capitalize()}: {content}")

        history_block = "\n".join(history_lines) if history_lines else "(no recent history)"
        safe_message = (user_message or "").replace('"', '\\"').strip()

        full_prompt = f"""
You rewrite the user's message into a self-contained search query for retrieving relevant passages from an uploaded PDF.

Rules:
- Use the conversation history to resolve references and pronouns ("it", "that", "this", "previous answer", "4th point", etc.).
- Replace references with their actual meaning from history.
- Include ONLY the document-related part (omit any unrelated real-world/fact questions).
- Output ONLY the rewritten query text. No quotes. No extra sentences.

Conversation history:
{history_block}

User message:
{safe_message}
""".strip()

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            rewritten = (response.text or "").strip().strip('"').strip()
            return rewritten or safe_message
        except Exception:
            return safe_message

    async def generate_social_response(self, user_message: str, username: str = "User") -> str:
        """
        Warm, conversational response for SOCIAL messages.
        """
        first_name = self._first_name_from_username(username)
        safe_message = (user_message or "").strip()

        full_prompt = f"""
You are a warm, friendly PDF document assistant.
The user's first name is: {first_name}

The user sent you a casual social message. Respond warmly and naturally.
Rules:
- Use their first name once if it fits naturally
- Keep response to 1-2 sentences maximum
- End by inviting them to ask about their uploaded document
- Match their energy (morning greeting -> morning reply, bye -> farewell, thanks -> you're welcome)
- Never mention PDFs robotically - keep it conversational

User message: "{safe_message}"
""".strip()

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
        )
        return (response.text or "").strip()
    
    async def generate_response(
        self,
        prompt: str,
        context: str,
        username: str = "User",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, bool]:
        """
        Generate a PDF-grounded response (PDF_QUESTION path only).

        Returns: (answer, is_relevant) where is_relevant indicates if the answer
        is based on the provided PDF context (used for showing references).
        """

        # Check if user requested specific word count
        import re

        word_count_match = re.search(r"in (\d+) words?", prompt.lower())
        word_constraint = ""
        if word_count_match:
            word_count = word_count_match.group(1)
            word_constraint = (
                f"\n\nIMPORTANT: Your answer MUST be approximately {word_count} words. "
                f"Be concise and precise."
            )

        first_name = self._first_name_from_username(username)

        # Must be returned exactly (no extra punctuation/whitespace) when
        # the requested information is not present in the provided PDF context.
        refusal_message = (
            "I can only answer questions based on the uploaded PDF. "
            "This information is not in your document."
        )

        history_block_lines: List[str] = []
        if history:
            for msg in history[-6:]:
                role = (msg.get("role", "") or "").strip().lower()
                content = (msg.get("content", "") or "").strip()
                if not content:
                    continue
                history_block_lines.append(f"{role.capitalize()}: {content}")

        history_block = (
            "\n".join(history_block_lines) if history_block_lines else "(no previous exchanges)"
        )

        context = context or ""
        context_block = context.strip() if context.strip() else "(no PDF context provided)"

        formatting_instructions = """
Response style:
- For summaries or "key points", use short numbered points (1., 2., 3., ...).
- Keep bullets/points short; avoid long paragraphs.
"""

        full_prompt = f"""
You are a helpful, warm PDF document assistant.
Primary purpose: help users understand and extract information from their uploaded PDFs.

STRICT PDF RULES (Always follow):
- ONLY use the provided PDF context and conversation history.
- Never use your training knowledge or any external/world knowledge.
- If PDF context is empty OR the document-related part of the request is not supported by the provided PDF context,
  you MUST respond with EXACTLY:
  {refusal_message}

Mixed message rule:
If the user's message contains BOTH document-related questions AND non-document part (social or real-world facts),
answer ONLY the document-related part using the PDF context rules above.
For the non-document part, include exactly one short sentence explaining you cannot answer that part without the document context.

The user's first name is: {first_name}

Conversation history:
{history_block}

PDF context:
{context_block}

Current user message:
{prompt}

{formatting_instructions}

CRITICAL CONSTRAINT: Your answer MUST be no more than 150 words.
{word_constraint}
""".strip()
        try:
            print(f"Calling Google Gemini API with model: {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            
            answer = response.text
            print(f"Gemini response received: {answer[:100]}...")
            
            answer_text = (answer or "").strip()

            if answer_text == refusal_message:
                return answer_text, False

            # Defensive heuristic: if the model drifts away from the exact refusal,
            # don't attach references.
            lower = answer_text.lower()
            is_relevant = not (
                "cannot find" in lower
                or "not in the" in lower
                or "no information" in lower
            )
            return answer_text, is_relevant
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            msg = str(e).lower()
            if "429" in msg or "resource_exhausted" in msg:
                return (
                    "I'm temporarily rate-limited. Please try again in a few seconds.",
                    False,
                )
            return (
                "I apologize, but I'm unable to generate a response at the moment. Please try again shortly.",
                False,
            )


llm_service = LLMService()

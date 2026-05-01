import os
import random
import asyncio
import time
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv
from logger_config import setup_logger, PerformanceTimer

load_dotenv()

logger = setup_logger(__name__)

class LLMService:
    """Service to handle LLM calls with Google Gemini or Ollama with multiple API key support"""
    
    def __init__(self):
        """Initialize LLM service with either Ollama or Google Gemini based on USE_OLLAMA flag"""
        self.use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # Default 5 minutes
        
        if self.use_ollama:
            # Initialize Ollama
            try:
                import ollama
                self.ollama_client = ollama
                self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                self.model_name = os.getenv("OLLAMA_MODEL", "qwen3-vl:4b")
                
                # Test connection
                try:
                    ollama.list()
                except Exception as conn_error:
                    raise ConnectionError(
                        f"❌ Cannot connect to Ollama at {self.ollama_base_url}. "
                        f"Make sure Ollama is running. Error: {conn_error}\n"
                        f"See OLLAMA_SETUP_GUIDE.md for installation instructions."
                    )
                
                logger.info(f"Initialized Ollama model: {self.model_name}")
                logger.info(f"Ollama URL: {self.ollama_base_url}")
                logger.info(f"Ollama timeout: {self.ollama_timeout}s")
            except ImportError:
                raise ImportError(
                    "❌ Ollama library not installed. Install it with: pip install ollama"
                )
        else:
            # Initialize Google Gemini
            # Load all available Google API keys
            self.api_keys = self._load_api_keys()
            if not self.api_keys:
                raise ValueError("No GOOGLE_API_KEY found in environment variables")
            
            # Initialize with first key
            self.current_key_index = 0
            genai.configure(api_key=self.api_keys[self.current_key_index])
            # Use stable Gemini model
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            
            logger.info(f"Initialized Google Gemini model: {self.model_name}")
            logger.info(f"Loaded {len(self.api_keys)} API key(s)")
    
    def _load_api_keys(self) -> List[str]:
        """Load all Google API keys from environment (GOOGLE_API_KEY, GOOGLE_API_KEY1, etc.)"""
        keys = []
        
        # Try GOOGLE_API_KEY first
        main_key = os.getenv("GOOGLE_API_KEY")
        if main_key:
            keys.append(main_key)
        
        # Try numbered keys (GOOGLE_API_KEY1, GOOGLE_API_KEY2, etc.)
        i = 1
        while True:
            key = os.getenv(f"GOOGLE_API_KEY{i}")
            if not key:
                break
            keys.append(key)
            i += 1
        
        return keys
    
    def _get_random_api_key(self) -> str:
        """Select random API key from pool for load distribution"""
        return random.choice(self.api_keys)
    
    def _switch_to_next_key(self) -> bool:
        """Rotate to next API key on quota exhaustion, returns True if successful"""
        if len(self.api_keys) <= 1:
            return False
        
        # Try next key
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_index]
        
        try:
            genai.configure(api_key=new_key)
            logger.info(f"Switched to API key #{self.current_key_index + 1}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch API key: {e}")
            return False
    
    def _make_api_call_with_retry(self, api_call_func, max_retries: int = None):
        """Execute API call with automatic retry and key rotation on quota/rate limit errors"""
        # For Ollama, no retry logic needed (no quota limits)
        if self.use_ollama:
            return api_call_func()
        
        # For Gemini, use retry logic
        if max_retries is None:
            max_retries = len(self.api_keys)
        
        last_error = None
        attempts = 0
        
        while attempts < max_retries:
            try:
                return api_call_func()
            except Exception as e:
                error_str = str(e)
                attempts += 1
                
                # Check if it's a quota/rate limit error
                is_quota_error = any(keyword in error_str for keyword in [
                    "RESOURCE_EXHAUSTED",
                    "429",
                    "quota",
                    "rate limit",
                    "Too Many Requests"
                ])
                
                is_unavailable = "503" in error_str or "UNAVAILABLE" in error_str
                
                if (is_quota_error or is_unavailable) and attempts < max_retries:
                    logger.warning(f"API key #{self.current_key_index + 1} quota/limit reached, trying next key...")
                    if self._switch_to_next_key():
                        continue
                    else:
                        logger.error("No more API keys available to try")
                        last_error = e
                        break
                else:
                    # Not a quota error or no more retries
                    last_error = e
                    break
        
        # If we get here, all retries failed
        if last_error:
            raise last_error
        else:
            raise Exception("API call failed after all retries")

    @staticmethod
    def _first_name_from_username(username: str) -> str:
        """Extract first name from username for personalized responses"""
        return (username or "User").strip().split()[0] if (username or "").strip() else "User"

    def _call_llm(self, prompt: str) -> str:
        """Call LLM (Ollama or Gemini) with the given prompt"""
        provider = "Ollama" if self.use_ollama else "Gemini"
        logger.info(f"🤖 Calling {provider} LLM: {self.model_name}")
        
        if self.use_ollama:
            # Call Ollama
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt
            )
            logger.info(f"✅ {provider} response received ({len(response['response'])} chars)")
            return response['response']
        else:
            # Call Gemini
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            logger.info(f"✅ {provider} response received ({len(response.text)} chars)")
            return response.text
    
    def _call_llm_stream(self, prompt: str):
        """Call LLM with streaming support (yields chunks of text)"""
        provider = "Ollama" if self.use_ollama else "Gemini"
        logger.info(f"🤖 Calling {provider} LLM (STREAMING): {self.model_name}")
        
        if self.use_ollama:
            import time
            start_time = time.time()
            timeout = self.ollama_timeout
            
            try:
                stream = self.ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    stream=True,
                    options={
                        "num_predict": 200,  # Limit tokens for speed
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_ctx": 2048,  # Smaller context for speed
                    }
                )
                
                for chunk in stream:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        logger.error(f"⏱️ Ollama timeout after {timeout}s")
                        yield "\n\n[Response timeout - the model is taking too long. Please try a shorter question or use Gemini instead.]"
                        break
                    
                    if 'response' in chunk:
                        text = chunk['response']
                        # Skip empty chunks (Ollama bug)
                        if text:
                            yield text
                        
            except Exception as e:
                logger.error(f"Ollama streaming error: {e}")
                yield f"\n\n[Error: {str(e)}]"
        else:
            # Call Gemini with streaming
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text

    async def classify_message(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Classify message as SOCIAL, PDF_QUESTION, or OUT_OF_SCOPE (legacy method, use classify_and_process)"""
        result = await self.classify_and_process(user_message, history, username="User")
        return result["classification"]

    async def classify_and_process(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        username: str = "User",
    ) -> Dict[str, str]:
        """Classify message and generate response/query in single API call for performance optimization"""
        import re

        # FAST PATH FOR OLLAMA: Skip classification (too slow), assume PDF_QUESTION
        if self.use_ollama:
            logger.info(f"⚡ Ollama fast path: Skipping classification (assuming PDF_QUESTION)")
            return {
                "classification": "PDF_QUESTION",
                "social_response": None,
                "rewritten_query": user_message,
            }

        safe_message = (user_message or "").replace('"', '\\"').strip()
        first_name = self._first_name_from_username(username)

        history_block_lines: List[str] = []
        if history:
            for msg in history[-6:]:  # Use last 6 for full context
                role = (msg.get("role", "") or "").strip().lower()
                content = (msg.get("content", "") or "").strip()
                if not content:
                    continue
                history_block_lines.append(f"{role.capitalize()}: {content}")

        history_block = "\n".join(history_block_lines) if history_block_lines else "(no recent history)"
        
        full_prompt = f"""
You are a smart PDF document assistant. Your task is to classify the user's message AND prepare the appropriate response/query in ONE step.

STEP 1: Classify the message into ONE category:

SOCIAL
- Greetings: hi, hello, hey, good morning, good evening, hii, heyy, heyyy, etc.
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

STEP 2: Based on classification, provide the appropriate output:

If SOCIAL:
- Generate a UNIQUE, DYNAMIC, warm, friendly 1-2 sentence response
- Use the user's first name ({first_name}) naturally if it fits
- Match their energy and tone exactly:
  * "hi" or "hello" → warm greeting back
  * "heyy" or "heyyy" → casual, friendly greeting
  * "thanks" → you're welcome message
  * "bye" → friendly farewell
  * "how are you" → brief status + offer help
- End by naturally inviting them to ask about their document
- NEVER use generic templates - make each response feel personal and contextual
- Consider conversation history to make response feel natural

If PDF_QUESTION:
- Rewrite the query to be self-contained for vector search (5-15 words)
- Resolve any pronouns or references using conversation history
- If already self-contained, return it unchanged

If OUT_OF_SCOPE:
- No additional processing needed

OUTPUT FORMAT (respond with EXACTLY this structure):
CLASSIFICATION: [SOCIAL|PDF_QUESTION|OUT_OF_SCOPE]
RESPONSE: [your dynamic response here - only for SOCIAL, must be unique and contextual]
QUERY: [rewritten query here - only for PDF_QUESTION]

IMPORTANT FOR SOCIAL RESPONSES:
- DO NOT use generic phrases like "How can I help you with your document?"
- DO create unique responses based on the specific greeting/message
- DO match the user's energy level (casual vs formal)
- DO reference conversation history if relevant
- DO make it feel like a real conversation, not a bot

Examples of GOOD dynamic social responses:
User: "heyy" → RESPONSE: Hey {first_name}! Great to see you. What would you like to explore in your PDF today?
User: "heyyy whats up" → RESPONSE: Hey there! Not much, just ready to help you dive into your document. What's on your mind?
User: "thanks" → RESPONSE: You're very welcome, {first_name}! Let me know if you need anything else from your PDF.
User: "good morning" → RESPONSE: Good morning, {first_name}! Hope you're having a great day. Ready to work on your document?
User: "bye" → RESPONSE: Take care, {first_name}! Come back anytime you need help with your documents.

Conversation history:
{history_block}

User message: "{safe_message}"
""".strip()

        try:
            logger.info(f"Classifying message: {safe_message[:80]}...")
            logger.info(f"History context: {len(history_block_lines)} messages")
            
            # Use retry mechanism for API call
            def api_call():
                return self._call_llm(full_prompt)
            
            raw = self._make_api_call_with_retry(api_call)
            raw = (raw or "").strip()
            logger.debug(f"LLM raw response: {raw[:200]}...")
            
            # Parse the structured response
            classification = "PDF_QUESTION"  # default
            social_response = None
            rewritten_query = None
            
            # Parse line by line
            lines = raw.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("CLASSIFICATION:"):
                    cat = line.replace("CLASSIFICATION:", "").strip().upper()
                    cat = re.sub(r"[^A-Z_]", "", cat)
                    if cat in {"SOCIAL", "PDF_QUESTION", "OUT_OF_SCOPE"}:
                        classification = cat
                elif line.startswith("RESPONSE:"):
                    # Get everything after "RESPONSE:" including multi-line responses
                    response_text = line.replace("RESPONSE:", "").strip()
                    # Check if response continues on next lines (not starting with CLASSIFICATION/QUERY)
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if next_line.startswith("CLASSIFICATION:") or next_line.startswith("QUERY:"):
                            break
                        if next_line:
                            response_text += " " + next_line
                    social_response = response_text
                elif line.startswith("QUERY:"):
                    # Get everything after "QUERY:"
                    query_text = line.replace("QUERY:", "").strip()
                    # Check if query continues on next lines
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if next_line.startswith("CLASSIFICATION:") or next_line.startswith("RESPONSE:"):
                            break
                        if next_line:
                            query_text += " " + next_line
                    rewritten_query = query_text
            
            # Fallback: if no structured output, try to extract from raw response
            if not social_response and not rewritten_query:
                # Try to find classification in first line
                first_line = raw.splitlines()[0].strip().upper() if raw else ""
                if any(word in first_line for word in ["SOCIAL", "PDF", "SCOPE"]):
                    classification = re.sub(r"[^A-Z_]", "", first_line)
                    if classification not in {"SOCIAL", "PDF_QUESTION", "OUT_OF_SCOPE"}:
                        classification = "PDF_QUESTION"
                
                # If still no response/query, use the rest of the text
                remaining_text = "\n".join(raw.splitlines()[1:]).strip() if len(raw.splitlines()) > 1 else ""
                if classification == "SOCIAL" and remaining_text:
                    social_response = remaining_text
                elif classification == "PDF_QUESTION" and remaining_text:
                    rewritten_query = remaining_text
            
            # Final fallback: if classification is SOCIAL but no response, call separate method
            if classification == "SOCIAL" and not social_response:
                logger.warning("LLM didn't provide social response, calling separate method")
                social_response = await self.generate_social_response(user_message, username)
            
            # Final fallback: if classification is PDF_QUESTION but no query, use original
            if classification == "PDF_QUESTION" and not rewritten_query:
                logger.warning("LLM didn't provide rewritten query, using original message")
                rewritten_query = user_message
            
            # Log the final result
            logger.info(f"Classification result: {classification}")
            if classification == "SOCIAL" and social_response:
                logger.info(f"Social response: {social_response[:80]}...")
            elif classification == "PDF_QUESTION" and rewritten_query:
                logger.info(f"Rewritten query: {rewritten_query}")
            
            return {
                "classification": classification,
                "social_response": social_response,
                "rewritten_query": rewritten_query,
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}", exc_info=True)
            # Safe fallback
            return {
                "classification": "PDF_QUESTION",
                "social_response": None,
                "rewritten_query": user_message,
            }

    async def rewrite_search_query(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Rewrite user query to be self-contained using conversation history (legacy, use classify_and_process)"""
        history_lines: List[str] = []
        if history:
            for msg in history[-6:]:
                role = (msg.get("role", "") or "").strip().lower()
                content = (msg.get("content", "") or "").strip()
                if not content:
                    continue
                label = "User" if role == "user" else "Assistant"
                history_lines.append(f"{label}: {content}")

        last_3_turns_formatted = (
            "\n".join(history_lines) if history_lines else "(no recent history)"
        )
        raw_message = user_message or ""

        full_prompt = f"""
You are a query rewriter for a PDF document assistant.

Your job is to analyze the user's latest message and determine
if it can be used directly as a vector search query, or if it
needs to be rewritten into a self-contained query using context
from the conversation history.

A message NEEDS rewriting if it contains ANY of these:
- References to numbered items from a previous response
  ("the 4th point", "first one", "last topic", "second item")
- Pronouns referring to something discussed earlier
  ("it", "that", "this", "they", "those")
- Relative references to prior conversation
  ("what you said", "previous answer", "that concept", "earlier")
- Continuation requests with no stated topic
  ("elaborate", "go deeper", "give an example", "expand", "more details")
- Any message that CANNOT be understood without reading the history

A message does NOT need rewriting if:
- It is completely self-contained and specific
- It is a social/casual message (greeting, thanks, bye)
- It clearly states a topic without referencing prior context

Conversation history (most recent last):
{last_3_turns_formatted}

Current user message:
{raw_message}

Instructions:
- If the message needs rewriting: output ONLY the rewritten
  self-contained query (5-15 words, no explanation)
- If the message does NOT need rewriting: output ONLY the
  original message unchanged
- Never output anything except the query itself
- Never explain your decision
- Never add prefixes like "Rewritten:" or "Query:"
""".strip()

        try:
            def api_call():
                return self._call_llm(full_prompt)
            
            llm_out = self._make_api_call_with_retry(api_call)
            llm_out = (llm_out or "").strip()
            if llm_out == raw_message.strip():
                return raw_message
            return llm_out if llm_out else raw_message
        except Exception:
            return raw_message

    async def generate_social_response(self, user_message: str, username: str = "User") -> str:
        """Generate warm, personalized response for social messages like greetings and thanks"""
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

        def api_call():
            return self._call_llm(full_prompt)
        
        response_text = self._make_api_call_with_retry(api_call)
        return (response_text or "").strip()
    
    async def generate_response(
        self,
        prompt: str,
        context: str,
        username: str = "User",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, bool]:
        """Generate PDF-grounded answer using RAG context, returns (answer, is_relevant) tuple"""

        # Check if user requested specific word count
        import re

        word_count_match = re.search(r"in (\d+) words?", prompt.lower())
        requested_words = int(word_count_match.group(1)) if word_count_match else None
        prompt_lower = (prompt or "").lower()
        long_form_intent = any(
            k in prompt_lower
            for k in (
                "summarize",
                "summary",
                "explain",
                "point wise",
                "point-wise",
                "key points",
                "elaborate",
                "detailed",
                "in detail",
            )
        )

        # Dynamic response cap:
        # - Long-form intents need more room than strict 150 words.
        # - Explicit large word requests get a larger cap buffer.
        max_word_cap = 150
        if long_form_intent:
            max_word_cap = 400
        if requested_words:
            max_word_cap = max(max_word_cap, min(requested_words + 75, 600))

        word_constraint = ""
        if requested_words:
            word_constraint = (
                f"\n\nIMPORTANT: Your answer MUST be approximately {requested_words} words. "
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

CRITICAL CONSTRAINT: Your answer MUST be no more than {max_word_cap} words.
{word_constraint}
""".strip()
        try:
            provider = "Ollama" if self.use_ollama else "Gemini"
            logger.info(f"{'='*80}")
            logger.info(f"🤖 GENERATING ANSWER WITH {provider.upper()}")
            logger.info(f"{'='*80}")
            logger.info(f"📝 Query: {prompt[:100]}...")
            logger.info(f"📄 Context length: {len(context)} chars")
            logger.info(f"💬 History: {len(history) if history else 0} messages")
            logger.info(f"🎯 Model: {self.model_name}")
            logger.info(f"{'='*80}")
            
            def api_call():
                return self._call_llm(full_prompt)
            
            answer = self._make_api_call_with_retry(api_call)
            
            answer_text = (answer or "").strip()
            
            logger.info(f"{'='*80}")
            logger.info(f"✅ ANSWER GENERATED SUCCESSFULLY")
            logger.info(f"{'='*80}")
            logger.info(f"📊 Answer length: {len(answer_text)} chars ({len(answer_text.split())} words)")
            logger.info(f"🤖 Provider: {provider}")
            logger.info(f"{'='*80}")

            if answer_text == refusal_message:
                return answer_text, False

            return answer_text, True
            
        except Exception as e:
            logger.error(f"{'='*80}")
            logger.error(f"❌ LLM API ERROR")
            logger.error(f"{'='*80}")
            logger.error(f"Provider: {provider}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"{'='*80}", exc_info=True)
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
    
    async def generate_response_stream(
        self,
        prompt: str,
        context: str,
        username: str = "User",
        history: Optional[List[Dict[str, str]]] = None,
    ):
        """Generate PDF-grounded answer using RAG context with streaming support (yields text chunks)"""
        import re

        word_count_match = re.search(r"in (\d+) words?", prompt.lower())
        requested_words = int(word_count_match.group(1)) if word_count_match else None
        prompt_lower = (prompt or "").lower()
        long_form_intent = any(
            k in prompt_lower
            for k in (
                "summarize",
                "summary",
                "explain",
                "point wise",
                "point-wise",
                "key points",
                "elaborate",
                "detailed",
                "in detail",
            )
        )

        max_word_cap = 150
        if long_form_intent:
            max_word_cap = 400
        if requested_words:
            max_word_cap = max(max_word_cap, min(requested_words + 75, 600))

        word_constraint = ""
        if requested_words:
            word_constraint = (
                f"\n\nIMPORTANT: Your answer MUST be approximately {requested_words} words. "
                f"Be concise and precise."
            )

        first_name = self._first_name_from_username(username)

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

        # MODIFIED: Two-step approach - first get thinking, then get answer
        # Step 1: Get thinking only
        thinking_only_prompt = f"""You are analyzing a user's question about a PDF document.

USER QUESTION: {prompt}

Write ONLY your internal reasoning (1-2 sentences) about how you will answer this question based on the PDF context below. Do NOT write the actual answer yet.

PDF CONTEXT:
{context_block}

YOUR REASONING (1-2 sentences only):""".strip()

        # Step 2: Get answer with the thinking prepended
        full_prompt = f"""You are a PDF assistant helping {first_name}.

IMPORTANT: Provide ONLY the answer to the user's question. Do NOT repeat your reasoning.

PDF CONTEXT:
{context_block}

USER QUESTION: {prompt}

RULES:
- ONLY use the PDF context above
- If info not in PDF: "{refusal_message}"
- Max {max_word_cap} words
- Use numbered points for summaries

YOUR ANSWER:""".strip()
        
        try:
            provider = "Ollama" if self.use_ollama else "Gemini"
            logger.info(f"{'='*80}")
            logger.info(f"🤖 STREAMING ANSWER WITH {provider.upper()}")
            logger.info(f"{'='*80}")
            logger.info(f"📝 Query: {prompt[:100]}...")
            logger.info(f"📄 Context length: {len(context)} chars")
            logger.info(f"💬 History: {len(history) if history else 0} messages")
            logger.info(f"🎯 Model: {self.model_name}")
            logger.info(f"⚡ Mode: STREAMING (real-time with thinking)")
            logger.info(f"{'='*80}")
            
            # Two-step streaming: First thinking, then answer
            provider = "Ollama" if self.use_ollama else "Gemini"
            logger.info(f"{'='*80}")
            logger.info(f"🤖 STREAMING ANSWER WITH {provider.upper()} (TWO-STEP)")
            logger.info(f"{'='*80}")
            logger.info(f"📝 Query: {prompt[:100]}...")
            logger.info(f"📄 Context length: {len(context)} chars")
            logger.info(f"💬 History: {len(history) if history else 0} messages")
            logger.info(f"🎯 Model: {self.model_name}")
            logger.info(f"⚡ Mode: STREAMING ({'single-step' if self.use_ollama else 'two-step'})")
            logger.info(f"{'='*80}")
            
            # Send status
            yield "<<<STATUS>>>🧠 Generating response..."
            
            if self.use_ollama:
                # OLLAMA: Single-step - thinking + answer in one call with structured format
                logger.info("🧠 Streaming thinking + answer from Ollama (single call)...")
                
                # Prompt that instructs the model to output thinking and answer in a structured way
                structured_prompt = f"""You are a helpful PDF assistant for {first_name}.

PDF CONTEXT:
{context_block}

USER QUESTION: {prompt}

INSTRUCTIONS:
1. First, write your thinking process inside [THINKING] tags
2. Then, write your final answer inside [ANSWER] tags
3. Keep total response under {max_word_cap} words

Format:
[THINKING]
Your reasoning here...
[/THINKING]

[ANSWER]
Your answer here...
[/ANSWER]

Response:""".strip()
                
                # Stream and parse the structured output
                buffer = ""
                in_thinking = False
                in_answer = False
                thinking_started = False
                answer_started = False
                
                for chunk in self._call_llm_stream(structured_prompt):
                    buffer += chunk
                    
                    # Check for [THINKING] tag
                    if "[THINKING]" in buffer and not thinking_started:
                        thinking_started = True
                        in_thinking = True
                        yield "<<<THINKING_START>>>"
                        # Remove everything before and including [THINKING]
                        buffer = buffer.split("[THINKING]", 1)[1]
                    
                    # Check for [/THINKING] tag
                    if "[/THINKING]" in buffer and in_thinking:
                        # Send remaining thinking text before the tag
                        thinking_part = buffer.split("[/THINKING]", 1)[0]
                        if thinking_part:  # Don't strip - preserve spaces
                            yield thinking_part
                        yield "<<<THINKING_END>>>"
                        in_thinking = False
                        buffer = buffer.split("[/THINKING]", 1)[1]
                        continue
                    
                    # Check for [ANSWER] tag
                    if "[ANSWER]" in buffer and not answer_started:
                        answer_started = True
                        in_answer = True
                        yield "<<<STATUS>>>✍️ Generating answer..."
                        yield "<<<ANSWER_START>>>"
                        # Remove everything before and including [ANSWER]
                        buffer = buffer.split("[ANSWER]", 1)[1]
                    
                    # Check for [/ANSWER] tag
                    if "[/ANSWER]" in buffer and in_answer:
                        # Send remaining answer text before the tag
                        answer_part = buffer.split("[/ANSWER]", 1)[0]
                        if answer_part:  # Don't strip - preserve spaces
                            yield answer_part
                        in_answer = False
                        break
                    
                    # Stream content when we have enough in buffer (word by word)
                    if (in_thinking or in_answer) and " " in buffer:
                        # Find last space to get complete words
                        last_space = buffer.rfind(" ")
                        if last_space > 0:
                            words_to_send = buffer[:last_space + 1]  # Include the space
                            buffer = buffer[last_space + 1:]
                            if words_to_send:  # Don't strip - preserve spaces!
                                yield words_to_send
                
                # Send any remaining buffer content (preserve trailing space if exists)
                if buffer and (in_thinking or in_answer):
                    yield buffer
                
                # Ensure markers are sent even if tags weren't found
                if thinking_started and in_thinking:
                    yield "<<<THINKING_END>>>"
                if not answer_started:
                    yield "<<<STATUS>>>✍️ Generating answer..."
                    yield "<<<ANSWER_START>>>"
                        
            else:
                # GEMINI: Two-step approach (works better for Gemini)
                yield "<<<THINKING_START>>>"
                try:
                    def thinking_call():
                        return self._call_llm(thinking_only_prompt)
                    
                    thinking_text = self._make_api_call_with_retry(thinking_call)
                    thinking_text = (thinking_text or "").strip()
                    
                    # Stream thinking word by word
                    words = thinking_text.split()
                    buffer = []
                    for i, word in enumerate(words):
                        buffer.append(word)
                        if len(buffer) >= 4 or i == len(words) - 1:
                            yield " ".join(buffer) + " "
                            buffer = []
                            await asyncio.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Error getting thinking: {e}")
                    yield "Analyzing your question... "
                
                yield "<<<THINKING_END>>>"
                yield "<<<ANSWER_START>>>"
                
                for chunk in self._call_llm_stream(full_prompt):
                    yield chunk
            
            logger.info(f"{'='*80}")
            logger.info(f"✅ STREAMING COMPLETE")
            logger.info(f"🤖 Provider: {provider}")
            logger.info(f"{'='*80}")
            
        except Exception as e:
            logger.error(f"{'='*80}")
            logger.error(f"❌ STREAMING ERROR")
            logger.error(f"{'='*80}")
            logger.error(f"Provider: {provider if 'provider' in locals() else 'Unknown'}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"{'='*80}", exc_info=True)
            msg = str(e).lower()
            if "429" in msg or "resource_exhausted" in msg:
                yield "I'm temporarily rate-limited. Please try again in a few seconds."
            else:
                yield "I apologize, but I'm unable to generate a response at the moment. Please try again shortly."


    async def generate_read_mode_response(
        self,
        prompt: str,
        context: Dict[str, str],
        username: str = "User",
    ) -> str:
        """Generate answer for Read Mode using selected text and page context without vector search"""
        from services.read_mode_service import read_mode_service
        
        full_prompt = read_mode_service.format_read_mode_prompt(
            question=prompt,
            context=context,
            username=username
        )
        
        try:
            logger.info(f"Generating Read Mode answer for query: {prompt[:80]}...")
            logger.info(f"Context - Selected: {len(context.get('selected_text', ''))} chars, "
                       f"Page: {len(context.get('page_text', ''))} chars")
            
            def api_call():
                return self._call_llm(full_prompt)
            
            answer_text = self._make_api_call_with_retry(api_call)
            answer_text = (answer_text or "").strip()
            
            logger.info(f"Read Mode answer generated: {len(answer_text)} chars")
            logger.debug(f"Answer preview: {answer_text[:150]}...")
            
            return answer_text
            
        except Exception as e:
            logger.error(f"LLM API error in Read Mode: {e}", exc_info=True)
            msg = str(e).lower()
            if "429" in msg or "resource_exhausted" in msg:
                return "I'm temporarily rate-limited. Please try again in a few seconds."
            return "I apologize, but I'm unable to generate a response at the moment. Please try again shortly."


llm_service = LLMService()

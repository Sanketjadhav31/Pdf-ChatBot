import os
from typing import Optional
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
    
    async def generate_response(self, prompt: str, context: str) -> tuple[str, bool]:
        """Generate response using Google Gemini.

        Returns: (answer, is_relevant) where is_relevant indicates if answer uses the context.
        The answer is formatted as clear bullet/numbered points when appropriate.
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

        formatting_instructions = """
Answer in a structured, easy-to-read way:
- For summaries or \"key points\", respond as short numbered points (1., 2., 3., ...).
- If the user explicitly asks for more detailed points, you may nest sub-points as (a), (b), (c) under each number.
- Keep each point focused and avoid long paragraphs.
- Only answer using information that is clearly supported by the context.
"""

        full_prompt = f"""You are a PDF chatbot. Based ONLY on the context below, answer the user's question.

Context from PDF:
{context}

User question:
{prompt}

{formatting_instructions}
{word_constraint}
"""
        try:
            print(f"Calling Google Gemini API with model: {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            
            answer = response.text
            print(f"Gemini response received: {answer[:100]}...")
            
            is_relevant = not ("cannot find" in answer.lower() or "not in the" in answer.lower() or "no information" in answer.lower())
            return answer, is_relevant
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            return f"I apologize, but I'm unable to generate a response at the moment. Error: {str(e)}", False


llm_service = LLMService()

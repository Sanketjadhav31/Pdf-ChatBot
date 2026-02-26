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
        """Generate response using Google Gemini
        Returns: (answer, is_relevant) where is_relevant indicates if answer uses the context
        """
        
        # Check if user requested specific word count
        import re
        word_count_match = re.search(r'in (\d+) words?', prompt.lower())
        word_constraint = ""
        if word_count_match:
            word_count = word_count_match.group(1)
            word_constraint = f"\n\nIMPORTANT: Your answer MUST be approximately {word_count} words. Be concise and precise."
        
        full_prompt = f"""Based on the following context from the PDF document, answer the question accurately.

Context from PDF:
{context}

Question: {prompt}{word_constraint}

IMPORTANT INSTRUCTIONS:
1. If the context contains relevant information to answer the question, provide a clear answer with specific references to page numbers.
2. If the context does NOT contain relevant information to answer the question, respond with: "I cannot find relevant information about this in the uploaded documents."
3. Do NOT make up information or answer from general knowledge if it's not in the context.
4. Only answer based on what's explicitly stated in the provided context."""
        
        try:
            print(f"Calling Google Gemini API with model: {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,  # Use the full model name with 'models/' prefix
                contents=full_prompt
            )
            
            answer = response.text
            print(f"Gemini response received: {answer[:100]}...")
            
            is_relevant = not ("cannot find" in answer.lower() or "not in the" in answer.lower() or "no information" in answer.lower())
            return answer, is_relevant
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            return f"I apologize, but I'm unable to generate a response at the moment. Error: {str(e)}", False


llm_service = LLMService()

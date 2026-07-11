from __future__ import annotations

"""
RAG Query Pipeline — Generator Component

Calls the Groq API using the llama-3.3-70b-versatile model to generate answers.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
    GROQ_TEMPERATURE,
    GROQ_MAX_TOKENS,
)


class Generator:
    """Generator class responsible for calling the LLM via Groq."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize ChatGroq instance."""
        key = api_key or GROQ_API_KEY
        if not key:
            raise ValueError("GROQ_API_KEY is missing. Check your configuration or .env file.")
        
        self.chat = ChatGroq(
            groq_api_key=key,
            model_name=GROQ_MODEL_NAME,
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
            max_retries=5,
        )

    def generate(self, system_prompt: str, user_content: str) -> str:
        """Generate response content from system prompt and user query/context.

        Args:
            system_prompt: Guidelines and constraints for the LLM.
            user_content: Context chunks and user query.

        Returns:
            The raw text response from the LLM.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]
        
        try:
            response = self.chat.invoke(messages)
            return str(response.content).strip()
        except Exception as e:
            # Return a clear error indicator to be handled by the postprocessor or orchestrator
            return f"[ERROR] LLM generation failed: {e}"

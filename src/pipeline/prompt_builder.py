from __future__ import annotations

"""
RAG Query Pipeline — Prompt Builder

Constructs the prompt sent to the LLM. Combines the system rules,
the retrieved context passages (including source URL and dates), and the user query.
"""

import tiktoken


class PromptBuilder:
    """Class to construct prompts for LLM query generation."""

    def __init__(self) -> None:
        """Initialize PromptBuilder and tiktoken encoder."""
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoder = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in a string using tiktoken."""
        if self.encoder:
            return len(self.encoder.encode(text))
        return len(text) // 4  # rough fallback

    def build_prompt(self, query: str, chunks: list[dict]) -> tuple[str, str]:
        """Construct prompt parts.

        Args:
            query: The user query string.
            chunks: List of retrieved chunk dicts with 'text' and 'metadata'.

        Returns:
            Tuple of (system_prompt, user_content)
        """
        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            text = chunk["text"]
            meta = chunk["metadata"]
            scheme = meta.get("scheme_name", "Unknown Scheme")
            url = meta.get("source_url", "Unknown URL")
            # Try to get downloaded_at, fallback to ingestion_date
            date_str = meta.get("downloaded_at") or meta.get("ingestion_date") or ""
            # Simple ISO date extraction (YYYY-MM-DD)
            if date_str and len(date_str) >= 10:
                date_str = date_str[:10]
            else:
                date_str = "N/A"

            context_parts.append(
                f"[Source {idx}]\n"
                f"Scheme: {scheme}\n"
                f"URL: {url}\n"
                f"Date: {date_str}\n"
                f"Content: {text}"
            )

        context_str = "\n\n".join(context_parts)

        system_prompt = (
            "You are a facts-only mutual fund FAQ assistant for HDFC AMC schemes.\n\n"
            "RULES:\n"
            "1. Answer ONLY using the provided CONTEXT. Do NOT use prior knowledge or external facts.\n"
            "2. Keep your answer to a MAXIMUM of 3 sentences. Be extremely concise.\n"
            "3. Include EXACTLY ONE source citation URL from the context metadata.\n"
            "4. End every response with: \"Last updated from sources: <date>\"\n"
            "   (Use the 'Date' from the cited source metadata, e.g. YYYY-MM-DD)\n"
            "5. If the context does not contain the answer, say:\n"
            "   \"I don't have enough information to answer this from my sources.\"\n"
            "6. NEVER provide investment advice, opinions, or recommendations.\n"
            "7. NEVER compare fund performance or calculate returns. If asked to compare or calculate, provide the factsheet URL only.\n"
        )

        user_content = (
            f"CONTEXT:\n{context_str}\n\n"
            f"USER QUESTION: {query}"
        )

        return system_prompt, user_content

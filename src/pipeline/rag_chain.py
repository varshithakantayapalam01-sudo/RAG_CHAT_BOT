from __future__ import annotations

"""
RAG Query Pipeline — Orchestrator (RAG Chain)

Wires together Retriever, PromptBuilder, Generator, and PostProcessor
to execute the end-to-end RAG flow.
"""

from src.pipeline.retriever import Retriever
from src.pipeline.prompt_builder import PromptBuilder
from src.pipeline.generator import Generator
from src.pipeline.postprocessor import PostProcessor


class RAGPipeline:
    """Orchestrates the retrieval and generation workflow."""

    def __init__(self) -> None:
        """Initialize all pipeline components and query cache."""
        self.retriever = Retriever()
        self.prompt_builder = PromptBuilder()
        self.generator = Generator()
        self.postprocessor = PostProcessor()
        self._cache: dict[str, dict] = {}
        self._max_cache_size = 128

    def run(self, query: str) -> dict:
        """Run the end-to-end factual QA flow.

        Args:
            query: User's question.

        Returns:
            Structured result dict from PostProcessor.
        """
        # Clean query for uniform cache lookup
        cleaned_query = query.strip().lower()
        if cleaned_query in self._cache:
            return self._cache[cleaned_query]

        # 1. Retrieve candidates
        chunks = self.retriever.retrieve(query)

        # 2. Short-circuit if no relevant passages are found above threshold
        if not chunks:
            result = self.postprocessor.postprocess(
                raw_answer="I don't have enough information to answer this from my sources.",
                retrieved_chunks=[],
            )
            # Cache the fallback answer too
            self._cache_result(cleaned_query, result)
            return result

        # 3. Build Prompt
        system_prompt, user_content = self.prompt_builder.build_prompt(query, chunks)

        # 4. Generate LLM Answer
        raw_answer = self.generator.generate(system_prompt, user_content)

        # 5. Postprocess (Limit sentences, extract citation, inject footer)
        result = self.postprocessor.postprocess(raw_answer, chunks)
        
        self._cache_result(cleaned_query, result)
        return result

    def _cache_result(self, query_key: str, result: dict) -> None:
        """Cache query results and enforce cache size limits."""
        if len(self._cache) >= self._max_cache_size:
            # Simple FIFO eviction: remove the oldest inserted key
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key)
        self._cache[query_key] = result


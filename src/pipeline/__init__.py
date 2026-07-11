"""
Pipeline Package

Modules for the RAG query pipeline: guardrails, retrieval,
prompt building, LLM generation, and post-processing.
"""

from src.pipeline.rag_chain import RAGPipeline

__all__ = ["RAGPipeline"]

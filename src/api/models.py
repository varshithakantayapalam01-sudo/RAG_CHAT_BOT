from __future__ import annotations

"""
API Layer — Pydantic Schemas

Defines request and response validation structures for REST communication.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Pydantic model representing a chat request from the user."""

    query: str = Field(
        ...,
        description="The user's question, limited to 500 characters.",
        max_length=500,
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session identifier for chat history tracking.",
    )


class ChatResponse(BaseModel):
    """Pydantic model representing the response sent back to the user."""

    status: str = Field(
        ...,
        description="Execution status: 'success' or 'refused'.",
    )
    type: str = Field(
        ...,
        description="Response classification: 'factual', 'advisory', 'pii', 'off_topic', or 'profanity'.",
    )
    answer: str = Field(
        ...,
        description="The response content or refusal message.",
    )
    citation: Optional[str] = Field(
        None,
        description="The validated source URL cited in the response (if factual).",
    )
    educational_link: Optional[str] = Field(
        None,
        description="Educational SEBI/AMFI resource link (for advisory refusals).",
    )
    footer: str = Field(
        ...,
        description="A dynamic date footer or static compliance disclaimer.",
    )
    confidence: Optional[float] = Field(
        None,
        description="Optional confidence rating or retrieval distance.",
    )


class VectorStoreStatus(BaseModel):
    """Vector store collection statistics."""

    collection_name: str = Field(..., description="ChromaDB collection name.")
    document_count: int = Field(..., description="Number of indexed chunks.")
    persist_directory: str = Field(..., description="Persistent storage directory.")


class HealthResponse(BaseModel):
    """Pydantic model representing system health and ingestion status."""

    status: str = Field(..., description="System health status: 'healthy' or 'unhealthy'.")
    vectorstore: Optional[VectorStoreStatus] = Field(
        None, description="Vector store collection statistics."
    )
    last_ingestion: Optional[str] = Field(
        None, description="ISO timestamp of the last ingestion pipeline execution."
    )
    last_collected: Optional[str] = Field(
        None, description="ISO timestamp of when scheme sources were last collected."
    )
    error: Optional[str] = Field(None, description="Error detail if system status is unhealthy.")


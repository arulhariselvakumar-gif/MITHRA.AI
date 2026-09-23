"""
Pydantic schemas for the Mithra AI Microservice.
"""

from typing import Any, List
from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: str = Field(..., description="Role of the sender ('user' or 'assistant'/'mithra')")
    content: str = Field(..., description="Text content of the message")


class GenerateRequest(BaseModel):
    message: str = Field(..., description="Current user input text")
    history: List[Any] = Field(
        default_factory=list,
        description="Prior conversation history list (e.g. [{'role': 'user', 'content': '...'}])"
    )
    language: str = Field(
        default="English",
        description="User's preferred response language (e.g., English, Tamil, Tanglish, Hindi, Hinglish, Telugu)"
    )


class GenerateResponse(BaseModel):
    reply: str = Field(..., description="Mithra's generated companion reply")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    model: str = Field(default="Qwen3-4B", description="Active model identifier")
    mode: str = Field(default="demo", description="Operational mode ('live' or 'demo')")

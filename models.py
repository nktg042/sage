from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    is_crisis: bool = False
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None
    document_id: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    conversation_id: int

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    id: int
    title: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = []

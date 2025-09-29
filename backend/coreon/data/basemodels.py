from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional

# Represents the valid content types
class ContentType(str, Enum):
    CONVERSATION = "conversation"
    SEARCH = "search"
    MEMORY = "memory"

# Chat Model
class ChatBase(BaseModel):
    id: Optional[int] = None
    title: str = "Untitled chat"
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    last_active_at: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

# Conversation Model
class MessageBase(BaseModel):
    id: Optional[int] = None
    chat_id: Optional[int] = None
    model_name: Optional[str] = None
    content: str
    role: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

# Embedding Model
class EmbeddingBase(BaseModel):
    id: int
    chat_id: Optional[int] = None
    content_type: ContentType
    conversation_id: Optional[int] = None
    faiss_id: Optional[int] = None
    embedding_model: Optional[str] = None
    vector: list
    created_at: datetime

    class Config:
        from_attributes = True
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from typing import Optional


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
    model_name: Optional[str] = None
    content: str
    role: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True        
        
class ChatCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    
    @field_validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace')
        return v.strip()


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(default="user", pattern="^(user|assistant)$")
    
    @field_validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()


class ErrorResponse(BaseModel):
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status_code: int

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, select
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from enum import Enum
from typing import Optional, List

Base = declarative_base()

class ContentType(Enum):
    """Valid content types for embeddings"""
    CONVERSATION = "conversation"
    SEARCH = "search"
    MEMORY = "memory"

class Chat(Base):
    """
    Represents a chat.
    Stores metadata such as the chat title, creation time, and last activity timestamp.
    Has one-to-many relationships with conversations and search tied to this chat.
    """
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    title = Column(String, default="Untitled chat")
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="chat", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="chat")

    def __str__(self):
        return f"<Chat(id={self.id}, title='{self.title}')>"
    
    async def get_embeddings(self, db_session, content_type: Optional[ContentType] = None):
        """Get all embeddings for this chat, optionally filtered by content type"""
        query = select(Embedding).where(Embedding.chat_id == self.id)
        if content_type:
            query = query.where(Embedding.content_type == content_type)
        result = await db_session.execute(query)
        return result.scalars().all()
    
    async def get_conversations_count(self, db_session) -> int:
        """Get total number of conversations in this chat"""
        result = await db_session.execute(
            select(Conversation).where(Conversation.chat_id == self.id)
        )
        return len(result.scalars().all())

class Conversation(Base):
    """
    Represents a single message within a chat.
    Contains the role (user or assistant), message content, timestamp, and the model used.
    Linked to one chat and optionally related embeddings and memories.
    """
    __tablename__ = 'conversation'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chat.id'), nullable=False)
    model_name = Column(String(255), nullable=True)
    role = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    chat = relationship("Chat", back_populates="conversations")
    embedding = relationship("Embedding", back_populates="conversation", uselist=False, cascade="all, delete-orphan")

    def __str__(self):
        return f"<Conversation(id={self.id}, role={self.role}, model={self.model_name}, message='{self.message[:50]}')>"
    
    async def get_embedding(self, db_session):
        """Get the embedding for this conversation"""
        result = await db_session.execute(
            select(Embedding).where(
                Embedding.content_type == ContentType.CONVERSATION,
                Embedding.conversation_id == self.id
            )
        )
        return result.scalar_one_or_none()
    
    async def has_embedding(self, db_session) -> bool:
        """Check if this conversation has an embedding"""
        embedding = await self.get_embedding(db_session)
        return embedding is not None

class Embedding(Base):
    """
    Stores vector embeddings for conversations, searches, and memory.
    Generic table that handles all content types.
    """
    __tablename__ = 'embedding'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chat.id'), nullable=True)
    
    # Content identification
    content_type = Column(SQLEnum(ContentType), nullable=False)
    
    # Here's where the three columns come back
    conversation_id = Column(Integer, ForeignKey('conversation.id'), nullable=True)
    
    # FAISS integration
    faiss_id = Column(Integer, nullable=True)
    
    # Embedding data  
    embedding_model = Column(String(255), nullable=True)
    vector = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    chat = relationship("Chat", back_populates="embeddings")
    
    # Relationships with cascading deletes from the "parent" objects
    conversation = relationship("Conversation", back_populates="embedding")
    
    def __str__(self):
        return f"<Embedding(id={self.id}, type={self.content_type})>"

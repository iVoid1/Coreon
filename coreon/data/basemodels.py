from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Session(Base):
    """
    Represents a chat session.
    Stores metadata such as the session title, creation time, and last activity timestamp.
    Has one-to-many relationships with conversations and search tied to this session.
    """
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    title = Column(String, default="Untitled Session")
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now)

    # العلاقات
    conversations = relationship("Conversation", back_populates="session")
    searches = relationship("Search", back_populates="session")
    embedding = relationship("Embedding", back_populates="session")
    search_queries = relationship("SearchQuery", back_populates="session")

    def __str__(self):
        return f"<Session(id={self.id}, title='{self.title}')>"

class Conversation(Base):
    """
    Represents a single message within a chat session.
    Contains the role (user or assistant), message content, timestamp, and the model used.
    Linked to one session and optionally related embeddings and memories.
    """
    __tablename__ = 'conversation'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    model_name = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

    # العلاقات
    session = relationship("Session", back_populates="conversations")
    embedding = relationship("Embedding", back_populates="conversation", uselist=False)
    memories = relationship("Memory", back_populates="conversation")

    def __str__(self):
        return f"<Conversation(id={self.id}, role={self.role}, model={self.model_name}, message='{self.message[:50]}')>"

class Embedding(Base):
    """
    Stores vector embeddings of conversation messages.
    """
    __tablename__ = 'embedding'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('conversation.id'), nullable=False)
    vector = Column(Text, nullable=True)
    faiss_id = Column(Integer, nullable=True)  # هذا العمود هو اللي بيربط بـ Faiss

    # العلاقات
    session = relationship("Session", back_populates="embedding")
    conversation = relationship("Conversation", back_populates="embedding")

    def __str__(self):
        return f"<Embedding(id={self.id}, faiss_id={self.faiss_id})>"
    
class Memory(Base):
    """
    Represents memory chunks or extracted facts learned from conversations.
    Can be temporary or persistent and linked to specific conversation entries.
    """
    __tablename__ = 'memory'

    id = Column(Integer, primary_key=True)
    memory = Column(Text, nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversation.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)

    # العلاقات
    conversation = relationship("Conversation", back_populates="memories")

    def __str__(self):
        return f"<Memory(id={self.id})>"
    
class Search(Base):
    """
    Stores the results of web/document search related to a session.
    Includes the topic, content, source URL, LLM analysis, timestamps, and expiry.
    """
    __tablename__ = 'search'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    search_query_id = Column(Integer, ForeignKey('search_query.id'), nullable=False)
    topic = Column(String(255))
    content = Column(Text)
    source_url = Column(String(255), nullable=True)
    analysis = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    expired_at = Column(DateTime, nullable=True)

    # العلاقات
    session = relationship("Session", back_populates="searches")
    search_query = relationship("SearchQuery", back_populates="searches")

    def __str__(self):
        return f"<Search(id={self.id}, topic={self.topic})>"

class SearchQuery(Base):
    """
    Represents the original search request made during a session.
    Tracks query text and timestamp.
    """
    __tablename__ = 'search_query'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    query_text = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    # العلاقات
    session = relationship("Session", back_populates="search_queries")
    searches = relationship("Search", back_populates="search_query")

    def __str__(self):
        return f"<SearchQuery(id={self.id}, query='{self.query_text}')>"
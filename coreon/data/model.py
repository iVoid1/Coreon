from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime





Base = declarative_base()


class Session(Base):
    __tablename__ = 'session'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, default="Untitled Session")
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now)

    #relationships
    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")
    searches = relationship("Search", back_populates="related_session")

class Conversation(Base):
    __tablename__ = 'conversation'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('session.id', ondelete='CASCADE'))
    model_name = Column(String)
    role = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    
    #relationships
    session = relationship("Session", back_populates="conversations")
    embedding = relationship("Embedding", uselist=False, back_populates="conversation")
    memories = relationship("Memory", back_populates="conversation")

class Embedding(Base):
    __tablename__ = 'embedding'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversation.id'), unique=True)
    vector = Column(Text)
    
    #relationships
    conversation = relationship("Conversation", back_populates="embedding")

class Search(Base):
    __tablename__ = 'search'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'))
    search_query_id = Column(Integer, ForeignKey('search_query.id'))
    topic = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String)
    analysis = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    expired_at = Column(DateTime, nullable=True)
    
    related_session = relationship("Session", back_populates="searches")
    search_query = relationship("SearchQuery", back_populates="searches")

class SearchQuery(Base):
    __tablename__ = 'search_query'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'))
    query_text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    #relationships
    session = relationship("Session")  # يمكن إضافة back_populates حسب الحاجة
    searches = relationship("Search", back_populates="search_query")

class Memory(Base):
    __tablename__ = 'memory'
    
    id = Column(Integer, primary_key=True)
    memory = Column(Text, nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversation.id'))
    timestamp = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)
    
    #relationships
    conversation = relationship("Conversation", back_populates="memories")
    
    

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Database:
    def __init__(self, db_path) -> None:
        self.engine = create_engine(db_path)
        self.SessionLocal = sessionmaker(bind=self.engine)

    class Session(Base):
        __tablename__ = 'session'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        title = Column(Text, default="Untitled Session")
        created_at = Column(DateTime, default=datetime.now)

        conversation = relationship("Database.Conversation", back_populates="session", cascade="all, delete")

    class Conversation(Base):
        __tablename__ = 'conversation'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        session_id = Column(Integer, ForeignKey('session.id', ondelete='CASCADE'))
        model_name = Column(String)
        role = Column(String)
        message = Column(Text)
        timestamp = Column(DateTime, default=datetime.now)

        session = relationship("Database.Session", back_populates="conversation")
        embedding = relationship("Database.Embedding", uselist=False, back_populates="conversation")

    class Embedding(Base):
        __tablename__ = 'embedding'
        
        id = Column(Integer, primary_key=True)
        conversation_id = Column(Integer, ForeignKey('conversation.id'), unique=True)
        vector = Column(Text)

        conversation = relationship("Database.Conversation", back_populates="embedding")
        
    class Reference(Base):
        __tablename__ = 'reference'
        
        id = Column(Integer, primary_key=True)
        session_id = Column(Integer, ForeignKey('session.id'))
        search_query_id = Column(Integer, ForeignKey('search_query.id'))  # الجديد
        topic = Column(String, nullable=False)
        content = Column(Text, nullable=False)
        source_url = Column(String)
        analysis = Column(Text)
        timestamp = Column(DateTime, default=datetime.now)
        expired_at = Column(DateTime, nullable=True)

        # علاقات

        related_session = relationship("Database.Session", backref="reference")
        search_query = relationship("Database.SearchQuery", backref="references")  # الجديد

    class SearchQuery(Base):
        __tablename__ = 'search_query'
        
        id = Column(Integer, primary_key=True)
        session_id = Column(Integer, ForeignKey('session.id'))
        query_text = Column(String, nullable=False)
        timestamp = Column(DateTime, default=datetime.now)

        session = relationship("Database.Reference", backref="search_query")

    class Memory(Base):
        __tablename__ = 'memory'
        id = Column(Integer, primary_key=True)
        memory = Column(Text, nullable=False)  
        conversation_id = Column(Integer, ForeignKey('conversation.id'))  

        timestamp = Column(DateTime, default=datetime.now)
        expires_at = Column(DateTime, nullable=True)

    conversation = relationship("Database.Conversation", backref="memories")

    def initialize(self):
        Base.metadata.create_all(self.engine)
        


if __name__ == "__main__":
    db = Database(db_path="sqlite:///database.sqlite")
    db.initialize()
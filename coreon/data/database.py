from datetime import datetime
from functools import wraps
from typing import Optional
from sqlalchemy.orm import Session as SQLASession

from coreon.data.model import Session, Conversation, Base, create_engine, sessionmaker, Column


def with_session(func):
    @wraps(func)
    def wrapper(self, *args, db_session=None, **kwargs):
        db_session = self.SessionLocal()
        try:
            return func(self, *args, db_session=db_session, **kwargs)
        finally:
            db_session.close()
    return wrapper


class Database:
    def __init__(self, db_path):
        #TODO: make more useful variables
        self.engine = create_engine(db_path, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db_path = db_path
        

    def initialize(self):
        Base.metadata.create_all(self.engine)
    
    @with_session
    def create_session(self, title: str="Untitled Session", 
                       db_session: Optional[SQLASession]=None
                       ) -> (tuple[Column[int], Column[str]]|tuple[None, None]):
        """Create a new chat session with a given title. Returns session id and title."""
        
        #Check if session with db_session exists
        if db_session == None:
            return None, None
        
        session = Session(title=title)
        
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        return session.id, session.title
    
    @with_session
    def insert_conversation(self, session_id: int, 
                    model_name: str, 
                    role: str, 
                    message: str, 
                    timestamp: Optional[datetime] = None, 
                    db_session: Optional[SQLASession]=None
                    ) -> (Column[int]|None):
        """Insert a new conversation into the database. Returns conversation id."""
        #Check if session with db_session exists
        if db_session == None:
            return
        
        if timestamp is None:
            timestamp = datetime.now()

        conversation = Conversation(session_id=session_id, model_name=model_name, role=role, message=message, timestamp=timestamp)
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        return conversation.id
      

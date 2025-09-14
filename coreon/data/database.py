from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Optional, Union
from datetime import datetime
import logging

from coreon.data.basemodels import Base, Session, Conversation, Embedding


class Database:
    """
    Database class to handle database operations with model class.
    This class provides methods to create a session, save messages, and manage the database.
    SQLAlchemy is used for ORM operations.
    """
    def __init__(self, db_path: str, echo: bool = False):
        """
        Initialize the database connection.
        
        :param db_path: Path to the database file.
        :param echo: If True, SQLAlchemy will log all the statements issued to stderr.
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        self.engine = create_engine(db_path, echo=echo)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Enable SQLite foreign keys
        self._enable_foreign_keys()
        
        # Create tables if they do not exist
        Base.metadata.create_all(self.engine)
        self.logger.info(f"Database initialized: {db_path}")

    def _enable_foreign_keys(self):
        """Enable foreign key constraints for SQLite."""
        @event.listens_for(self.engine, "connect")
        def set_fk_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            
    @contextmanager
    def create_db_session(self):
        """
        Context manager for database sessions.
        
        :return: A session object to interact with the database.
        """
        db_session = self.SessionLocal()
        try:
            yield db_session
            db_session.expunge_all()  # Clear the session cache
            db_session.commit()
            self.logger.debug("Session committed")
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Session rollback due to error: {e}")
            raise
        finally:
            db_session.close()
            self.logger.debug("Session closed")
    
    def create_session(self, title: str = "Untitled Session")-> Optional[Session]:
        """
        Create a new chat session.
        
        :param title: Title of the session.
        :return: The created session object or None if creation failed.
        """
        
        try:
            with self.create_db_session() as db_session:
                # Create a new chat session
                session = Session(title=title)
                
                self.insert(session)
                self.logger.info(f"Created session: {session.id} - '{session.title}'")
                
                return session
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None

    def get_session(self, session_id: int) -> Optional[Session]:
        """
        Get a session by its ID.
        
        :param session_id: ID of the session.
        :return: Session object or None if not found.
        """
        try:
            with self.create_db_session() as db_session:
                session = db_session.query(Session).filter(
                    Session.id == session_id
                ).first()
                self.logger.debug(f"Retrieved session: {session}")
                return session
        except Exception as e:
            self.logger.error(f"Failed to get session by ID: {e}")
            return None

    def get_all_sessions(self) -> list[Session]:
        """
        Get all sessions in the database.
        
        :return: List of all Session objects.
        """
        try:
            with self.create_db_session() as db_session:
                sessions = db_session.query(Session).all()
                self.logger.debug(f"Retrieved {len(sessions)} sessions")
                return sessions
        except Exception as e:
            self.logger.error(f"Failed to get all sessions: {e}")
            return []

    def save_message(self, session_id: int, role: str, content: str, model_name: str = "default")-> Optional[Conversation]:
        """Save a conversation message to the database.
        
        :param session_id: ID of the session.
        :param role: Role of the message (user or assistant).
        :param content: Content of the message.
        :param model_name: Name of the model used for the message.
        """
        try:
            
            with self.create_db_session() as db_session:
                message = Conversation(
                    session_id=session_id,
                    role=role,
                    message=content,
                    model_name=model_name
                )
                self.logger.debug(f"Saved {role} message for session {session_id}")
                self.insert(message)
                return message
        except Exception as e:
            self.logger.error(f"Failed to save message: {e}")
            return None
      
    def get_conversation(self, session_id: int) -> list[Conversation]:
        """
        Get conversation history for a session.
        Retrieves all messages in the session ordered by timestamp.
        
        :param session_id: ID of the session.
        :return: List of Conversation objects or None if retrieval failed.
        """
        try:
            with self.create_db_session() as db_session:
                conversations = db_session.query(Conversation).filter(
                    Conversation.session_id == session_id
                ).order_by(Conversation.timestamp).all()
                
                self.logger.debug(f"Retrieved {len(conversations)} messages for session {session_id}")
                return conversations
        except Exception as e:
            self.logger.error(f"Failed to get conversation: {e}")
            return []
        
    def insert_embedding(self, session_id: int, message_id: int, faiss_id=None) -> None:
        """
        Create embeddings for conversation history.
        
        :param message_id: ID of the message.
        """
        try:
            with self.create_db_session() as db_session:
                embedding = Embedding(
                    session_id=session_id,
                    message_id=message_id,
                    faiss_id=faiss_id
                    )
                self.insert(embedding)
                self.logger.debug(f"Inserted embeddings for message {embedding.message_id}")
        except Exception as e:
            self.logger.error(f"Failed to insert embeddings: {e}")

    def get_embeddings(self, session_id: int) -> list[Embedding]:
        """
        Get embeddings for a session.
        
        :param session_id: ID of the session.
        :return: List of Embedding objects or [] if retrieval failed.
        """
        try:
            with self.create_db_session() as db_session:
                embeddings = db_session.query(Embedding).filter(
                    Embedding.session_id == session_id
                ).all()
                self.logger.debug(f"Retrieved {len(embeddings)} embeddings for session {session_id}")
                return embeddings
        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {e}")
            return []

    def insert(self, item: Union[Session, Conversation, Embedding]):
        with self.create_db_session() as db_session:
            db_session.add(item)
            db_session.flush()
            db_session.refresh(item)
            self.logger.debug(f"Inserted {item}")
    
    def close(self):
        """Close the database connection."""
        self.engine.dispose()
        self.logger.info("Database connection closed")
        

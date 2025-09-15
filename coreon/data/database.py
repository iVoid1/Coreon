from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Optional, Union
from datetime import datetime
import logging

from coreon.data.basemodels import Base, Chat, Conversation, Embedding


class Database:
    """
    Database class to handle database operations with model class.
    This class provides methods to create a chat, save messages, and manage the database.
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
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=True)
        
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
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Session rollback due to error: {e}")
            raise
        finally:
            db_session.close()

    async def insert(self, item: Union[Chat, Conversation, Embedding]):
        """
        Insert an item into the database.
        
        :param item: The item to insert.
        :return: The inserted item.
        """
        with self.create_db_session() as db_session:
            db_session.add(item)
            db_session.flush()
            db_session.refresh(item)
            return item

    async def create_chat(self, title: str = "Untitled chat")-> Chat:
        """
        Create a new chat .
        
        :param title: Title of the chat.
        :return: The created chat object or None if creation failed.
        """
        
        try:
            # Create a new chat chat
            chat = Chat(title=title)
            
            await self.insert(chat)
            self.logger.info(f"Created chat: {chat.id} - '{chat.title}'")                
            return chat
        except Exception as e:
            self.logger.error(f"Failed to create chat: {e}")
            raise e
  
    async def save_message(
            self,
            chat_id: int,
            role: str,
            message: str,
            model_name: str = "ai"
        )-> Conversation:

        """Save a conversation message to the database.
        
        :param chat_id: ID of the chat.
        :param role: Role of the message (user or assistant).
        :param content: Content of the message.
        :param model_name: Name of the model used for the message.
        """
        try:
            
            message = Conversation(
                chat_id=chat_id,
                role=role,
                message=message,
                model_name=model_name
            )
            
            await self.insert(message)
            return message
        except Exception as e:
            self.logger.error(f"Failed to save message: {e}")
            raise e
        
    async def save_embedding(self, chat_id: int, message_id: int, vector, faiss_id=None) -> Embedding:
        """
        Create embeddings for conversation history.
        
        :param chat_id: ID of the chat.
        :param message_id: ID of the message.
        :param vector: Embedding vector.
        :param faiss_id: FAISS ID.
        """
        try:
            embedding = Embedding(
                chat_id=chat_id,
                message_id=message_id,
                vector=vector,
                faiss_id=faiss_id
                )
            await self.insert(embedding)
            self.logger.debug(f"Inserted embeddings for message {embedding.message_id}")
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to insert embeddings: {e}")
            raise e

    async def get_chat(self, chat_id: int) -> Chat:
        """
        Get a chat by its ID.
        
        :param chat_id: ID of the chat.
        :return: chat object or None if not found.
        """
        try:
            with self.create_db_session() as db_session:
                chat = db_session.query(Chat).filter(
                    Chat.id == chat_id
                ).first()
                return chat
        except Exception as e:
            self.logger.error(f"Failed to get chat by ID: {e}")
            raise e

    async def get_all_chats(self) -> list[Chat]:
        """
        Get all chats in the database.
        
        :return: List of all chat objects.
        """
        try:
            with self.create_db_session() as db_session:
                chats = db_session.query(Chat).all()
                return chats
        except Exception as e:
            self.logger.error(f"Failed to get all chats: {e}")
            return []

    async def get_conversation(self, chat_id: int) -> list[Conversation]:
        """
        Get conversation history for a chat.
        Retrieves all messages in the chat ordered by timestamp.
        
        :param chat_id: ID of the chat.
        :return: List of Conversation objects or None if retrieval failed.
        """
        try:
            with self.create_db_session() as db_session:
                conversations = db_session.query(Conversation).filter(
                    Conversation.chat_id == chat_id
                ).order_by(Conversation.timestamp).all()
                
                return conversations
        except Exception as e:
            self.logger.error(f"Failed to get conversation: {e}")
            return []
        
    async def get_embeddings(self, chat_id: int) -> list[Embedding]:
        """
        Get embeddings for a chat.
        
        :param chat_id: ID of the chat.
        :return: List of Embedding objects or [] if retrieval failed.
        """
        try:
            with self.create_db_session() as db_session:
                embeddings = db_session.query(Embedding).filter(
                    Embedding.chat_id == chat_id
                ).all()
                return embeddings
        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {e}")
            return []

    def close(self):
        """Close the database connection."""
        self.engine.dispose()
        self.logger.info("Database connection closed.")
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import event, select
from contextlib import asynccontextmanager
from typing import Union, Optional, List

from coreon.data import Base, Chat, Conversation, Embedding, ContentType
from coreon.utils import setup_logger

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
        self.is_initialized = False
        self.logger = setup_logger(__name__)
    
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=echo)
        self.SessionLocal = async_sessionmaker(bind=self.engine, autoflush=True, expire_on_commit=False)
        
        # Enable SQLite foreign keys
        self._enable_foreign_keys()
        
        self.logger.info(f"Database initialized: {db_path}")

    def _enable_foreign_keys(self):
        """Enable foreign key constraints for SQLite."""
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_fk_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
      
    async def connect(self):
        """Connect to the database."""
        await self.engine.connect()
        self.logger.info("Database connected.")
              
    async def init_db(self):
        """Creates database tables if they don't exist."""
        if self.is_initialized:
            self.logger.info("Database already initialized.")
            return
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                self.is_initialized = True
                self.logger.info("Database tables created.")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            await self.close()
    async def ensure_initialized(self):
        """Ensure database is initialized before operations."""
        if not self.is_initialized:
            await self.init_db()
            
    async def close(self):
        """Close the database connection."""
        await self.engine.dispose()
        await self.SessionLocal().close_all()
        self.logger.info("Database connection closed.")
         
    @asynccontextmanager
    async def create_db_session(self):
        """
        Context manager for database sessions.
        
        :return: A session object to interact with the database.
        """
        await self.ensure_initialized()
        db_session = self.SessionLocal()
        try:
            yield db_session
            db_session.expunge_all()  # Clear the session cache
            await db_session.commit()
        except Exception as e:
            await db_session.rollback()
            self.logger.error(f"Session rollback due to error: {e}")
            raise
        finally:
            await db_session.close()

    async def insert(self, item: Union[Chat, Conversation, Embedding]):
        """
        Insert an item into the database.
        
        :param item: The item to insert.
        :return: The inserted item.
        """
        await self.ensure_initialized()
        async with self.create_db_session() as db_session:
            db_session.add(item)
            await db_session.flush()
            await db_session.refresh(item)
            return item

    # Chat operations
    async def create_chat(self, title: str = "Untitled chat") -> Chat:
        """
        Create a new chat.
        
        :param title: Title of the chat.
        :return: The created chat object.
        """
        await self.ensure_initialized()
        try:
            chat = Chat(title=title)
            await self.insert(chat)
            self.logger.info(f"Created chat: {chat.id} - '{chat.title}'")                
            return chat
        except Exception as e:
            self.logger.error(f"Failed to create chat: {e}")
            raise e
    
    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        """
        Get a chat by its ID.
        
        :param chat_id: ID of the chat.
        :return: Chat object or None if not found.
        """
        await self.ensure_initialized()
        try:
            async with self.create_db_session() as db_session:
                result = await db_session.execute(
                    select(Chat).where(Chat.id == chat_id)
                )
                return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Failed to get chat by ID: {e}")
            raise e

    async def get_all_chats(self) -> List[Chat]:
        """
        Get all chats in the database.
        
        :return: List of all chat objects.
        """
        await self.ensure_initialized()
        try:
            async with self.create_db_session() as db_session:
                result = await db_session.execute(select(Chat))
                return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get all chats: {e}")
            return []

    # Conversation operations
    async def save_message(
        self,
        chat_id: int,
        role: str,
        message: str,
        model_name: str = "ai"
    ) -> Conversation:
        """Save a conversation message to the database.
        
        :param chat_id: ID of the chat.
        :param role: Role of the message (user or assistant).
        :param message: Content of the message.
        :param model_name: Name of the model used for the message.
        """
        await self.ensure_initialized()
        try:
            message_obj = Conversation(
                chat_id=chat_id,
                role=role,
                message=message,
                model_name=model_name
            )
            
            await self.insert(message_obj)
            return message_obj
        except Exception as e:
            self.logger.error(f"Failed to save message: {e}")
            raise e

    async def get_conversation(self, chat_id: int) -> List[Conversation]:
        """
        Get conversation history for a chat.
        Retrieves all messages in the chat ordered by timestamp.
        
        :param chat_id: ID of the chat.
        :return: List of Conversation objects.
        """
        await self.ensure_initialized()
        try:
            async with self.create_db_session() as db_session:
                result = await db_session.execute(
                    select(Conversation).where(
                        Conversation.chat_id == chat_id
                    ).order_by(Conversation.timestamp)
                )
                return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get conversation: {e}")
            return []

    # Embedding operations
    async def save_embedding(
        self, 
        chat_id: int,
        content_type: ContentType,
        conversation_id: int,
        embedding_model: str,
        vector,
        faiss_id: Optional[int] = None
        
    ) -> Embedding:
        """
        Save embedding for any content type.
        
        :param content_type: Type of content (conversation, search, memory).
        :param content_id: ID of the content.
        :param vector: Embedding vector.
        :param chat_id: Optional chat ID for organization.
        :param embedding_model: Model used for embedding.
        :param faiss_id: FAISS ID for vector search.
        """
        await self.ensure_initialized()
        try:
            embedding = Embedding(
                chat_id=chat_id,
                content_type=content_type,
                conversation_id=conversation_id,
                embedding_model=embedding_model,
                vector=vector,
                faiss_id=faiss_id
            )
            await self.insert(embedding)
            self.logger.debug(f"Inserted embedding for {content_type.value} {conversation_id}")
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to insert embedding: {e}")
            raise e

    async def get_embeddings(
        self, 
        chat_id: Optional[int] = None,
        content_type: Optional[ContentType] = None
    ) -> List[Embedding]:
        """
        Get embeddings with optional filters.
        
        :param chat_id: Filter by chat ID.
        :param content_type: Filter by content type.
        :return: List of Embedding objects.
        """
        await self.ensure_initialized()
        try:
            async with self.create_db_session() as db_session:
                query = select(Embedding)
                
                if chat_id is not None:
                    query = query.where(Embedding.chat_id == chat_id)
                if content_type is not None:
                    query = query.where(Embedding.content_type == content_type)
                    
                result = await db_session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {e}")
            return []

    async def get_embedding_by_content(
        self, 
        content_type: ContentType, 
        content_id: int
    ) -> Optional[Embedding]:
        """
        Get embedding for specific content.
        
        :param content_type: Type of content.
        :param content_id: ID of the content.
        :return: Embedding object or None.
        """
        await self.ensure_initialized()
        try:
            async with self.create_db_session() as db_session:
                result = await db_session.execute(
                    select(Embedding).where(
                        Embedding.content_type == content_type,
                        Embedding.content_id == content_id
                    )
                )
                return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Failed to get embedding: {e}")
            return None


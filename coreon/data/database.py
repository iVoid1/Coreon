from sqlalchemy.orm import Session as SQLASession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from datetime import datetime
from typing import Optional

from coreon.data.model import Session, Conversation, Base, Column
from coreon.data.decorators import with_session, transactional, enforce_sqlite_fk
from coreon.utils.logger import Logger


logger = Logger(__name__)




class Database:
    """
    Handles all database interactions such as session creation,
    conversation insertion, and querying past sessions.
    """
    
    def __init__(self, db_path, initialize_tables: bool = True, foreign_keys: bool = True, echo: bool = False):
        """
        Initialize the database engine and session factory.
        :param db_path: SQLAlchemy database URL
        """
        # Create the database engine
        logger.info(f"Initializing database connection at: {db_path}")
        self.engine = create_engine(db_path, echo=echo)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db_path = db_path
        
        # Enable foreign key enforcement if using SQLite
        if foreign_keys:
            enforce_sqlite_fk(self.engine)  # Enable foreign key enforcement for SQLite
            logger.info("Database engine created successfully.", echo=echo)

        # Initialize tables if requested
        if initialize_tables:
            self.initialize_tables()
            logger.info("Database tables initialized.", echo=echo)
        else:
            logger.warning("Database tables not initialized. Call `initialize_tables()` manually if needed.", echo=echo)
        


    def initialize_tables(self):
        """
        Creates all tables in the database based on the defined models.
        """
        logger.info("Creating tables...")
        Base.metadata.create_all(self.engine)
        logger.success("All tables created successfully.")

    @with_session
    def create_session(self, 
                       title: str = "Untitled Session",
                       catch: bool = False,
                       echo: bool = False,
                       *,
                       db_session: Optional[SQLASession] = None
                       ) -> Optional[Session]:
        """
        Creates a new session in the database.
        :param title: Title of the session, defaults to "Untitled Session"
        :param catch: Whether to catch exceptions
        :param echo: Whether to log the operation
        :param db_session: Optional SQLAlchemy session to use
        Return: (session_id: int, session_title: str)
        """
        if db_session is None:
            logger.warning("No database session provided for creating a new session.")
            return None
        logger.debug(f"Creating new session with title: '{title}'", echo=echo)
        session = Session(title=title)
        
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        logger.info(f"New session created with ID: {session.id}, title: '{session.title}'")
        return session

    @with_session
    @transactional()
    def insert_conversation(self, 
                            session_id: Optional[int] = None, 
                            model_name: str = "default_model", 
                            role: str = "user", 
                            message: str = "", 
                            timestamp: Optional[datetime] = None, 
                            echo: bool = True,
                            commit: bool = True,
                            catch: bool = True,
                            *,
                            db_session: Optional[SQLASession] = None
                            ) -> Optional[Conversation]:
        """
        Inserts a conversation message into the database.
        :param session_id: ID of the session this conversation belongs to
        :param model_name: Name of the AI model that generated the response
        :param role: Role of the message sender ('user' or 'assistant')
        :param message: Content of the conversation message
        :param timestamp: Optional timestamp for the message, defaults to now
        :param db_session: Optional SQLAlchemy session to use
        :param echo: Whether to log the operation
        :param commit: Whether to commit the transaction
        :param catch: Whether to catch exceptions
        :return: ID of the inserted conversation message
        """
        if db_session is None:
            logger.warning("No database session provided for inserting conversation.")
            return None

        msg = Conversation(
            session_id=session_id,
            model_name=model_name,
            role=role,
            message=message,
            timestamp=timestamp or datetime.now()
        )
        logger.debug(f"Inserting conversation: {msg}", echo=echo)
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)
        logger.info(f"Inserted conversation with ID: {msg.id}, role: '{msg.role}', message: '{msg.message[:50]}'", echo=echo)
        return msg
        
    @with_session
    def fetch_conversation(self, session_id: int, 
                           *,
                           db_session: Optional[SQLASession] = None
                           ) -> list[Conversation] | None:
        if db_session is None:
            logger.warning("No database session provided for fetching conversation.")
            return []

        logger.debug(f"Fetching conversation for session: {session_id}")
        result = db_session.query(Conversation).filter(
            Conversation.session_id == session_id
        ).order_by(Conversation.timestamp).all()

        logger.info(f"Fetched {len(result)} messages for session {session_id}")
        return result

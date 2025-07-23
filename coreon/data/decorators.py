from functools import wraps
from sqlalchemy import event

from coreon.utils.logger import Logger

logger = Logger(__name__)


# --- Decorators for Database Operations ---

def with_session(func, catch=None):
    """
    Decorator to manage the lifecycle of a database session for any function or method.
    Handles exceptions, logs errors, and ensures the session is always closed.
    Can be used on both class methods (expects self.SessionLocal) and standalone functions (expects session_factory kwarg).
    If the wrapped function returns None, logs a warning.
    """
    @wraps(func)
    def wrapper(self, *args, db_session=None, **kwargs):
        # Determine session factory: from self or explicit kwarg
        _catch = kwargs.get("catch", catch)
        db_session = self.SessionLocal()
        if db_session is None:
            logger.exception("No database session provided. Ensure to pass db_session or use with_session on a class method.")
            if _catch:
                raise RuntimeError("No database session provided. Ensure to pass db_session or use with_session on a class method.")
             
        # Session already provided, just call the function
        try:
            result = func(self, *args, db_session=db_session, **kwargs)
            if result is None:
                logger.warning(f"{func.__name__} returned None.")
            db_session.close()
            logger.debug(f"Session closed for {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper


def transactional(commit=None, catch=None, echo=False):
    """
    A decorator that wraps a method in a database transaction.

        Args:
            commit (bool, optional): Whether to commit the transaction after the method executes. Defaults to None.
                If None, the transaction is not committed. If True, the transaction is committed unless an exception occurs.
            catch (bool, optional): Whether to catch exceptions raised by the method. Defaults to None.
                If None, exceptions are re-raised. If True, exceptions are caught and a RuntimeError is raised instead.

        Returns:
            callable: A decorator that wraps the method in a database transaction.

        Raises:
            RuntimeError: If commit is True and an exception occurs during the transaction, or if catch is True and an exception occurs.
            Exception: If catch is False and an exception occurs during the transaction, the original exception is re-raised.

        Example:
            @transactional(commit=True, catch=True)
            def my_method(self, *args, db_session=None, **kwargs):
                # Do something with the database session
                pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, db_session, **kwargs):
            _commit = kwargs.get("commit", commit)
            _catch = kwargs.get("catch", catch)
            _echo = kwargs.get("echo", echo)
            
            try:
                logger.debug(f"Executing {func.__name__} transactionally", echo=_echo)
                result = func(self, *args, db_session=db_session, **kwargs)
                if _commit:
                    db_session.commit()
                logger.info(f"{func.__name__} committed successfully", tag="success", echo=_echo)
                return result
            except Exception as e:
                db_session.rollback()
                logger.error(f"Rolled back {func.__name__} due to {e}", echo=_echo)
                if _catch:
                    raise RuntimeError(f"Database error: {e}")
                else:
                    raise
        return wrapper
    return decorator

def enforce_sqlite_fk(engine):
    """Enable foreign key enforcement for SQLite."""
    @event.listens_for(engine, "connect")
    def _set_fk_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        logger.debug("Enforcing SQLite foreign key constraint")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
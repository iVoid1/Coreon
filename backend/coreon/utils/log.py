import logging
from rich.logging import RichHandler
from rich.console import Console

def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Setup a logger with Rich formatting."""
    logger = logging.getLogger(name)
   
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
   
    logger.propagate = False
   
    console = Console(log_time_format="%H:%M:%S")
    handler = RichHandler(
        console=console,
        show_time=True,
        rich_tracebacks=True,
        tracebacks_width=40,
    )
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
   
    logger.addHandler(handler)
    
    logger.setLevel(level)
    handler.setLevel(level)
   
    return logger

def set_logger_level(logger: logging.Logger, level: int):
    """Set the level of a logger."""
    logger.setLevel(level)
    
    for handler in logger.handlers:
        handler.setLevel(level)


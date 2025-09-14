import logging
from rich.logging import RichHandler
from rich.console import Console

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger with Rich formatting."""
    logger = logging.getLogger(name)
    
    # إزالة جميع الـ handlers الموجودة مسبقاً
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # منع انتشار الرسائل للـ parent loggers
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
    logger.setLevel(level=logging.INFO)
    
    return logger

# أو الحل البديل - استخدام نفس الـ logger instance
_loggers = {}

def setup_logger_singleton(name: str) -> logging.Logger:
    """Setup a logger with Rich formatting (Singleton pattern)."""
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
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
    logger.setLevel(level=logging.INFO)
    
    _loggers[name] = logger
    return logger
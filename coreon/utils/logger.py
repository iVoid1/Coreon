import logging
from rich.logging import RichHandler
from rich.console import Console

SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")

class Logger:
    _instance = None

    def __new__(cls, name: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger(name)
        return cls._instance

    def _init_logger(self, name):
        self.console = Console(log_time_format="%H:%M:%S")
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)

        if not self._logger.hasHandlers():
            handler = RichHandler(
                console=self.console,
                show_time=True,
                rich_tracebacks=True,
                tracebacks_width=80,
            )
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def log(self, level, msg, echo: bool = True, tag=None, **kwargs):
        if not echo:
            return

        if tag:
            msg = f"[{tag}] {msg}"
        self._logger.log(level, msg, stacklevel=3, **kwargs)

    def info(self, msg, tag: str = "", echo: bool = True, **kwargs):
        self.log(logging.INFO, msg, tag=tag, echo=echo, **kwargs)
        
    def debug(self, msg, tag: str = "", echo: bool = True, **kwargs):
        self.log(logging.DEBUG, msg, tag=tag, echo=echo, **kwargs)
        
    def error(self, msg, tag: str = "", echo: bool = True, **kwargs):
        self.log(logging.ERROR, msg, tag=tag, echo=echo, **kwargs)
        
    def success(self, msg, tag: str = "", echo: bool = True, **kwargs):
        self.log(SUCCESS, msg, tag=tag, echo=echo, **kwargs)
        
    def warning(self, msg, tag: str = "", echo: bool = True, **kwargs):
        self.log(logging.WARNING, msg, tag=tag, echo=echo, **kwargs)
        
    def critical(self, msg, tag: str = "", echo: bool = True, **kwargs):
        self.log(logging.CRITICAL, msg, tag=tag, echo=echo, **kwargs)
        
    def exception(self, msg, tag: str = "", echo: bool = True, **kwargs):
        self.log(logging.ERROR, msg, tag=tag, echo=echo, exc_info=True, **kwargs)

    def set_console(self, console: Console):
        self.console = console

    def __repr__(self):
        return f"<Logger(name={self._logger.name})>"
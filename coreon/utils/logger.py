import logging
from typing import Any



class Logger:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        self._format = '%(name)s - %(levelname)s - %(message)s'
        self.set_format(self._format)
        

    def debug(self, msg: Any):
        self._logger.debug(msg)

    def info(self, msg: Any):
        self._logger.info(msg)

    def warning(self, msg: Any):
        self._logger.warning(msg)

    def error(self, msg: Any, exc_info: bool = False):
        self._logger.error(msg, exc_info=exc_info)

    def critical(self, msg: Any):
        self._logger.critical(msg)
    
    def exception(self, msg: Any):
        self._logger.exception(msg)
    
    def set_format(self, fmt: str):
        self.formatter = logging.Formatter(fmt)
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(self.formatter)
        self._logger.addHandler(self.handler)
        
        
        
logger = Logger(__name__)
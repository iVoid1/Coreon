"""
Coreon AI Module
This module provides the Coreon class, which is a simple wrapper for the Ollama chat client
It allows interaction with AI models for chat functionality.
It includes methods for sending messages and receiving responses, with support for streaming responses.
It also includes logging for debugging and error handling.
It is designed to be used in a chat application context, where users can send messages and receive AI-generated responses.
It is part of the Coreon project, which is a chat application that uses AI models for conversation.
"""

from coreon.Ai.coreon import Coreon
from coreon.Ai.coreon import AiModel
from coreon.data.database import Database
from coreon.data.basemodels import Chat, Conversation, Embedding
from coreon.utils.log import setup_logger

logger = setup_logger(__name__)

__title__ = "Coreon AI Module"
__vision__ = "0.1.0"
__author__ = "Void"

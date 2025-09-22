"""
Coreon AI Module
This module provides the Coreon class, which is a simple wrapper for the Ollama chat client
It allows interaction with AI models for chat functionality.
It includes methods for sending messages and receiving responses, with support for streaming responses.
It also includes logging for debugging and error handling.
It is designed to be used in a chat application context, where users can send messages and receive AI-generated responses.
It is part of the Coreon project, which is a chat application that uses AI models for conversation.
"""

from coreon.Ai import Coreon
from coreon.Ai import AiModel
from coreon.data import Database
from coreon.data import Chat, Conversation, Embedding, ContentType
from coreon.data import ChatBase, ConversationBase, EmbeddingBase
from coreon.utils import setup_logger

logger = setup_logger(__name__)

__title__ = "Coreon AI Module"
__vision__ = "0.1.0"
__author__ = "Void"

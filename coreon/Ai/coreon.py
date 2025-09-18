import ollama
from ollama import ChatResponse

import faiss
import json
import numpy as np
import os

from typing import Optional

from coreon.data.basemodels import Chat, Conversation, Embedding
from coreon.data.database import Database
from coreon.utils.log import setup_logger

logger = setup_logger(__name__)


class Coreon:
    """Coreon AI Module. 
    use database to store conversation data
    use ollama to generate responses
    
    Attributes:
        db (Database): Database object
        ai_model (str): AI model name
        embedding_model (str): Embedding model name
    """
    
    def __init__(
        self, db: Database, 
        ai_model: str = "llama3.1",
        embed_model: str = "nomic-embed-text:latest", 
        dimension: int = 768,
        host: str = "http://localhost:11434"
        ):
        """Initialize Coreon AI Module.
        
        Args:
            db (Database): Database object
            ai_model (str): AI model name
            embedding_model (str): Embedding model name
            host (str): Ollama host
            """
        self.db = db
        self.host = host
        self.client = ollama.AsyncClient(host=host)
        self.ai_model = ai_model
        self.embedding_model = embed_model
        self.dimension = dimension
        self.chat_id = None
        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.history: list[dict] = []
        self.conversation_data = []
        self.embeddings = np.array([], dtype=np.float32)
        self.logger = setup_logger(__name__)
        
        self.logger.info("Coreon AI initialized")  
                     
    async def load_conversation(self, chat_id: int):
        """Loads conversation from the chat into the FAISS index."""
        self.chat_id = chat_id
        self.conversation_data = await self.db.get_conversation(chat_id=chat_id)
        self.logger.info(f"Conversation loaded for chat {chat_id}")
        self.faiss_index = faiss.IndexFlatL2(self.dimension)
        await self.load_vectors(chat_id=chat_id)
        if not self.embeddings.size:
            self.logger.warning(f"No embeddings found for chat {chat_id}")
            return
        self.faiss_index.add(self.embeddings) # type: ignore
        self.logger.info(f"Conversation loaded into FAISS index{self.embeddings.shape}")  
      
    async def load_vectors(self, chat_id: Optional[int] = None):
        """Returns the vectors of the chat id if not provided use self.chat_id."""
        embeddings = []
        if chat_id:
            for embedding in await self.db.get_embeddings(chat_id=chat_id):
                embeddings.append(embedding.vector)
                
        elif self.chat_id:
            for embedding in await self.db.get_embeddings(chat_id=self.chat_id):
                embeddings.append(embedding.vector)
        else:
            self.logger.warning("No chat id provided")
            
        self.embeddings = np.array(embeddings, dtype=np.float32)
        return self.embeddings
    
    async def embed_text(self, text: str):
        """Generates an embedding for the given text."""
        try:
            response = await self.client.embeddings(
                model=self.embedding_model, prompt=text
            )
            return response.embedding
        except Exception as e:
            self.logger.error(f"Error getting embedding: {e}")
            raise e
        
    async def search_memory(self, query: str, k: int = 5):
        """Searches the FAISS index for relevant memories.

        Args:
            query (str): The search query.
            k (int): The number of relevant memories to retrieve.

        Returns:
            Tuple[np.ndarray, np.ndarray]: Distances and indices of the nearest neighbors.
        """
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            self.logger.warning("FAISS index is not initialized or empty. No search will be performed.")
            return np.array([[]]), np.array([[]])

        try:
            query_embedding = await self.embed_text(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)

            distances, indices = self.faiss_index.search(query_array, k=k) # type: ignore
            self.logger.info(f"FAISS search results: Distances={distances}, Indices={indices}")
            return distances, indices
        
        except Exception as e:
            self.logger.error(f"Error during memory search: {e}")
            return np.array([[]]), np.array([[]])
        
    async def search_relevant(self, indices: np.ndarray, content: str=""):
        # self.history = []
        if indices.any():
            idx:int
            for idx in indices[0]:
                if 0 <= idx < len(self.conversation_data):
                    message_content = self.conversation_data[idx].message
                    message_role = self.conversation_data[idx].role
                    self.history.append({
                        "role": message_role,
                        "content": message_content
                    })

            if content:
                self.history.append({"role": "user", "content": content})
            else:
                self.logger.warning("No content provided for search_relevant")

        else:
            self.logger.warning(f"No relevant messages found for chat {self.chat_id}")

    async def add_index(self, embed: list, message: Chat):
        """Add a message to the FAISS index."""
        embedding_array = np.array([embed], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        self.faiss_index.add(embedding_array) # type: ignore
        self.conversation_data.append(message)

    async def save_message(self, chat_id: int, content: str, role: str, ):
        """Saves messages to the database."""
        message = await self.db.save_message(
            chat_id=chat_id, 
            role=role,
            message=content, 
            model_name=self.ai_model
            )
        
        embed = await self.db.save_embedding(
            chat_id=chat_id, 
            message_id=message.id,  # type: ignore
            vector=await self.embed_text(content),
            )
        await self.add_index(embed.vector, message) # type: ignore
        return message, embed
    
    async def chat(
        self,
        chat_id: int,
        content: str,
    ):
        """Generates a message from the AI model.
            it loads the conversation into the FAISS index if it is not already loaded
            search for the most relevant message in the conversation and use it as a prompt with the new message(content)
            saves the content and response to the database
        Args:
            chat_id (int): The ID of the chat.
            content (str): The content of the message.
        """

        if self.faiss_index.ntotal == 0:
            await self.load_conversation(chat_id)

        D, I = await self.search_memory(content, k=5)
        await self.search_relevant(I, content=content)
            
        response = await self.client.chat(
            model=self.ai_model,
            messages=self.history,
            stream=True
            )
        self.logger.info(f"Generated response for chat {chat_id}")

        message_response = []
        async for message in response:
            message_response.append(message.message.content)
            yield message


        user_message, user_embedding = await self.save_message(
            chat_id=chat_id, 
            content=content,
            role="user"
            )
        if user_message or user_embedding:
            self.logger.info(f"Saved user message for chat {chat_id}")
        else:
            self.logger.warning(f"Failed to save user message for chat {chat_id}")
            
        if message_response:
            ai_message, ai_embedding = await self.save_message(
                chat_id=chat_id, 
                content="".join(message_response),
                role="assistant"
                )
        
            if ai_message and ai_embedding:
                self.logger.info(f"Saved AI message for chat {chat_id}")
            else:
                self.logger.warning(f"Failed to save AI message for chat {chat_id}")
        else:
            self.logger.warning(f"Failed to generate response for chat {chat_id}")
        yield ai_message
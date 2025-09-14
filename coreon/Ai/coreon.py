import ollama
from ollama import ChatResponse

import faiss
import json
import numpy as np
import os

from typing import Iterator, List, Dict, Union

from coreon.data.basemodels import Session, Conversation, Embedding
from coreon.data.database import Database
from coreon.utils.utils import setup_logger

logger = setup_logger(__name__)


class Coreon:
    """Simple wrapper for Ollama chat client."""
    
    def __init__(self, db: Database, ai_model: str = "llama3.1", embed_model: str = "nomic-embed-text", host: str = "http://localhost:11434"):
        self.db = db
        self.host = host
        self.client = ollama.Client(host=host)
        self.ai_model = ai_model
        self.embedding_model = embed_model
        self.faiss_index = None
        self.history = []
        self.conversation_data = []
        self.logger = setup_logger(__name__)
        
        self.logger.info("Coreon AI initialized")  
                
        

    def load_memory(self, session_id: int):
        # This is a placeholder for your database logic
        # self.history = self.db.get_conversation(session_id=session_id)
        conversation_data = np.array(self.db.get_conversation(session_id=session_id)).astype(np.float32)
        for conversation in conversation_data:
            self.history.append({"role": conversation.role, "content": conversation.message})
        self.conversation_data = conversation_data
        self.faiss_index = faiss.IndexFlatL2(self.conversation_data.shape[1])
        self.faiss_index.add(conversation_data) # type: ignore


    def search_memory(self, query: str, k: int = 5) -> List[Dict[str, Union[int, str, float]]]:
        """Searches the FAISS index for relevant memories."""
        if self.faiss_index is None:
            return []
        
        query_embedding = self.embed_text(query)
        distances, indices = self.faiss_index.search(query_embedding, k=k) # type: ignore
        
        results = []
        for i, idx in enumerate(indices[0]):
            results.append({
                "content": self.history[idx]["content"],
                "distance": distances[0][i]
            })
        return results
    
    def embed_text(self, text: str):
        """Generates an embedding for the given text."""
        return np.array(self.client.embeddings(model=self.embedding_model, prompt=text)['embedding']).astype(np.float32)

    # async def chat(
    #     self,
    #     content: str,
    #     user,
    #     channel_id: int,
    #     mommy_mode: bool = False,
    # ):
    #     # This is a placeholder for your chat logic
    #     response = await self.client.chat(
    #         model=self.model,
    #         messages=self.history,
    #         prompt=f"[Name: {user.display_name}]: {content}",)
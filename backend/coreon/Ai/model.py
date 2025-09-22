from ollama import AsyncClient
from typing import Optional
from coreon.utils.log import setup_logger

logger = setup_logger(__name__)

class AiModel:
    def __init__(
        self, 
        model: Optional[str] = None, 
        embedding_model: Optional[str] = None, 
        host: str = "http://localhost:11434"
        ):
        self.client = AsyncClient(host=host)
        self.model: Optional[str] = model
        self.embedding_model: Optional[str] = embedding_model
        self.logger = logger
        
    async def chat(
        self,
        history: list[dict[str, str]],
        stream: bool = False
    ):
        """Generates a message from the AI model.
            it loads the conversation into the FAISS index if it is not already loaded
            search for the most relevant message in the conversation and use it as a prompt with the new message(content)
            saves the content and response to the database
        Args:
            history (list[dict[str, str]]): The conversation history.
            stream (bool): Whether to stream the response or not.
        """
        if self.model is None:
            self.logger.error("No model selected")
            raise Exception("No model selected")
        
        return await self.client.chat(
            model=self.model,
            messages=history,
            stream=stream
        )
            
    async def embed_text(self, text: str):
        """Generates an embedding for the given text."""
        try:
            if self.embedding_model is None:
                self.logger.error("No embedding model selected")
                raise Exception("No embedding model selected")
            
            response = await self.client.embeddings(
                model=self.embedding_model, prompt=text
            )
            return response.embedding
        except Exception as e:
            self.logger.error(f"Error getting embedding: {e}")
            raise e
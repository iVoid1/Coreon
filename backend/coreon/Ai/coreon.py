import faiss
import numpy as np
from ollama import ChatResponse
from typing import Optional, AsyncIterator, Union, List
from collections import deque
from rich import print
from coreon.data import Message
from coreon.Ai import AiModel
from coreon.utils import setup_logger

logger = setup_logger(__name__)


class Coreon:
    """Coreon AI Module - simplified and flexible model management"""
    
    
    def __init__(
        self, 
        ai_model: Optional[Union[str, List[AiModel]]] = None,
        embedding_model: Optional[Union[str, List[AiModel]]] = None,
        auto_create_chat: bool = False,
    ):
        """Initialize Coreon AI Module."""
        # --- Memory Stores ---
        self.messages: deque[Message] = deque()
        self.embeddings = np.array([], dtype=np.float32) 
        
        # --- Model Setup ---
        self.ai_models: dict[str, AiModel] = {}
        self.embed_models: dict[str, AiModel] = {}
        self.main_ai_model: Optional[str] = None
        self.main_embed_model: Optional[str] = None
        
        # --- FAISS & Chat Data ---
        self.dimension = 768
        self.faiss_index = faiss.IndexFlatL2(self.dimension)
        
        self.history: list[dict] = []
        
        # --- Settings & Logger ---
        self.auto_create_chat = auto_create_chat
        self.logger = setup_logger(__name__)
        
        # Setup models
        self._setup_models(ai_model, embedding_model)
        
        self.logger.info("Coreon AI Module initialized.")

    #-------------------------------------
    #--- Helper Functions with AiModel ---
    #-------------------------------------

    def _process_models(self, models_input, is_embedding: bool = False):
        """General helper to process model input (str or list[str/AiModel])"""
        models_dict = {}
        main_model_name = None
        
        if models_input is None: return models_dict, None
        models_list = [models_input] if isinstance(models_input, (str, AiModel)) else models_input
        
        for model in models_list:
            if model is None: continue
            
            if isinstance(model, str):
                model_name = model
                model_obj = AiModel(model=model_name) if not is_embedding else AiModel(embedding_model=model_name)
            elif isinstance(model, AiModel):
                model_name = model.model if not is_embedding else model.embedding_model
                model_obj = model
            else: continue

            if model_name:
                models_dict[model_name] = model_obj
                if main_model_name is None: main_model_name = model_name
                    
        return models_dict, main_model_name

    def _setup_models(
        self, 
        ai_model: Optional[Union[str, List[str], List[AiModel]]],
        embedding_model: Optional[Union[str, List[str], List[AiModel]]]
    ):
        """Setup models in a simplified way"""
        self.ai_models, self.main_ai_model = self._process_models(ai_model, is_embedding=False)
        self.embed_models, self.main_embed_model = self._process_models(embedding_model, is_embedding=True)
        self.logger.info(f"AI models: {list(self.ai_models.keys())}")
        self.logger.info(f"Embed models: {list(self.embed_models.keys())}")

    def _get_ai_model(self, model_name: Optional[str] = None) -> str:
        """Get AI model name (uses main model if not specified)"""
        if model_name and model_name in self.ai_models:
            return model_name
        elif self.main_ai_model:
            self.logger.info(f"Using main AI model: {self.main_ai_model}")
            return self.main_ai_model
        else:
            raise ValueError("No AI model available")

    def _get_embed_model(self, model_name: Optional[str] = None) -> str:
        """Get embedding model name (uses main model if not specified)"""
        if model_name and model_name in self.embed_models:
            return model_name
        elif self.main_embed_model:
            self.logger.info(f"Using main embedding model: {self.main_embed_model}")
            return self.main_embed_model
        else:
            raise ValueError("No embedding model available")
    
    #-------------------------------
    #--- Memory Search Functions ---
    #-------------------------------
    
    
    async def save_memory(self, content: str, embedding, role: str):
        """Save message to memory"""
        message = Message(content=content, role=role)
        self.messages.append(message)
        
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        self.faiss_index.add(embedding_array) # type: ignore
        
        self.embeddings = np.append(self.embeddings, embedding_array)
        
    async def search_memory(
        self, 
        query: str, 
        embedding_model: Optional[str] = None, 
        k: int = 5
    ):
        """Search memory using FAISS"""
        
        try:
            # Use specified model or main model
            embed_model_name = self._get_embed_model(embedding_model)
            
            query_embedding = await self.embed_models[embed_model_name].embed_text(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)

            distances, indices = self.faiss_index.search(query_array, k=k) # type: ignore
            print(indices)
            print(self.faiss_index.ntotal)
            self.logger.info(f"Found {len(indices[0])} relevant messages")
            return indices, distances
 
        except Exception as e:
            self.logger.error(f"Error during memory search: {e}")
            return np.array([[]]), np.array([[]])

    async def search_relevant(self, indices: np.ndarray, content: str = "", user_role: str = "user"):
        """Build history from relevant messages"""
        self.history = []
        
        if not indices.any():
            self.logger.warning(f"No relevant messages found")
            if content:
                self.history.append({"role": user_role, "content": content})
            return
        # Add relevant messages
        for idx in indices[0]:
            idx: int
            if 0 <= idx < len(self.messages):
                message_obj = self.messages[idx]
                self.logger.info(f"Found relevant message: {message_obj}")
                self.history.append({
                    "role": message_obj.role,
                    "content": message_obj.content
                })
                self.logger.info(f"Added relevant message to history: {message_obj}")

        # Add new message
        if content:
            self.history.append({"role": user_role, "content": content})
            self.logger.info(f"Added new message to history: {content}\nhistory: {self.history}")
        else:
            self.logger.warning("No content provided for search_relevant")


    #---------------------------------------------
    #--- Function for interacting with AiModel ---
    #---------------------------------------------


    async def model_chat(
        self,
        content: list[dict],
        model_name: str,
        stream: bool = False
    ):

        """Chat with AI model"""
        model_name = self._get_ai_model(model_name)
        return await self.ai_models[model_name].chat(content, stream=stream)

    async def embed_text(
        self, 
        text: str, 
        embedding_model: Optional[str] = None
    ):
        """Get embedding for text"""
        embed_model_name = self._get_embed_model(embedding_model)
        return await self.embed_models[embed_model_name].embed_text(text)

    async def chat(
        self,
        content: str,
        ai_model: Optional[str] = None,
        embed_model: Optional[str] = None,
        stream: bool = False,
        k: int = 5,
        user_role: str = "user"
    ):
        """Chat with AI - simplified and flexible"""
            
        # Search for relevant messages
        indices, _ = await self.search_memory(
            query=content, 
            embedding_model=embed_model, 
            k=k
        )
        await self.search_relevant(indices, content=content, user_role=user_role)

        # Get model name
        ai_model_name = self._get_ai_model(ai_model)
        
        # Send to AI
        ai_response = await self.ai_models[ai_model_name].chat(self.history, stream=stream)
        complete_response = []
        
        # Process response
        if stream:
            async for response in self._stream_response(ai_response_stream=ai_response):
                yield response
                complete_response.append(response.message.content)
                
        elif isinstance(ai_response, ChatResponse):
            yield ai_response
            
        # Save user message to memory
        await self.save_memory(
            content=content, 
            embedding=await self.embed_text(text=content, embedding_model=embed_model),
            role=user_role
        )
        await self.save_memory(
            content="".join(complete_response), 
            embedding=await self.embed_text(text="".join(complete_response), embedding_model=embed_model),
            role="assistant"
        )
        
        print(self.__dict__)

    async def _stream_response(self, ai_response_stream: Union[AsyncIterator[ChatResponse], ChatResponse]) -> AsyncIterator[ChatResponse]:
        """Handle streaming response"""
        if isinstance(ai_response_stream, ChatResponse):
            return
        # Return each part of the stream
        async for streaming_message in ai_response_stream:
            yield streaming_message
        

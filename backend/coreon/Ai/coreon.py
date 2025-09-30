import faiss
import numpy as np
from ollama import ChatResponse
from typing import Optional, AsyncIterator, Union, List
from collections import deque

from coreon.data import Database
from coreon.data import Message, Embedding
from coreon.Ai import AiModel
from coreon.utils import setup_logger

logger = setup_logger(__name__)


class Coreon:
    """Coreon AI Module - simplified and flexible model management"""
    
    # ... (Keep all original imports and class definition)

    # Define max history size for Volatile Mode
    MAX_VOLATILE_HISTORY = 50 
    
    def __init__(
        self, 
        db: Optional[Union[Database, str]] = None, # Made DB Optional
        ai_model: Optional[Union[str, List[AiModel]]] = None,
        embedding_model: Optional[Union[str, List[AiModel]]] = None,
        dimension: int = 768,
        auto_create_chat: bool = False,
    ):
        """Initialize Coreon AI Module."""
        
        # --- 1. Memory Mode Setup ---
        if isinstance(db, (Database, str)):
            self.db = Database(db) if isinstance(db, str) else db
            self.memory_mode = False # False for Persistent (DB is available)
        else:
            self.db = None
            self.memory_mode = True # True for Volatile (RAM only)
        
        # --- 2. Unified Memory Stores (Source of Truth) ---
        # 💡 Messages: Deque for Volatile, List for Persistent
        max_len = self.MAX_VOLATILE_HISTORY if self.memory_mode else 0
        self.messages: deque[Message] | List[Message] = deque(maxlen=max_len) if self.memory_mode else []
        
        # 💡 Embeddings: The unified NumPy array for FAISS (Original name kept)
        self.embeddings = np.array([], dtype=np.float32) 
        
        # --- 3. Model Setup (Unchanged) ---
        self.ai_models: dict[str, AiModel] = {}
        self.embed_models: dict[str, AiModel] = {}
        self.main_ai_model: Optional[str] = None
        self.main_embed_model: Optional[str] = None
        
        # --- 4. FAISS & Chat Data ---
        self.dimension = dimension
        self.chat_id: Optional[int] = None
        self.faiss_index = faiss.IndexFlatL2(dimension)
        
        self.history: list[dict] = []
        
        # --- 5. Settings & Logger (Unchanged) ---
        self.auto_create_chat = auto_create_chat
        self.user_role = "user"
        self.assistant_role = "assistant"
        self.logger = setup_logger(__name__)
        
        # Setup models (Unchanged)
        self._setup_models(ai_model, embedding_model)
        
        self.logger.info(f"Coreon AI initialized successfully in {'volatile' if self.memory_mode else 'persistent'} mode")

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

    #--------------------------------------
    #--- Helper Functions with Database ---
    #--------------------------------------

    async def init_database(self):
        """Setup database"""
        
        if self.db is None:
            self.logger.error("Database is not initialized")
            return
                  
        if isinstance(self.db, str):
            self.db = Database(self.db)

        self.logger.info("Initializing database...")
        await self.db.init_db()
    
    async def validate_chat_id(self, chat_id: Optional[int], create_if_not_found: bool = False, title: str = "Auto-created chat") -> Optional[int]:
        """
        Validate chat ID.

        Args:
            chat_id (int): The chat ID to validate.
            title (str, optional): The title of the chat. Defaults to "Auto-created chat".
        
        Returns:
            Optional[int]: The validated chat ID or None if validation fails.
        """
        
        try:
            if self.db is None:
                self.logger.error("Database is not initialized")
                return None

            if chat_id is None:
                self.logger.error("Chat ID is None")
                return None
            
            chat_exists = await self.db.get_chat(chat_id)
            
            if chat_exists:
                self.logger.info(f"Chat {chat_id} exists and is valid")
                return chat_id
            
            if self.auto_create_chat or create_if_not_found:
                self.logger.info(f"Chat {chat_id} not found, creating new chat with title: '{title}'")
                new_chat = await self.db.create_chat(title=title)
                self.logger.info(f"Created new chat with ID: {new_chat.id}")
                return new_chat.id # type: ignore
            else:
                self.logger.warning(f"Chat {chat_id} not found and auto_create_chat is disabled")
                return None
                
        except Exception as e:
            self.logger.error(f"Error validating chat_id {chat_id}: {e}")
            return None

    async def load_vectors(self, chat_id: Optional[int] = None):
        """Load vectors for conversation"""
        if self.db is None:
            self.logger.error("Database is not initialized")
            return np.array([])
        
        embeddings = []
        target_chat_id = chat_id or self.chat_id
        
        if not target_chat_id:
            self.logger.warning("No chat id provided")
            return np.array([])
            
        for embedding in await self.db.get_embeddings(chat_id=target_chat_id):
            embeddings.append(embedding.vector)
                
        self.embeddings = np.array(embeddings, dtype=np.float32)
        return self.embeddings

    async def load_message(self, chat_id: Optional[int] = None):
        """
        Loads messages and embeddings from DB or uses RAM data (Volatile).
        Populates self.conversation_data and self.embeddings.
        Then loads vectors into FAISS index.
        """
        
        # 1. Reset FAISS and Unified Vectors (self.embeddings)
        self.faiss_index = faiss.IndexFlatL2(self.dimension)
        self.embeddings = np.array([], dtype=np.float32) # <-- Resetting the unified vector array
        
        # 2. Determine source and load data
        if not self.memory_mode: # Persistent Mode (DB)
            
            if self.db is None:
                self.logger.error("Database is not initialized in persistent mode")
                return
            
            validated_chat_id = await self.validate_chat_id(chat_id=chat_id)
            if validated_chat_id is None:
                self.logger.warning(f"Chat validation failed.")
                return
            
            self.chat_id = validated_chat_id
            
            # Load messages & reassign conversation_data as a regular List[Message]
            self.messages = await self.db.get_messages(chat_id=self.chat_id)
            self.logger.info(f"Messages loaded for chat {self.chat_id}")
            
            # Load vectors directly into self.embeddings
            await self.load_vectors(chat_id=self.chat_id)

        # 3. Load vectors into FAISS
        if self.embeddings.size > 0:
            self.faiss_index.add(self.embeddings) # type: ignore
            self.logger.info(f"Loaded {self.embeddings.shape[0]} embeddings into FAISS")
        else:
            self.logger.warning(f"No embeddings found for current session")
            
    async def _save_message(
        self, 
        chat_id: Optional[int], 
        role: str, 
        content: str, 
        ai_model: Optional[str] = None, 
        embed_model: Optional[str] = None
    ):
        """
        Saves one message to DB (if available) AND updates the unified RAM variables.
        """
        
        # 1. Create embedding vector first
        ai_model_name = self._get_ai_model(ai_model)
        embed_model_name = self._get_embed_model(embed_model)
        
        embedding_vector = await self.embed_models[embed_model_name].embed_text(content)
        
        message = None
        embedding = None
        
        chat_id = await self.validate_chat_id(chat_id=chat_id, create_if_not_found=True)
        
        # 2. Try to Save message/embedding to DB (Persistent Logic)
        if (not self.memory_mode) and (self.db is not None) and (chat_id is not None):
            # Save message
            message = await self.db.save_message(
                chat_id=chat_id, 
                role=role,
                content=content, 
                model_name=ai_model_name
            )
            
            # Create and save embedding
            embedding_vector = await self.embed_models[embed_model_name].embed_text(content)
            embedding = await self.db.save_embedding(
                chat_id=chat_id,
                message_id=message.id, # type: ignore
                embedding_model=embed_model_name,
                vector=embedding_vector
            )            
        
        # 3. Create a Message object if DB save failed or if in Volatile Mode
        if message is None:
            # Placeholder IDs for RAM/Volatile Mode
            message = Message(
                chat_id=-1,
                role=role,
                content=content,
                model_name=ai_model_name
                )
        if embedding is None:
            # Placeholder IDs for RAM/Volatile Mode
            embedding = Embedding(
                message_id=message.id,
                embedding_model=embed_model_name,
                vector=embedding_vector
                )
        # 4. Update Unified Variables and FAISS (Crucial Step: Always happens)
        
        # Append to the unified message list/deque
        self.messages.append(message)

        # Update self.embeddings and FAISS Index
        embedding_array = np.array([embedding_vector], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        
        if self.embeddings.size == 0:
            self.embeddings = embedding_array
        else:
            self.embeddings = np.append(self.embeddings, embedding_array, axis=0) # <-- Appending to self.embeddings

        self.faiss_index.add(embedding_array) # type: ignore
        
        return message, embedding

    async def save_messages(
        self,
        chat_id: Optional[int],
        user_content: str,
        ai_content: str,
        ai_model: str,
        embed_model: Optional[str],
        user_role: str,
        assistant_role: str
    ):
        """Save complete conversation both user and AI messages"""
        
        # Save user message
        await self._save_message(
            chat_id=chat_id,
            role=user_role,
            content=user_content,
            ai_model=ai_model,
            embed_model=embed_model
        )
        
        # Save AI response
        if ai_content:
            await self._save_message(
                chat_id=chat_id, 
                role=assistant_role,
                content=ai_content,
                ai_model=ai_model,
                embed_model=embed_model
            )
            self.logger.info(f"Messages saved for chat {chat_id}")
        else:
            self.logger.error(f"No AI content to save for chat {chat_id}")
        return
    
    #---------------------------
    #--- Function with faiss ---
    #---------------------------
    
    async def search_memory(
        self, 
        query: str, 
        chat_id: Optional[int] = None, 
        embedding_model: Optional[str] = None, 
        k: int = 5
    ):
        """Search memory using FAISS"""
        
        if chat_id is None:
            self.logger.info("No chat_id provided, using simple chat mode")
        else:
            # Load messages if not loaded
            if (self.faiss_index is None 
                or self.faiss_index.ntotal == 0 
                or self.chat_id != chat_id
                ):
                await self.load_message(chat_id=chat_id)
        
        try:
            # Use specified model or main model
            embed_model_name = self._get_embed_model(embedding_model)
            
            query_embedding = await self.embed_models[embed_model_name].embed_text(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)

            distances, indices = self.faiss_index.search(query_array, k=k) # type: ignore
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

    async def add_index(self, embed: list, message_obj: Message):
        """Add new message to FAISS index"""
        embedding_array = np.array([embed], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        self.faiss_index.add(embedding_array) # type: ignore
        self.messages.append(message_obj)

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
        chat_id: Optional[int] = None,
        user_role: str = "user",
        assistant_role: str = "assistant"
    ):
        """Chat with AI - simplified and flexible"""
            
        # Search for relevant messages
        indices, _ = await self.search_memory(
            chat_id=chat_id, 
            query=content, 
            embedding_model=embed_model, 
            k=k
        )
        await self.search_relevant(indices, content=content, user_role=user_role)

        # Get model name
        ai_model_name = self._get_ai_model(ai_model)
        
        # Send to AI
        ai_response = await self.ai_models[ai_model_name].chat(self.history, stream=stream)
        self.logger.info(f"Generated response for chat {chat_id or 'simple mode'} using {ai_model_name}")

        # Process response
        if stream:
            async for response in self._handle_streaming_response(
                ai_response_stream=ai_response,
                chat_id=chat_id,
                user_content=content,
                ai_model=ai_model_name,
                embed_model=embed_model,
                user_role=user_role,
                assistant_role=assistant_role
            ):
                yield response
        else:
            result = await self._handle_non_streaming_response(
                ai_response=ai_response,
                chat_id=chat_id,
                user_content=content,
                ai_model=ai_model_name,
                embed_model=embed_model,
                user_role=user_role,
                assistant_role=assistant_role
            )
            yield result

    async def _handle_streaming_response(
        self, 
        ai_response_stream: AsyncIterator[ChatResponse] | ChatResponse,
        chat_id: Optional[int], 
        user_content: str,
        ai_model: str,
        embed_model: Optional[str],
        user_role: str,
        assistant_role: str
    ) -> AsyncIterator[ChatResponse]:
        """Handle streaming response"""
        if isinstance(ai_response_stream, ChatResponse):
            self.logger.error(f"Failed to generate response for chat {chat_id}")
            return
        response_content_parts = []
        
        # Return each part of the stream
        async for streaming_message in ai_response_stream:
            ai_content = streaming_message.message.content
            if ai_content:
                response_content_parts.append(ai_content)
            yield streaming_message
        
        # Save messages
        complete_ai_response = "".join(response_content_parts)
        await self.save_messages(
            chat_id=chat_id,
            user_content=user_content,
            ai_content=complete_ai_response,
            ai_model=ai_model,
            embed_model=embed_model,
            user_role=user_role, 
            assistant_role=assistant_role
        )

    async def _handle_non_streaming_response(
        self, 
        ai_response: ChatResponse | AsyncIterator[ChatResponse], 
        chat_id: Optional[int], 
        user_content: str,
        ai_model: str,
        embed_model: Optional[str],
        user_role: str,
        assistant_role: str
    ) -> Optional[ChatResponse]:
        """Handle non-streaming response"""
        if isinstance(ai_response, AsyncIterator):
            self.logger.error(f"Failed to generate response for chat {chat_id}")
            return
        if not ai_response or not ai_response.message.content:
            self.logger.error(f"Failed to generate response for chat {chat_id}")
            return None
            
        complete_ai_response = ai_response.message.content
        # Save messages
        await self.save_messages(
            chat_id=chat_id,
            user_content=user_content,
            ai_content=complete_ai_response,
            ai_model=ai_model,
            embed_model=embed_model,
            user_role=user_role, 
            assistant_role=assistant_role
        )
        
        return ai_response
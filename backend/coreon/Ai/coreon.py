import faiss
import numpy as np
from ollama import ChatResponse
from typing import Optional, AsyncIterator, Union, List

from coreon.data import Database
from coreon.data import Chat, ContentType
from coreon.Ai import AiModel
from coreon.utils import setup_logger

logger = setup_logger(__name__)


class Coreon:
    """Coreon AI Module - simplified and flexible model management"""
    
    def __init__(
        self, 
        db: Union[Database, str], 
        ai_model: Optional[Union[str, List[AiModel]]] = None,
        embedding_model: Optional[Union[str, List[AiModel]]] = None,
        dimension: int = 768,
    ):
        """Initialize Coreon AI Module."""
        
        # Setup database
        self.db = Database(db) if isinstance(db, str) else db
        
        # Setup models
        self.ai_models: dict[str, AiModel] = {}
        self.embed_models: dict[str, AiModel] = {}
        self.main_ai_model: Optional[str] = None
        self.main_embed_model: Optional[str] = None
        
        # Setup FAISS
        self.dimension = dimension
        self.chat_id: Optional[int] = None
        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.embeddings = np.array([], dtype=np.float32)
        
        # Conversation data
        self.history: list[dict] = []
        self.conversation_data = []
        
        # Logger
        self.logger = setup_logger(__name__)
        
        # Setup models
        self._setup_models(ai_model, embedding_model)
        
        self.logger.info("Coreon AI initialized successfully")

    def _setup_models(
        self, 
        ai_model: Optional[Union[str, List[str], List[AiModel]]],
        embedding_model: Optional[Union[str, List[str], List[AiModel]]]
    ):
        """Setup models in a simplified way"""
        
        # Setup AI models
        if ai_model:
            if isinstance(ai_model, str):
                model_obj = AiModel(model=ai_model)
                self.ai_models[ai_model] = model_obj
                self.main_ai_model = ai_model

            elif isinstance(ai_model, list):
                for model in ai_model:
                    if model is None:
                        continue

                    if isinstance(model, str):
                        model_name = model
                        model_obj = AiModel(model=model)
                        self.ai_models[model_name] = model_obj

                        if self.main_ai_model is None:
                            self.main_ai_model = model_name

                    elif isinstance(model, AiModel):
                        if model.model is None:
                            continue
                        self.ai_models[model.model] = model
                        if self.main_ai_model is None:
                            self.main_ai_model = model.model
        
        # Setup Embedding models
        if embedding_model:
            if isinstance(embedding_model, str):
                model_obj = AiModel(embedding_model=embedding_model)
                self.embed_models[embedding_model] = model_obj
                self.main_embed_model = embedding_model

            elif isinstance(embedding_model, list):
                for embed_model in embedding_model:
                    if embed_model is None:
                        continue

                    if isinstance(embed_model, str):
                        embed_model_name = embed_model
                        embed_model_obj = AiModel(embedding_model=embed_model)
                        self.embed_models[embed_model_name] = embed_model_obj

                        if self.main_embed_model is None:
                            self.main_embed_model = embed_model_name

                    elif isinstance(embed_model, AiModel):
                        if embed_model.embedding_model is None:
                            continue
                        self.embed_models[embed_model.embedding_model] = embed_model
                        if self.main_embed_model is None:
                            self.main_embed_model = embed_model.embedding_model

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

    async def init_database(self):
        """Setup database"""
        await self.db.init_db()

    async def load_conversation(self, chat_id: int):
        """Load conversation into FAISS index"""
        self.chat_id = chat_id
        self.conversation_data = await self.db.get_conversation(chat_id=chat_id)
        self.logger.info(f"Conversation loaded for chat {chat_id}")
        
        self.faiss_index = faiss.IndexFlatL2(self.dimension)
        await self.load_vectors(chat_id=chat_id)
        
        if not self.embeddings.size:
            self.logger.warning(f"No embeddings found for chat {chat_id}")
            return
            
        self.faiss_index.add(self.embeddings) # type: ignore
        self.logger.info(f"Loaded {self.embeddings.shape[0]} embeddings into FAISS")

    async def load_vectors(self, chat_id: Optional[int] = None):
        """Load vectors for conversation"""
        embeddings = []
        target_chat_id = chat_id or self.chat_id
        
        if not target_chat_id:
            self.logger.warning("No chat id provided")
            return np.array([])
            
        for embedding in await self.db.get_embeddings(chat_id=target_chat_id):
            embeddings.append(embedding.vector)
                
        self.embeddings = np.array(embeddings, dtype=np.float32)
        return self.embeddings

    async def search_memory(
        self, 
        chat_id: int, 
        query: str, 
        embedding_model: Optional[str] = None, 
        k: int = 5
    ):
        """Search memory using FAISS"""
        
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            self.logger.warning("FAISS index empty, loading conversation...")
            await self.load_conversation(chat_id)
        
        try:
            # Use specified model or main model
            embed_model_name = self._get_embed_model(embedding_model)
            
            query_embedding = await self.embed_models[embed_model_name].embed_text(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)

            distances, indices = self.faiss_index.search(query_array, k=k) # type: ignore
            self.logger.info(f"Found {len(indices[0])} relevant messages")
            return distances, indices
 
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
            if 0 <= idx < len(self.conversation_data):
                message = self.conversation_data[idx]
                self.history.append({
                    "role": message.role,
                    "content": message.message
                })

        # Add new message
        if content:
            self.history.append({"role": user_role, "content": content})
            self.logger.info(f"Added new message to history: {content}\nhistory: {self.history}")
        else:
            self.logger.warning("No content provided for search_relevant")

    async def add_index(self, embed: list, message: Chat):
        """Add new message to FAISS index"""
        embedding_array = np.array([embed], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        self.faiss_index.add(embedding_array) # type: ignore
        self.conversation_data.append(message)

    async def _save_message(
        self, 
        chat_id: int, 
        role: str, 
        content: str, 
        ai_model: Optional[str] = None, 
        embed_model: Optional[str] = None
    ):
        """Save one message to database and create embedding"""
        
        # Use specified models or main models
        ai_model_name = self._get_ai_model(ai_model)
        embed_model_name = self._get_embed_model(embed_model)
        
        # Save message
        message = await self.db.save_message(
            chat_id=chat_id, 
            role=role,
            message=content, 
            model_name=ai_model_name
        )
        
        # Create and save embedding
        embedding_vector = await self.embed_models[embed_model_name].embed_text(content)
        embedding = await self.db.save_embedding(
            chat_id=chat_id,
            content_type=ContentType.CONVERSATION,
            conversation_id=message.id, # type: ignore
            embedding_model=embed_model_name,
            vector=embedding_vector
        )
        
        # Add to FAISS index
        await self.add_index(embedding.vector, message) # type: ignore
        return message, embedding

    async def save_conversation(
        self,
        chat_id: int,
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
            self.logger.info(f"Conversation saved for chat {chat_id}")
        else:
            self.logger.error(f"No AI content to save for chat {chat_id}")
    
    
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
        if chat_id is None:
            self.logger.warning("No chat_id provided, cannot load conversation")
            self.history = [{"role": user_role, "content": content}]
        else:
            # Load conversation if not loaded
            if self.faiss_index is None or self.faiss_index.ntotal == 0:
                await self.load_conversation(chat_id)
            
            # Search for relevant messages
            distances, indices = await self.search_memory(
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

        self.logger.info(f"Generated response for chat {chat_id} using {ai_model_name}")

        # Process response
        if stream:
            async for message in self._handle_streaming_response(
                ai_response_stream=ai_response,
                chat_id=chat_id,
                user_content=content,
                ai_model=ai_model_name,
                embed_model=embed_model,
                user_role=user_role,
                assistant_role=assistant_role
            ):
                yield message
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

    async def embed_text(
        self, 
        text: str, 
        embedding_model: Optional[str] = None
    ):
        """Get embedding for text"""
        embed_model_name = self._get_embed_model(embedding_model)
        return await self.embed_models[embed_model_name].embed_text(text)

    async def _handle_streaming_response(
        self, 
        ai_response_stream: AsyncIterator[ChatResponse] | ChatResponse,
        chat_id: Optional[int], 
        user_content: str,
        ai_model: str,
        embed_model: Optional[str],
        user_role: str,
        assistant_role: str
    ):
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
        
        if chat_id is None:
            self.logger.warning("No chat_id provided, cannot save conversation")
            return
        
        # Save conversation
        complete_ai_response = "".join(response_content_parts)
        await self.save_conversation(
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
    ):
        """Handle non-streaming response"""
        if isinstance(ai_response, AsyncIterator):
            self.logger.error(f"Failed to generate response for chat {chat_id}")
            return
        if not ai_response or not ai_response.message.content:
            self.logger.error(f"Failed to generate response for chat {chat_id}")
            return None
            

        if chat_id is None:
            self.logger.warning("No chat_id provided, cannot save conversation")
            return ai_response
            
        complete_ai_response = ai_response.message.content
        # Save conversation
        await self.save_conversation(
            chat_id=chat_id,
            user_content=user_content,
            ai_content=complete_ai_response,
            ai_model=ai_model,
            embed_model=embed_model,
            user_role=user_role, 
            assistant_role=assistant_role
        )
        
        return ai_response

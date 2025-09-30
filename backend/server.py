import uvicorn
from fastapi import FastAPI, Request, Response, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import json
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from coreon import Coreon
from coreon.data import ChatBase, MessageBase
from coreon.utils import setup_logger

logger = setup_logger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Coreon Backend", version="0.2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
coreon = Coreon(
    db="coreon.sqlite", 
    ai_model="gemma3:12b", 
    embedding_model="nomic-embed-text:latest",
    faiss_index_dir="faiss_indices"
)


# Enhanced Pydantic models with validation
class ChatCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    
    @field_validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace')
        return v.strip()


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(default="user", pattern="^(user|assistant)$")
    
    @field_validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()


class ErrorResponse(BaseModel):
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status_code: int


async def startup_event():
    """Initialize database on startup"""
    try:
        await coreon.init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await coreon.db.close()
        logger.info("Database closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "0.2.0"
    }


# Get all chats
@router.get("/chats", response_model=List[ChatBase])
@limiter.limit("30/minute")
async def get_all_chats(request: Request):
    """Get all chats with pagination support"""
    try:
        all_chats = await coreon.db.get_all_chats()
        logger.info(f"Retrieved {len(all_chats)} chats")
        return [ChatBase.model_validate(chat) for chat in all_chats]
    except Exception as e:
        logger.error(f"Failed to get chats: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve chats"
        )


# Get a single chat by ID
@router.get("/chats/{chat_id}", response_model=ChatBase)
@limiter.limit("60/minute")
async def get_chat(chat_id: int, request: Request):
    """Get chat by ID"""
    try:
        chat = await coreon.db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return ChatBase.model_validate(chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat")


# Get all messages for a specific chat
@router.get("/chats/{chat_id}/messages", response_model=List[MessageBase])
@limiter.limit("60/minute")
async def get_messages(chat_id: int, request: Request):
    """Get all messages for a chat"""
    try:
        # Verify chat exists
        chat = await coreon.db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        messages = await coreon.db.get_message(chat_id)
        logger.info(f"Retrieved {len(messages)} messages for chat {chat_id}")
        return [MessageBase.model_validate(msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


# Create a new chat
@router.post("/chats", response_model=ChatBase, status_code=201)
@limiter.limit("10/minute")
async def create_chat(chat: ChatCreate, request: Request):
    """Create a new chat"""
    try:
        new_chat = await coreon.db.create_chat(title=chat.title)
        logger.info(f"Created chat {new_chat.id}: '{new_chat.title}'")
        return ChatBase.model_validate(new_chat)
    except Exception as e:
        logger.error(f"Failed to create chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat")


# Delete a chat
@router.delete("/chats/{chat_id}", status_code=200)
@limiter.limit("20/minute")
async def delete_chat(chat_id: int, request: Request):
    """Delete a chat by ID"""
    try:
        chat = await coreon.db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        success = await coreon.db.delete_chat(chat_id)
        if success:
            logger.info(f"Deleted chat {chat_id}")
            return {
                "detail": "Chat deleted successfully",
                "chat_id": chat_id,
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete chat")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat")


# Stream AI response
@router.post("/chats/{chat_id}/response")
@limiter.limit("20/minute")
async def stream_response(
    chat_id: int, 
    message: MessageCreate,
    request: Request
):
    """Stream AI response for a message"""
    
    # Validate chat exists
    try:
        chat = await coreon.db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate chat")
    
    async def response_generator():
        try:
            # Send user message confirmation
            yield json.dumps({
                'type': 'user_message',
                'content': message.content,
                'role': message.role,
                'timestamp': datetime.now().isoformat()
            }) + '\n'
            
            # Stream AI response
            async for item in coreon.chat(
                chat_id=chat_id,
                message=message.content,
                user_role=message.role,
                stream=True
            ):
                if item and item.message.content:
                    yield json.dumps({
                        'type': 'ai_chunk',
                        'content': item.message.content,
                        'timestamp': datetime.now().isoformat()
                    }) + '\n'
            
            # Send completion signal
            yield json.dumps({
                'type': 'done',
                'content': '',
                'timestamp': datetime.now().isoformat()
            }) + '\n'
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            yield json.dumps({
                'type': 'error',
                'content': str(e),
                'timestamp': datetime.now().isoformat()
            }) + '\n'
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            yield json.dumps({
                'type': 'error',
                'content': 'An error occurred while generating response',
                'timestamp': datetime.now().isoformat()
            }) + '\n'
    
    return StreamingResponse(
        response_generator(),
        media_type='application/x-ndjson'
    )


app.include_router(router)
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

if __name__ == "__main__":
    uvicorn.run(
        "server_improved:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
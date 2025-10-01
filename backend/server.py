import uvicorn
from fastapi import FastAPI, Request, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from coreon import Coreon
from coreon.data import Database, ChatBase, MessageBase
from coreon.utils import setup_logger

from typing import List, Optional
import json
from datetime import datetime


logger = setup_logger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Coreon Backend", version="0.2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

router = APIRouter()

coreon = Coreon(
    ai_model="gemma3:12b", 
    embedding_model="nomic-embed-text:latest", 
    auto_create_chat=True
)
database = Database(db_path="coreon.sqlite")

async def startup_event():
    """Initialize database on startup"""
    try:
        await database.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await database.close()
        logger.info("Database closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        
# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if coreon and database else "unhealthy",
        "coreon": "healthy" if coreon else "unhealthy",
        "database": "healthy" if database else "unhealthy",
        "timestamp": datetime.now(),
        "version": "0.2.0"
    }
    
# Stream AI response
async def _response_generator(
    message: MessageBase, 
    coreon: Coreon,
    database: Optional[Database] = None,
    chat_id: Optional[int] = None
    ):
    """Stream AI response for a chat."""
    try:
       
        yield json.dumps({
            'type': 'user_message',
            'content': message.content,
            'role': message.role,
            'timestamp': datetime.now().isoformat()
        }) + '\n'
        
        response = [] 
        async for item in coreon.chat(
            content=message.content,
            user_role=message.role,
            stream=True
            ):
            response.append(item.message.content) # type: ignore
            yield json.dumps({
                'type': 'ai_chunk',
                'content': item.message.content, # type: ignore
                'timestamp': datetime.now().isoformat()
            }) + '\n'

        # Save chat history if database and chat_id are provided
        if database and chat_id:
            # Save user message
            await database.save_message(
                chat_id=chat_id,
                role=message.role,
                content=message.content,
            )
            # Save AI response
            await database.save_message(
                chat_id=chat_id,
                role="assistant",
                content="".join(response)
            )
            logger.info(f"Saved chat for chat_id {chat_id}")
       
        yield json.dumps({
            'type': 'done',
            'content': '',
            'timestamp': datetime.now().isoformat()
        }) + '\n'
            
    except ValueError as e:
        logger.error(f"Validation error during chat: {e}")
        yield json.dumps({
            'type': 'error',
            'content': str(e),
            'timestamp': datetime.now().isoformat()
        }) + '\n'
        
    except Exception as e:
        logger.error(f"Error during streaming chat: {e}")
        yield json.dumps({
            'type': 'error',
            'content': 'An error occurred while generating response',
            'timestamp': datetime.now().isoformat()
        }) + '\n'

# Temporary (RAM) chat
@router.post("/chat/response")
@limiter.limit("20/minute")
async def stream_volatile_response(
    request: Request,  # FIXED: Added request parameter
    message: MessageBase,
    ):
    """Stream AI response for a temporary (RAM) chat. Passes chat_id=None."""
    return StreamingResponse(
        _response_generator(message=message, coreon=coreon),
    )

# Persistent (DB) chat
@router.post("/chat/{chat_id}/response")  # FIXED: Changed from /chats/ to /chat/
@limiter.limit("20/minute")
async def stream_persistent_response(
    request: Request,  # FIXED: Added request parameter
    chat_id: int, 
    message: MessageBase,
    ):
    """Stream AI response for a persistent (DB) chat. Requires chat validation."""
    try:
        chat = await database.get_chat(chat_id)  # FIXED: Use 'chat' instead of overwriting 'chat_id'
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        logger.info(f"Retrieved chat {chat_id}")
    except HTTPException:
        logger.error(f"Failed to get chat {chat_id}")
        raise
    except Exception as e:
        logger.error(f"Failed to get chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat")
    
    return StreamingResponse(
        _response_generator(
            message=message,
            coreon=coreon,
            database=database,
            chat_id=chat.id  # FIXED: Use chat.id instead of chat_id.id # type: ignore
            ),
    )


# Get all chats
@router.get("/chat/all", response_model=List[ChatBase])
@limiter.limit("30/minute")
async def get_all_chats(request: Request):
    """Get all chats with pagination support"""
    try:
        all_chats = await database.get_all_chats()
        logger.info(f"Retrieved {len(all_chats)} chats")
        return [ChatBase.model_validate(chat) for chat in all_chats]
    except Exception as e:
        logger.error(f"Failed to get chats: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve chats"
        )


# Get a single chat by ID
@router.get("/chat/{chat_id}", response_model=ChatBase)
@limiter.limit("60/minute")
async def get_chat(request: Request, chat_id: int):  # FIXED: Added request parameter
    """Get chat by ID"""
    try:
        chat = await database.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return ChatBase.model_validate(chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat")


# Get all messages for a specific chat
@router.get("/chat/{chat_id}/messages", response_model=List[MessageBase])
@limiter.limit("60/minute")
async def get_messages(request: Request, chat_id: int):  # FIXED: Added request parameter
    """Get all messages for a chat"""
    try:
        chat = await database.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        messages = await database.get_messages(chat_id) 
        logger.info(f"Retrieved {len(messages)} messages for chat {chat_id}")
        return [MessageBase.model_validate(msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


# Create a new chat
@router.post("/chat/create", response_model=ChatBase, status_code=201)
@limiter.limit("10/minute")
async def create_chat(request: Request, chat: ChatBase):  # FIXED: Added request parameter
    """Create a new chat"""
    try:
        new_chat = await database.create_chat(title=chat.title)
        logger.info(f"Created chat {new_chat.id}: '{new_chat.title}'")
        return ChatBase.model_validate(new_chat)
    except Exception as e:
        logger.error(f"Failed to create chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat")


# Delete a chat
@router.delete("/chat/delete/{chat_id}", status_code=200)
@limiter.limit("20/minute")
async def delete_chat(request: Request, chat_id: int):  # FIXED: Added request parameter
    """Delete a chat by ID"""
    try:
        chat = await database.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        success = await database.delete_chat(chat_id)
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


app.include_router(router)
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
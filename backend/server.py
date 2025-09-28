import uvicorn
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from typing import List
import json
from datetime import datetime
from typing import Optional

from coreon import Coreon
from coreon.data import ChatBase, MessageBase
from coreon.utils import setup_logger

logger = setup_logger(__name__)

app = FastAPI(title="Coreon Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
coreon = Coreon(db="coreon.sqlite", ai_model="gemma3:12b", embedding_model="nomic-embed-text:latest")


async def startup_event():
    await coreon.init_database()

# --- ROUTES AFTER CORRECTION ---
# Get all chats
@router.get("/chats", response_model=List[ChatBase])
async def get_all_chats():
    """Get all chats"""
    try:
        logger.info(f"Retrieved chats")
        all_chats = await coreon.db.get_all_chats()
        return [ChatBase.model_validate(chat) for chat in all_chats]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get chats") from e

# Get a single chat by ID
@router.get("/chats/{chat_id}", response_model=ChatBase)
async def get_chat(chat_id: int):
    """Get chat by ID"""
    try:
        chat = await coreon.db.get_chat(chat_id)
        return ChatBase.model_validate(chat)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Chat not found") from e
    
# Get all messages for a specific chat
@router.get("/chats/{chat_id}/messages", response_model=List[MessageBase])
async def get_message(chat_id: int):
    """Get all messages for a chat"""
    try:
        messages = await coreon.db.get_message(chat_id)
        logger.info(f"Retrieved messages for chat {chat_id}")
        response = [MessageBase.model_validate(conv) for conv in messages]
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get messages") from e

# Create a new chat
@router.post("/chats", response_model=ChatBase)
async def create_chat(chat: ChatBase):
    """Create a new chat"""
    try:
        new_chat = await coreon.db.create_chat(title=chat.title)
        new_chat = ChatBase.model_validate(new_chat)
        logger.info(f"Created new chat with ID {new_chat}")
        return new_chat
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create chat") from e
        
@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int):
    """Delete a chat by ID"""
    try:
        await coreon.db.delete_chat(chat_id)
        logger.info(f"Deleted chat with ID {chat_id}")
        return {"detail": "Chat deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete chat") from e
   
@router.post("/chats/{chat_id}/response", response_class=StreamingResponse)
async def stream_response(chat_id, message: MessageBase):
    # Validation
    if not message.content.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    
    async def response_generator():
        yield json.dumps({'type': 'user_message', 'content': message.content, 'role': 'user'})
        
        async for item in coreon.chat(
            chat_id=chat_id,
            message=message.content,
            user_role=message.role,
            stream=True
        ):
            if item and item.message.content:
                logger.info(f"Streaming response: {item.message.content}")
                yield json.dumps({'type': 'ai_chunk', 'content': item.message.content})
        
        yield json.dumps({'type': 'done', 'content': ''})
    
    return StreamingResponse(response_generator())

app.include_router(router)
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", coreon.db.close)

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
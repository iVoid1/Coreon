from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
import asyncio

from coreon import Coreon
from coreon.data import Chat, ChatBase

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
    
@router.get("/chat/{chat_id}", response_model=ChatBase)
async def get_chat(chat_id: int):
    """Get chat by ID"""
    try:
        await coreon.db.connect()
        chat = await coreon.db.get_chat(chat_id)
        json_chat = ChatBase.model_validate(chat)
        return json_chat.model_dump()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Chat not found") from e

@router.post("/chat/all", response_model=ChatBase)
async def create_chat(chat: ChatBase):
    """Create a new chat"""
    try:
        new_chat = await coreon.db.get_all_chats()
        json_chats = [ChatBase.model_validate(chat) for chat in new_chat]
        return [json_chat.model_dump() for json_chat in json_chats]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create chat") from e
 
app.include_router(router)
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", coreon.db.close)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
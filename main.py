import asyncio

from coreon.data.database import Database, Conversation
from coreon.Ai.coreon import Coreon
from coreon.utils.log import setup_logger

logger = setup_logger(__name__)

def clear_screen():
    """Clear the console screen."""
    print("\033c", end="")

def get_user_input() -> str:
    """Get user input with prompt."""
    return input("\nYou: ").strip()

def print_response(content: str|None):
    """Print AI response."""
    print(f"Coreon: {content}", end="", flush=True)

async def main():
    logger.info("Starting Coreon...")
    # Initialize components
    db = Database("coreon/coreon.sqlite")
    await db.init_db()

    coreon = Coreon(db=db, ai_model="gemma3:12b", embed_model="nomic-embed-text:latest", dimension=768, host="http://localhost:11434")

    # Create Chat
    chat = await db.get_chat(chat_id=1)
    if chat is None:
        logger.error("Failed to create chat. Exiting.")
        chat = await db.create_chat(title="Coreon Chat")    
    logger.info(f"Chat started - Chat: {chat.id}")
    print("Chat with Coreon (type 'exit' to quit, 'clear' to clear screen)")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                logger.info("Chat ended.")
                break
            
            if user_input.lower() == "clear":
                clear_screen()
                continue
            
            #TODO: Get AI response
            print(f"Coreon: ", end="", flush=True)
            async for response in coreon.chat(
                                chat_id=chat.id,    # type: ignore
                                content=user_input
                                ):
                if isinstance(response, Conversation):
                    ai_response = response
                else:
                    print(response.message.content, end="", flush=True)
            print()
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import sys
from coreon import Coreon, setup_logger

logger = setup_logger(__name__)

def clear_screen():
    """Clear the console screen."""
    print("\033c", end="")

async def setup_chat():
    """Setup Coreon instance and get/create chat."""
    logger.info("Initializing Coreon...")
    
    coreon = Coreon(
        db="coreon.sqlite", 
        ai_model="gemma3:12b", 
        embedding_model="nomic-embed-text:latest"
    )
    
    await coreon.init_database()
    logger.info("Database initialized")
    
    # Try to get existing chat or create new one
    print("Setting up chat...")
    chat = await coreon.db.get_chat(chat_id=1)
    if chat is None:
        chat = await coreon.db.create_chat(title="Coreon Chat")
        logger.info(f"Created new chat: {chat.id}")
    else:
        logger.info(f"Using existing chat: {chat.id}")
    
    return coreon, chat

async def chat_loop(coreon: Coreon, chat):
    """Main chat interaction loop."""
    print("Chat with Coreon (type 'exit' to quit, 'clear' to clear screen)")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle exit command
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            # Handle clear command
            if user_input.lower() == "clear":
                clear_screen()
                continue
            
            # Process AI response
            print("Coreon: ", end="", flush=True)
            
            async for response in coreon.chat(
                chat_id=chat.id,
                content=user_input,
                stream=True
            ):
                print(response.message.content, end="", flush=True) # type: ignore
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n\nChat interrupted. Goodbye!")
            break
            
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            print(f"\nSorry, there was an error: {e}")
            continue

async def main():
    """Main application entry point."""
    try:
        coreon, chat = await setup_chat()
        await chat_loop(coreon, chat)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Application shutting down")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication interrupted")
        sys.exit(0)
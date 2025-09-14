from coreon.data.database import Database, Embedding
from coreon.Ai.coreon import Coreon
from coreon.utils.utils import setup_logger

logger = setup_logger(__name__)

def clear_screen():
    """Clear the console screen."""
    print("\033c", end="")

def get_user_input() -> str:
    """Get user input with prompt."""
    return input("\nYou: ").strip()

def print_response(content: str):
    """Print AI response."""
    print(f"Coreon: {content}")

def main():
    logger.info("Starting Coreon...")
    # Initialize components
    db = Database("sqlite:///coreon/coreon.sqlite")
    
    
    coreon = Coreon(db=db, ai_model="llama3.1")

    # Create session
    session = db.create_session("Chat Session")
    if not session:
        logger.error("Failed to create session. Exiting.")
        return
    
    logger.info(f"Chat started - Session: {session.id}")
    print("Chat with Coreon (type 'exit' to quit, 'clear' to clear screen)")
    
    while True:
        try:
            user_input = get_user_input()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                logger.info("Chat session ended")
                break
            
            if user_input.lower() == "clear":
                clear_screen()
                continue
            
            # Save user message
            db.save_message(
                session_id=session.id, # type: ignore
                role="user",
                content=user_input,
                model_name=coreon.ai_model)
            
            #TODO: Get AI response
            
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}")

if __name__ == "__main__":
    main()
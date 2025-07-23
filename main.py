from coreon.data.database import Database
from coreon.Ai.coreon import Coreon
from coreon.utils.logger import Logger

logger = Logger(__name__)

def main():
    db = Database(
        db_path="sqlite:///coreon/coreon.sqlite", # SQLite database path
        initialize_tables=True, # Create tables if they don't exist
        foreign_keys=True, # Enable enforce_sqlite_fk() function for SQLite foreign key enforcement
        echo=False# Enable SQLAlchemy echo for debugging
        )    
    
    session = db.create_session(title="Test Session", catch=False) # Create a new session
    if session:
        logger.info(f"Started new session: (ID: {session.id}, title: '{session.title}')")
    else:
        logger.warning("Failed to create a new session.")
        
    model = Coreon(model="llama3.1") # Initialize the Coreon model client
    logger.info(f"Using model: {model.model}")    

    while True:
        try:
            # Get user input
            print("\nType your message (or 'exit' to quit): ", end="")
            message = input("You: ").strip()
            if not message:
                continue
            if message.lower() == "exit":
                logger.info("Exiting the chat session.")
                break
            if message.lower() == "clear":
                logger.info("Clearing the console.")
                print("\033c", end="")
                continue
            
            # Fetch conversation and build context
            # conversation = db.fetch_conversation(session_id)
            # Convert Conversation objects to dict
            # conversations = [{"role": conv.role, "content": conv.message} for conv in conversation]
            # TODO: make a function for this
            # TODO: use the context builder to build the context

            # Generate response
            response = model._chat(message, stream=True)
            response_chat = ""
            print(f"Coreon: ")
            for chunk in response:
                print(chunk.message.content, end='', flush=True) # type: ignore
                response_chat += chunk.message.content # type: ignore
            print()
            
            # Save conversation
            if session is None:
                logger.error("No session found. Cannot save conversation.")
                continue
            
            db.insert_conversation(session.id, model.model, "user", message, ) # type: ignore
            db.insert_conversation(session.id, model.model, "assistant", response_chat, ) # type: ignore


        except KeyboardInterrupt:
            logger.warning("User interrupted the session.")
            break
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
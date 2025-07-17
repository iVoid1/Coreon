from coreon.data.database import Database

def main():
    db = Database("sqlite:///coreon/coreon.sqlite")
    db.initialize()
    session_id, session_title = db.create_session(title="My First Session")
    print(f"Created session: ID={session_id}, Title='{session_title}'")

if __name__ == "__main__":
    main()
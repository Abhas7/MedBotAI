import sys
import os

# Adjust path to import app modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.db.supabase import SupabaseDB, get_supabase_client

def test_supabase_connection():
    print("=" * 60)
    print("MEDBOT DATABASE CONNECTION TEST")
    print("=" * 60)
    
    missing = Config.validate()
    if missing:
        print(f"ERROR: Missing configuration variables: {', '.join(missing)}")
        print("Please set these variables in backend/.env before running this test.")
        sys.exit(1)
        
    try:
        # Check client init
        client = get_supabase_client()
        print("[OK] Supabase Client initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase Client: {str(e)}")
        sys.exit(1)
        
    test_email = "db_test_user@medbot.com"
    test_password = "hashed_pw_test_123"
    
    try:
        # 1. Clean up existing test user if any
        print("Cleaning up old test users if any...")
        existing_user = SupabaseDB.get_user_by_email(test_email)
        if existing_user:
            print("Found existing test user, deleting...")
            # Deleting user will cascade delete their sessions and messages
            client.table("users").delete().eq("id", existing_user["id"]).execute()
            print("[OK] Deleted existing test user.")

        # 2. Insert test user
        print("\nTesting: Create User...")
        user = SupabaseDB.create_user(test_email, test_password)
        if not user or not user.get("id"):
            raise ValueError("Create user response is missing user ID.")
        user_id = user["id"]
        print(f"[OK] User created successfully. ID: {user_id}")

        # 3. Retrieve user
        print("\nTesting: Get User by Email...")
        user_fetched = SupabaseDB.get_user_by_email(test_email)
        if not user_fetched or user_fetched["email"] != test_email:
            raise ValueError("Fetched user does not match email.")
        print(f"[OK] User retrieved successfully. Email: {user_fetched['email']}")

        # 4. Create test session
        print("\nTesting: Create Session...")
        session = SupabaseDB.create_session(user_id, "Test Diagnostic Session")
        if not session or not session.get("id"):
            raise ValueError("Create session response is missing session ID.")
        session_id = session["id"]
        print(f"[OK] Session created successfully. ID: {session_id}, Title: {session['title']}")

        # 5. Create test message
        print("\nTesting: Create Message...")
        test_sources = [{"page_number": 105, "text": "Medical encyclopedia excerpt about diagnostics"}]
        message = SupabaseDB.create_message(
            session_id=session_id,
            role="assistant",
            content="This is a test AI response with sources.",
            sources=test_sources
        )
        if not message or not message.get("id"):
            raise ValueError("Create message response is missing message ID.")
        print(f"[OK] Message created successfully. ID: {message['id']}")

        # 6. Retrieve messages
        print("\nTesting: Get Messages for Session...")
        messages = SupabaseDB.get_messages_by_session(session_id)
        if not messages or len(messages) == 0:
            raise ValueError("No messages retrieved for session.")
        print(f"[OK] Retrieved {len(messages)} message(s) successfully.")
        for msg in messages:
            print(f"  [{msg['role'].upper()}]: {msg['content']}")
            print(f"  Sources: {msg['sources']}")

        # 7. Delete session (confirm cascade)
        print("\nTesting: Delete Session (and verify cascade delete)...")
        deleted = SupabaseDB.delete_session(session_id)
        if not deleted:
            raise ValueError("Delete session returned False.")
        print("[OK] Session deleted successfully.")
        
        # Verify messages cascade
        remaining_messages = SupabaseDB.get_messages_by_session(session_id)
        if len(remaining_messages) > 0:
            raise ValueError("Messages were not cascade deleted with the session.")
        print("[OK] Message cascade deletion verified successfully.")

        # 8. Clean up user
        print("\nTesting: Delete User...")
        client.table("users").delete().eq("id", user_id).execute()
        print("[OK] User deleted successfully.")

        print("\n" + "=" * 60)
        print("[OK] ALL TESTS PASSED. Supabase connection and schema are fully verified!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_supabase_connection()

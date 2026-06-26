import sys
import os
import urllib.request
import json

# Adjust path to import app modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.auth.utils import create_token
from app.db.supabase import SupabaseDB

def test_chat_api():
    print("=" * 60)
    print("MEDBOT CHAT BLUEPRINT REST API VERIFICATION")
    print("=" * 60)
    
    # 1. Register or find test user
    test_email = "test_user_jwt@medbot.com"
    user = SupabaseDB.get_user_by_email(test_email)
    if not user:
        print("ERROR: Please run the authentication tests first to register the test user.")
        sys.exit(1)
    user_id = user["id"]
    print(f"Using Test User: {test_email} (ID: {user_id})")
    
    # 2. Generate a token
    token = create_token(user_id)
    print(f"Generated JWT: {token[:20]}...")
    
    # 3. Create a session using Python requests to the Flask local server
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create Session Request
    sess_url = "http://127.0.0.1:5000/api/sessions"
    sess_data = json.dumps({"title": "Diabetes Discussion"}).encode("utf-8")
    
    try:
        req = urllib.request.Request(sess_url, data=sess_data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode())
            session_id = res_data["id"]
            print(f"[OK] Session created successfully. ID: {session_id}, Title: {res_data['title']}")
    except Exception as e:
        print(f"[ERROR] Failed to create session via API: {str(e)}")
        sys.exit(1)
        
    # 4. Fetch Sessions list
    try:
        req = urllib.request.Request(sess_url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode())
            print(f"[OK] Sessions list fetched. Found {len(res_data)} session(s).")
            for s in res_data:
                print(f"  - Title: {s['title']}, Created At: {s['created_at']}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch sessions: {str(e)}")
        
    # 5. Fetch Message History (should have the user query and assistant response from the previous streaming run)
    print("\nFetching database messages directly to verify previous chat run...")
    try:
        # Get all sessions for this user
        sessions = SupabaseDB.get_sessions_by_user(user_id)
        found_messages = False
        for s in sessions:
            msgs = SupabaseDB.get_messages_by_session(s["id"])
            if msgs:
                print(f"[OK] Found session '{s['title']}' with {len(msgs)} messages:")
                for m in msgs:
                    print(f"  [{m['role'].upper()}]: {m['content']}")
                    if m['sources']:
                        print(f"    Sources: {m['sources']}")
                found_messages = True
                break
        if not found_messages:
            print("No messages found in any session yet.")
    except Exception as e:
        print(f"[ERROR] Failed to query messages: {str(e)}")
        
    # 6. Delete the test session
    del_url = f"http://127.0.0.1:5000/api/sessions/{session_id}"
    try:
        req = urllib.request.Request(del_url, headers=headers, method="DELETE")
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode())
            print(f"[OK] Delete Session API response: {res_data['message']}")
    except Exception as e:
        print(f"[ERROR] Failed to delete session: {str(e)}")

if __name__ == "__main__":
    test_chat_api()

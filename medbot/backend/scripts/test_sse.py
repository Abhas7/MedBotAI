import sys
import os
import urllib.request
import json

# Adjust path to import app modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.auth.utils import create_token
from app.db.supabase import SupabaseDB

def test_sse():
    print("=" * 60)
    print("MEDBOT CHAT SSE STREAMING VERIFICATION")
    print("=" * 60)
    
    # 1. Register or find test user
    test_email = "test_user_jwt@medbot.com"
    user = SupabaseDB.get_user_by_email(test_email)
    if not user:
        print("ERROR: Run auth tests first.")
        sys.exit(1)
    user_id = user["id"]
    
    token = create_token(user_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a session
    sess_url = "http://127.0.0.1:5000/api/sessions"
    sess_data = json.dumps({"title": "SSE In-Scope Test"}).encode("utf-8")
    
    req = urllib.request.Request(sess_url, data=sess_data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as res:
        session_id = json.loads(res.read().decode())["id"]
        print(f"Created Session: {session_id}")
        
    # Send chat query
    chat_url = "http://127.0.0.1:5000/api/chat"
    chat_data = json.dumps({
        "message": "What is diabetes?",
        "session_id": session_id
    }).encode("utf-8")
    
    print("Sending streaming chat query to /api/chat...")
    req = urllib.request.Request(chat_url, data=chat_data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as res:
            print("Response Status:", res.status)
            print("Response Headers:", dict(res.headers))
            
            # Read stream line by line
            print("STREAMING ANSWER: ", end="", flush=True)
            for line in res:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data:"):
                    data_json = json.loads(line_str[5:].strip())
                    if "token" in data_json:
                        print(data_json["token"], end="", flush=True)
                    elif "done" in data_json:
                        print("\n\n[DONE]")
                        print("Sources:", data_json["sources"])
                    elif "error" in data_json:
                        print(f"\n[ERROR]: {data_json['error']}")
    except Exception as e:
        print(f"\n[ERROR] Request failed: {str(e)}")
        
    # Verify database messages are saved
    print("\nVerifying database messages for this session...")
    msgs = SupabaseDB.get_messages_by_session(session_id)
    print(f"Found {len(msgs)} messages in database:")
    for m in msgs:
        print(f"  [{m['role'].upper()}]: {m['content']}")
        if m['sources']:
            print(f"    Sources count: {len(m['sources'])}")

if __name__ == "__main__":
    test_sse()

import logging
import httpx
from supabase import create_client, Client, ClientOptions
from app.config import Config

logger = logging.getLogger(__name__)

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Singleton initialization of the Supabase Client."""
    global _supabase_client
    if _supabase_client is None:
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_KEY
        if not url or not key or "placeholder" in url:
            logger.warning("SUPABASE_URL and SUPABASE_KEY must be configured with real values.")
            raise ValueError("Supabase is not configured properly.")
        logger.info("Initializing Supabase Client with custom httpx client (HTTP/2 disabled for Windows compatibility)...")
        httpx_client = httpx.Client(http2=False)
        options = ClientOptions(httpx_client=httpx_client)
        _supabase_client = create_client(url, key, options=options)
    return _supabase_client


class SupabaseDB:
    @staticmethod
    def create_user(email: str, password_hash: str) -> dict:
        """Create a new user in the users table."""
        try:
            client = get_supabase_client()
            response = client.table("users").insert({
                "email": email,
                "password_hash": password_hash
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error in create_user: {str(e)}")
            raise e

    @staticmethod
    def get_user_by_email(email: str) -> dict:
        """Retrieve user by their email address."""
        try:
            client = get_supabase_client()
            response = client.table("users").select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error in get_user_by_email: {str(e)}")
            raise e

    @staticmethod
    def get_user_by_id(user_id: str) -> dict:
        """Retrieve user by their UUID."""
        try:
            client = get_supabase_client()
            response = client.table("users").select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {str(e)}")
            raise e

    @staticmethod
    def create_session(user_id: str, title: str) -> dict:
        """Create a new chat session for a user."""
        try:
            client = get_supabase_client()
            response = client.table("sessions").insert({
                "user_id": user_id,
                "title": title
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error in create_session: {str(e)}")
            raise e

    @staticmethod
    def get_sessions_by_user(user_id: str) -> list:
        """Get all sessions for a user ordered by creation date desc."""
        try:
            client = get_supabase_client()
            response = client.table("sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error in get_sessions_by_user: {str(e)}")
            raise e

    @staticmethod
    def get_session_by_id(session_id: str) -> dict:
        """Retrieve a specific session by its ID."""
        try:
            client = get_supabase_client()
            response = client.table("sessions").select("*").eq("id", session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error in get_session_by_id: {str(e)}")
            raise e

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a chat session (cascades to messages)."""
        try:
            client = get_supabase_client()
            response = client.table("sessions").delete().eq("id", session_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error in delete_session: {str(e)}")
            raise e

    @staticmethod
    def create_message(session_id: str, role: str, content: str, sources: list = None) -> dict:
        """Save a new chat message to a session."""
        try:
            client = get_supabase_client()
            response = client.table("messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content,
                "sources": sources or []
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error in create_message: {str(e)}")
            raise e

    @staticmethod
    def get_messages_by_session(session_id: str) -> list:
        """Get message history for a session ordered chronologically."""
        try:
            client = get_supabase_client()
            response = client.table("messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error in get_messages_by_session: {str(e)}")
            raise e

import json
import logging
from flask import request, jsonify, Response
from app.chat import chat_bp
from app.auth.utils import token_required
from app.db.supabase import SupabaseDB
from app.chat.rag import MedicalRAGPipeline

logger = logging.getLogger(__name__)

_rag_pipeline = None

def get_rag_pipeline():
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = MedicalRAGPipeline()
    return _rag_pipeline

@chat_bp.route("/sessions", methods=["POST"])
@token_required
def create_session(current_user_id):
    """Create a new chat session for the current user."""
    data = request.get_json() or {}
    title = data.get("title", "New Chat").strip()
    
    if not title:
        title = "New Chat"
        
    try:
        session = SupabaseDB.create_session(current_user_id, title)
        if not session:
            return jsonify({"message": "Failed to create session."}), 500
            
        return jsonify(session), 201
    except Exception as e:
        logger.error(f"Error in create_session endpoint: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


@chat_bp.route("/sessions", methods=["GET"])
@token_required
def list_sessions(current_user_id):
    """List all sessions belonging to the current user."""
    try:
        sessions = SupabaseDB.get_sessions_by_user(current_user_id)
        return jsonify(sessions), 200
    except Exception as e:
        logger.error(f"Error in list_sessions endpoint: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


@chat_bp.route("/sessions/<session_id>/messages", methods=["GET"])
@token_required
def get_session_messages(current_user_id, session_id):
    """Get the message history of a specific session (ownership verified)."""
    try:
        # Verify ownership
        session = SupabaseDB.get_session_by_id(session_id)
        if not session or session["user_id"] != current_user_id:
            return jsonify({"message": "Session not found or access denied."}), 403
            
        messages = SupabaseDB.get_messages_by_session(session_id)
        return jsonify(messages), 200
    except Exception as e:
        logger.error(f"Error in get_session_messages endpoint: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


@chat_bp.route("/sessions/<session_id>", methods=["DELETE"])
@token_required
def delete_session(current_user_id, session_id):
    """Delete a chat session (ownership verified)."""
    try:
        # Verify ownership
        session = SupabaseDB.get_session_by_id(session_id)
        if not session:
            # Idempotent delete: if the session is already gone, return success
            return jsonify({"message": "Session deleted successfully."}), 200
            
        if session["user_id"] != current_user_id:
            return jsonify({"message": "Session not found or access denied."}), 403
            
        deleted = SupabaseDB.delete_session(session_id)
        if not deleted:
            return jsonify({"message": "Failed to delete session."}), 500
            
        return jsonify({"message": "Session deleted successfully."}), 200
    except Exception as e:
        logger.error(f"Error in delete_session endpoint: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


@chat_bp.route("/chat", methods=["POST"])
@token_required
def chat(current_user_id):
    """Secure SSE Chat streaming endpoint."""
    data = request.get_json() or {}
    query = data.get("message", "").strip()
    session_id = data.get("session_id")
    
    if not query or not session_id:
        return jsonify({"message": "message and session_id are required fields."}), 400
        
    try:
        # Verify ownership of session
        session = SupabaseDB.get_session_by_id(session_id)
        if not session or session["user_id"] != current_user_id:
            return jsonify({"message": "Session not found or access denied."}), 403
            
        # 1. Save user message to Supabase
        SupabaseDB.create_message(session_id, role="user", content=query, sources=[])
        
        # 2. Create Server-Sent Events (SSE) generator
        def sse_generator():
            full_answer = ""
            try:
                # Yield an initial empty token to avoid proxy timeouts while waiting for first token
                yield f"data: {json.dumps({'status': 'connected'})}\n\n"
                
                # Initialize pipeline and generate response AFTER sending headers and initial connection packet
                pipeline = get_rag_pipeline()
                stream, sources = pipeline.generate_response(query, stream=True)
                
                for token in stream:
                    full_answer += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
                    
                # Save assistant's final response and sources to Supabase
                SupabaseDB.create_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_answer,
                    sources=sources
                )
                
                # Yield a final packet with the full sources to render in UI
                yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
            except Exception as ex:
                logger.error(f"Error inside SSE generator loop: {str(ex)}")
                yield f"data: {json.dumps({'error': str(ex)})}\n\n"
                
        return Response(sse_generator(), mimetype="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint setup: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500

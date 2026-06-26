from flask import Blueprint

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

# Import routes to register them with the blueprint
from app.chat import routes

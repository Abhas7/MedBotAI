import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config

def setup_logging(app):
    """Set up colored console logging and plain rotating file logging."""
    # Ensure backend/logs directory exists
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(backend_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "app.log")
    
    # Base formatter for rotating file log (no color codes)
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d]: %(message)s"
    )
    
    # Rotating file handler (10MB, max 5 backup files)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # Colored console logging
    try:
        import colorlog
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    except ImportError:
        console_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure app logger
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

def create_app(config_class=Config):
    """Flask Application Factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Setup Loggers
    setup_logging(app)
    app.logger.info("Starting MedBot application initialization...")
    
    # Validate critical environment variables
    missing_configs = config_class.validate()
    if missing_configs:
        app.logger.warning(
            f"Missing required environment variables: {', '.join(missing_configs)}. "
            "Please check your .env configuration."
        )
    else:
        app.logger.info("All required environment configurations validated successfully.")
        
    # Register blueprints (placeholder registration in Step 1)
    from app.auth import auth_bp
    from app.chat import chat_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    
    # Global health/ping check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        app.logger.info("Health check endpoint triggered.")
        return jsonify({
            "status": "healthy",
            "message": "MedBot Flask Backend API is running.",
            "missing_env_vars": missing_configs
        }), 200
        
    return app

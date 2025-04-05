import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db
from routes.projects import projects_bp
from routes.files import files_bp
# Removed: from routes.legacy import legacy_bp
import logging

def create_app(config_class=Config):
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app) # Enable CORS for all routes
    db.init_app(app)

    # Configure logging
    logging.basicConfig(level=logging.INFO) # Log INFO level and above
    # You might want to add file logging for production
    # handler = logging.FileHandler('app.log')
    # handler.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # handler.setFormatter(formatter)
    # app.logger.addHandler(handler)

    # Create database tables if they don't exist
    # Use app context for database operations
    with app.app_context():
        # Check if tables already exist before creating
        # This is safer than calling create_all() unconditionally
        # inspector = db.inspect(db.engine)
        # if not inspector.has_table("project") or not inspector.has_table("file") or not inspector.has_table("legacy_file"):
        #     app.logger.info("Creating database tables...")
        #     db.create_all()
        # else:
        #     app.logger.info("Database tables already exist.")
        # Simpler approach for SQLite during development:
        db.create_all()


    # Register blueprints
    app.register_blueprint(projects_bp)
    app.register_blueprint(files_bp)
    # Removed: app.register_blueprint(legacy_bp)

    # Simple root route for health check or basic info
    @app.route('/')
    def index():
        return jsonify({"message": "Translation Tool API is running."})

    # Error Handling (optional but recommended)
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Log the error details
        app.logger.error(f'Internal Server Error: {str(error)}', exc_info=True)
        # Rollback the session in case of DB errors during the request
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        # Often raised by request parsing issues or explicit checks
        return jsonify({"error": "Bad Request", "message": str(error.description if hasattr(error, 'description') else error)}), 400


    app.logger.info("Flask application created successfully.")
    return app

# Create the app instance using the factory function
app = create_app()

# Run the development server
if __name__ == '__main__':
    # Use environment variables for host/port if available, otherwise default
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 3000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    app.run(host=host, port=port, debug=debug)

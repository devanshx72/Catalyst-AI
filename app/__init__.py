from flask import Flask, render_template
import os
from datetime import timedelta

def create_app(test_config=None):
    """Create and configure the Flask application"""
    # Explicitly set the template folder path
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    
    app = Flask(__name__, instance_relative_config=True, template_folder=template_dir, static_folder=static_dir)
    
    # Generate a stable secret key if not provided
    # This ensures sessions persist across server restarts
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        # Use a hash of the app path as fallback for development
        # In production, always set SECRET_KEY in environment
        import hashlib
        secret_key = hashlib.sha256(os.path.dirname(__file__).encode()).hexdigest()
    
    # Set up configuration
    app.config.from_mapping(
        SECRET_KEY=secret_key,
        MONGO_URI=os.getenv('MONGO_URI'),
        DB_NAME=os.getenv('DB_NAME', 'catalyst_ai_db'),
        # Session configuration
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    if test_config:
        app.config.from_mapping(test_config)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.roadmap import roadmap_bp
    from app.routes.career_coach import career_coach_bp
    from app.routes.tutor import tutor_bp  # Import the new tutor blueprint
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(career_coach_bp)
    app.register_blueprint(tutor_bp)  # Register the new tutor blueprint
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    return app
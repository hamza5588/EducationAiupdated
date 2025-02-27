# app/__init__.py
from flask import Flask
from datetime import timedelta
import os
from app.utils.db import init_db

def create_app():
    # Create Flask app with template folder in project root
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Basic configuration
    app.secret_key = 'your_secret_key'  # Change this in production
    app.permanent_session_lifetime = timedelta(days=30)
    
    # Ensure template folder exists
    if not os.path.exists(app.template_folder):
        os.makedirs(app.template_folder)
        print(f"Created template folder at: {app.template_folder}")
    else:
        print(f"Template folder exists at: {app.template_folder}")
    
    # Initialize database
    with app.app_context():
        init_db(app)
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.chat import bp as chat_bp
    from app.routes.files import bp as files_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(files_bp)
    
    # Create upload folder if it doesn't exist
    upload_folder = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Debug print to show template folder location
    print(f"Flask app template folder: {app.template_folder}")
    print(f"Flask app static folder: {app.static_folder}")
    
    return app
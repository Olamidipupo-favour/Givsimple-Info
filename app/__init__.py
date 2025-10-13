from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import redis
import os
from dotenv import load_dotenv
from werkzeug.routing import BaseConverter

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

# Add a regex converter for routes (e.g., to match only specific token formats)
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super().__init__(url_map)
        self.regex = items[0]

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Register custom converters
    app.url_map.converters['regex'] = RegexConverter

    # Configuration
    if config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    elif config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Initialize email
    from app.email import init_mail
    init_mail(app)
    
    # Add custom Jinja2 filters
    import json
    @app.template_filter('from_json')
    def from_json_filter(json_string):
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return None
    
    # Initialize rate limiter
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'])
        # Test Redis connection
        redis_client.ping()
        # Configure limiter with Redis
        app.config['RATELIMIT_STORAGE_URL'] = app.config['REDIS_URL']
        limiter.init_app(app)
    except Exception as e:
        app.logger.warning(f"Redis not available, using in-memory rate limiter: {e}")
        # Use in-memory storage
        app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
        limiter.init_app(app)
    
    # Register blueprints
    from app.views.public import public_bp
    from app.views.api import api_bp
    from app.views.admin import admin_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create tables and initialize admin user
    with app.app_context():
        db.create_all()
        
        # Create default admin user if none exists
        from app.auth import create_default_admin
        try:
            create_default_admin()
        except Exception as e:
            app.logger.error(f"Failed to create default admin: {e}")
    
    return app

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import redis
import os

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

def create_app(config_name=None):
    app = Flask(__name__)
    
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
    
    # Initialize rate limiter
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'])
        limiter.init_app(app, storage_uri=app.config['REDIS_URL'])
    except Exception as e:
        app.logger.warning(f"Redis not available, using in-memory rate limiter: {e}")
        limiter.init_app(app)
    
    # Register blueprints
    from app.views.public import public_bp
    from app.views.api import api_bp
    from app.views.admin import admin_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

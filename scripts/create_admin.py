#!/usr/bin/env python3
"""
Create Admin User Script

Usage: python scripts/create_admin.py
"""

import sys
import os
from pathlib import Path

# Set environment variables before importing app
os.environ['FLASK_ENV'] = 'development'

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import AdminUser

def create_admin_user():
    """Create admin user"""
    app = create_app('development')
    
    with app.app_context():
        # Get admin credentials from app config
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@givsimple.com')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
        # Check if admin already exists
        existing_admin = AdminUser.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            print(f"Admin user already exists: {admin_email}")
            return
        
        # Create new admin user
        admin = AdminUser(
            email=admin_email,
            is_active=True
        )
        admin.set_password(admin_password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print(f"Login at: /admin/login")

def main():
    try:
        create_admin_user()
    except Exception as e:
        print(f"Error creating admin user: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

import pytest
from flask import Flask
from app import create_app, db
from app.models import Tag, TagStatus, User, Activation
from app.views.public import public_bp

@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    # Do not re-register blueprints; create_app already handles registration
    with app.app_context():
        db.session.expire_on_commit = False
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def sample_tag(app):
    """Create a sample tag for testing"""
    with app.app_context():
        tag = Tag(token="TEST123", status=TagStatus.UNASSIGNED)
        db.session.add(tag)
        db.session.commit()
        return tag.token

@pytest.fixture
def active_tag(app):
    """Create an active tag for testing"""
    with app.app_context():
        tag = Tag(
            token="ACTIVE1", 
            status=TagStatus.ACTIVE, 
            target_url="https://cash.app/$testuser"
        )
        db.session.add(tag)
        db.session.commit()
        return tag.token, tag.target_url

@pytest.fixture
def blocked_tag(app):
    """Create a blocked tag for testing"""
    with app.app_context():
        tag = Tag(token="BLOCKED1", status=TagStatus.BLOCKED)
        db.session.add(tag)
        db.session.commit()
        return tag.token

class TestTokenRedirect:
    def test_redirect_active_tag(self, client, active_tag):
        """Active tags redirect immediately with 301"""
        token, target_url = active_tag
        response = client.get(f'/t/{token}')
        assert response.status_code == 301
        assert response.location == target_url
    
    def test_redirect_unassigned_tag(self, client, sample_tag):
        """Unassigned tags redirect to activation page"""
        response = client.get(f'/t/{sample_tag}')
        assert response.status_code == 302
        assert '/activate?token=' in response.location
    
    def test_redirect_blocked_tag(self, client, blocked_tag):
        """Blocked tags return 404 to hide existence"""
        response = client.get(f'/t/{blocked_tag}')
        assert response.status_code == 404
    
    def test_redirect_invalid_token_format(self, client):
        """Invalid token characters redirect to activation (length-only validation)"""
        response = client.get('/t/INVALID!')
        assert response.status_code == 302
        assert '/activate?token=INVALID!' in response.location
    
    def test_redirect_token_too_short(self, client):
        response = client.get('/t/SHORT')
        assert response.status_code == 404
    
    def test_redirect_token_too_long(self, client):
        response = client.get('/t/VERYLONGTOKEN123456')
        assert response.status_code == 404

class TestActivationPage:
    def test_activate_page_with_token(self, client, sample_tag):
        response = client.get(f'/activate?token={sample_tag}')
        assert response.status_code == 200
        assert sample_tag.encode() in response.data
    
    def test_activate_page_already_active(self, client, active_tag):
        active_token, _ = active_tag
        response = client.get(f'/activate?token={active_token}')
        assert response.status_code == 200
        assert b'already activated' in response.data
    
    def test_activate_page_blocked_token(self, client, blocked_tag):
        response = client.get(f'/activate?token={blocked_tag}')
        assert response.status_code == 200
        assert b'blocked' in response.data

class TestIndexPage:
    def test_index_page(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'GivSimple' in response.data
        assert b'NFC Cards, Simplified' in response.data

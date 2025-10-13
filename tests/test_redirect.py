import pytest
from flask import Flask
from app import create_app, db
from app.models import Tag, TagStatus, User, Activation, PaymentProvider
from app.views.public import public_bp

@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    app.register_blueprint(public_bp)
    
    with app.app_context():
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
        return tag

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
        return tag

@pytest.fixture
def blocked_tag(app):
    """Create a blocked tag for testing"""
    with app.app_context():
        tag = Tag(token="BLOCKED1", status=TagStatus.BLOCKED)
        db.session.add(tag)
        db.session.commit()
        return tag

class TestTokenRedirect:
    def test_redirect_active_tag(self, client, active_tag):
        """Test redirect to active tag"""
        response = client.get(f'/t/{active_tag.token}')
        assert response.status_code == 301
        assert response.location == active_tag.target_url
    
    def test_redirect_unassigned_tag(self, client, sample_tag):
        """Test redirect to activation page for unassigned tag"""
        response = client.get(f'/t/{sample_tag.token}')
        assert response.status_code == 302
        assert '/activate?token=' in response.location
    
    def test_redirect_nonexistent_tag(self, client):
        """Test redirect to activation for nonexistent tag"""
        response = client.get('/t/NONEXIST')
        assert response.status_code == 302
        assert '/activate?token=NONEXIST' in response.location
    
    def test_redirect_blocked_tag(self, client, blocked_tag):
        """Test 404 for blocked tag (should hide existence)"""
        response = client.get(f'/t/{blocked_tag.token}')
        assert response.status_code == 404
    
    def test_redirect_invalid_token_format(self, client):
        """Test 404 for invalid token format"""
        response = client.get('/t/INVALID!')
        assert response.status_code == 404
    
    def test_redirect_token_too_short(self, client):
        """Test 404 for token that's too short"""
        response = client.get('/t/SHORT')
        assert response.status_code == 404
    
    def test_redirect_token_too_long(self, client):
        """Test 404 for token that's too long"""
        response = client.get('/t/VERYLONGTOKEN123456')
        assert response.status_code == 404

class TestActivationPage:
    def test_activate_page_with_token(self, client, sample_tag):
        """Test activation page with valid token"""
        response = client.get(f'/activate?token={sample_tag.token}')
        assert response.status_code == 200
        assert sample_tag.token.encode() in response.data
    
    def test_activate_page_without_token(self, client):
        """Test activation page without token"""
        response = client.get('/activate')
        assert response.status_code == 200
        assert b'No token provided' in response.data
    
    def test_activate_page_invalid_token(self, client):
        """Test activation page with invalid token"""
        response = client.get('/activate?token=INVALID!')
        assert response.status_code == 200
        assert b'Invalid token format' in response.data
    
    def test_activate_page_nonexistent_token(self, client):
        """Test activation page with nonexistent token"""
        response = client.get('/activate?token=NONEXIST')
        assert response.status_code == 200
        assert b'Token not found' in response.data
    
    def test_activate_page_already_active(self, client, active_tag):
        """Test activation page for already active tag"""
        response = client.get(f'/activate?token={active_tag.token}')
        assert response.status_code == 200
        assert b'already activated' in response.data
    
    def test_activate_page_blocked_token(self, client, blocked_tag):
        """Test activation page for blocked token"""
        response = client.get(f'/activate?token={blocked_tag.token}')
        assert response.status_code == 200
        assert b'blocked' in response.data

class TestZelleInstructions:
    def test_zelle_instructions_with_email(self, client):
        """Test Zelle instructions page with email"""
        response = client.get('/pay-by-zelle?email=test@example.com')
        assert response.status_code == 200
        assert b'test@example.com' in response.data
    
    def test_zelle_instructions_with_phone(self, client):
        """Test Zelle instructions page with phone"""
        response = client.get('/pay-by-zelle?phone=+1234567890')
        assert response.status_code == 200
        assert b'+1234567890' in response.data
    
    def test_zelle_instructions_with_both(self, client):
        """Test Zelle instructions page with both email and phone"""
        response = client.get('/pay-by-zelle?email=test@example.com&phone=+1234567890')
        assert response.status_code == 200
        assert b'test@example.com' in response.data
        assert b'+1234567890' in response.data
    
    def test_zelle_instructions_without_contact(self, client):
        """Test Zelle instructions page without contact info"""
        response = client.get('/pay-by-zelle')
        assert response.status_code == 200
        assert b'Email or phone number required' in response.data

class TestIndexPage:
    def test_index_page(self, client):
        """Test index page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'GivSimple' in response.data
        assert b'Dynamic NFC Redirect Service' in response.data

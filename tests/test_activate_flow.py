import pytest
import json
from flask import Flask
from app import create_app, db
from app.models import Tag, TagStatus, User, Activation, PaymentProvider
from app.views.api import api_bp

@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    app.register_blueprint(api_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def unassigned_tag(app):
    """Create an unassigned tag for testing"""
    with app.app_context():
        tag = Tag(token="TEST123", status=TagStatus.UNASSIGNED)
        db.session.add(tag)
        db.session.commit()
        return tag

@pytest.fixture
def active_tag(app):
    """Create an active tag for testing"""
    with app.app_context():
        tag = Tag(token="ACTIVE1", status=TagStatus.ACTIVE, target_url="https://cash.app/$test")
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

class TestActivationAPI:
    def test_activate_success(self, client, unassigned_tag):
        """Test successful activation"""
        data = {
            'token': unassigned_tag.token,
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'payment_handle': '$testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'redirect_url' in result
        
        # Check database state
        with client.application.app_context():
            tag = Tag.query.get(unassigned_tag.id)
            assert tag.status == TagStatus.ACTIVE
            assert tag.target_url is not None
            assert tag.buyer_user_id is not None
            
            user = User.query.filter_by(email='test@example.com').first()
            assert user is not None
            assert user.name == 'Test User'
            assert user.phone == '+1234567890'
            
            activation = Activation.query.filter_by(tag_id=tag.id).first()
            assert activation is not None
            assert activation.payment_provider == PaymentProvider.CASHAPP
    
    def test_activate_nonexistent_token(self, client):
        """Test activation with nonexistent token"""
        data = {
            'token': 'NONEXIST',
            'name': 'Test User',
            'email': 'test@example.com',
            'payment_handle': '$testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 404
        
        result = json.loads(response.data)
        assert 'error' in result
        assert 'not found' in result['error'].lower()
    
    def test_activate_already_active(self, client, active_tag):
        """Test activation of already active tag"""
        data = {
            'token': active_tag.token,
            'name': 'Test User',
            'email': 'test@example.com',
            'payment_handle': '$testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result
        assert 'already activated' in result['error'].lower()
    
    def test_activate_blocked_token(self, client, blocked_tag):
        """Test activation of blocked token"""
        data = {
            'token': blocked_tag.token,
            'name': 'Test User',
            'email': 'test@example.com',
            'payment_handle': '$testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result
        assert 'blocked' in result['error'].lower()
    
    def test_activate_missing_fields(self, client, unassigned_tag):
        """Test activation with missing required fields"""
        data = {
            'token': unassigned_tag.token,
            'name': 'Test User',
            # Missing email and payment_handle
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result
        assert 'required fields' in result['error'].lower()
    
    def test_activate_invalid_email(self, client, unassigned_tag):
        """Test activation with invalid email"""
        data = {
            'token': unassigned_tag.token,
            'name': 'Test User',
            'email': 'invalid-email',
            'payment_handle': '$testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result
        assert 'email' in result['error'].lower()
    
    def test_activate_invalid_token_format(self, client):
        """Test activation with invalid token format"""
        data = {
            'token': 'INVALID!',
            'name': 'Test User',
            'email': 'test@example.com',
            'payment_handle': '$testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result
        assert 'token format' in result['error'].lower()
    
    def test_activate_invalid_payment_handle(self, client, unassigned_tag):
        """Test activation with invalid payment handle"""
        data = {
            'token': unassigned_tag.token,
            'name': 'Test User',
            'email': 'test@example.com',
            'payment_handle': 'invalid@domain.com'  # Not a valid payment handle
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result
        assert 'payment handle' in result['error'].lower()
    
    def test_activate_paypal_handle(self, client, unassigned_tag):
        """Test activation with PayPal handle"""
        data = {
            'token': unassigned_tag.token,
            'name': 'Test User',
            'email': 'test@example.com',
            'payment_handle': 'paypal.me/testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'paypal.me' in result['redirect_url']
    
    def test_activate_venmo_handle(self, client, unassigned_tag):
        """Test activation with Venmo handle"""
        data = {
            'token': unassigned_tag.token,
            'name': 'Test User',
            'email': 'test@example.com',
            'payment_handle': '@testuser'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'venmo.com' in result['redirect_url']
    
    def test_activate_zelle_handle(self, client, unassigned_tag):
        """Test activation with Zelle handle"""
        data = {
            'token': unassigned_tag.token,
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'payment_handle': 'zelle'
        }
        
        response = client.post('/api/activate', data=data)
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['success'] == True
        assert 'givsimple.com/pay-by-zelle' in result['redirect_url']
    
    def test_activate_existing_user(self, client, unassigned_tag):
        """Test activation with existing user"""
        with client.application.app_context():
            # Create existing user
            user = User(name='Existing User', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            
            data = {
                'token': unassigned_tag.token,
                'name': 'Test User',
                'email': 'test@example.com',
                'payment_handle': '$testuser'
            }
            
            response = client.post('/api/activate', data=data)
            assert response.status_code == 200
            
            # Check that existing user was used
            tag = Tag.query.get(unassigned_tag.id)
            assert tag.buyer_user_id == user.id
    
    def test_activate_duplicate_activation(self, client, unassigned_tag):
        """Test activation attempt by same user for same tag"""
        with client.application.app_context():
            # Create user and activation
            user = User(name='Test User', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            
            tag = Tag.query.get(unassigned_tag.id)
            tag.status = TagStatus.ACTIVE
            tag.buyer_user_id = user.id
            tag.target_url = 'https://cash.app/$test'
            db.session.commit()
            
            activation = Activation(
                tag_id=tag.id,
                user_id=user.id,
                payment_provider=PaymentProvider.CASHAPP,
                payment_handle_or_url='$test',
                resolved_target_url='https://cash.app/$test'
            )
            db.session.add(activation)
            db.session.commit()
            
            data = {
                'token': unassigned_tag.token,
                'name': 'Test User',
                'email': 'test@example.com',
                'payment_handle': '$testuser'
            }
            
            response = client.post('/api/activate', data=data)
            assert response.status_code == 400
            
            result = json.loads(response.data)
            assert 'error' in result
            assert 'already been activated' in result['error'].lower()

class TestHealthEndpoint:
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        result = json.loads(response.data)
        assert result['status'] == 'healthy'
        assert result['service'] == 'givsimple-api'

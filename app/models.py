from datetime import datetime
from enum import Enum
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import json

class TagStatus(Enum):
    UNASSIGNED = "unassigned"
    REGISTERED = "registered"
    ACTIVE = "active"
    BLOCKED = "blocked"

class PaymentProvider(Enum):
    CASHAPP = "cashapp"
    PAYPAL = "paypal"
    VENMO = "venmo"
    ZELLE = "zelle"
    GENERIC = "generic"

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(16), unique=True, nullable=False, index=True)
    status = db.Column(db.Enum(TagStatus), default=TagStatus.UNASSIGNED, nullable=False)
    target_url = db.Column(db.String(500), nullable=True)
    buyer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    buyer = db.relationship('User', backref='tags', lazy=True)
    activations = db.relationship('Activation', backref='tag', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='tag', lazy=True)
    
    def __repr__(self):
        return f'<Tag {self.token}: {self.status.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'status': self.status.value,
            'target_url': self.target_url,
            'buyer_user_id': self.buyer_user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    activations = db.relationship('Activation', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat()
        }

class Activation(db.Model):
    __tablename__ = 'activations'
    
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_provider = db.Column(db.Enum(PaymentProvider), nullable=False)
    payment_handle_or_url = db.Column(db.String(500), nullable=False)
    resolved_target_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Activation {self.id}: {self.payment_provider.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tag_id': self.tag_id,
            'user_id': self.user_id,
            'payment_provider': self.payment_provider.value,
            'payment_handle_or_url': self.payment_handle_or_url,
            'resolved_target_url': self.resolved_target_url,
            'created_at': self.created_at.isoformat()
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(100), nullable=False)  # 'system', 'admin', or admin email
    action = db.Column(db.String(100), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=True)
    meta = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.actor}>'
    
    def to_dict(self):
        meta_dict = None
        if self.meta:
            try:
                meta_dict = json.loads(self.meta)
            except json.JSONDecodeError:
                meta_dict = {'raw': self.meta}
        
        return {
            'id': self.id,
            'actor': self.actor,
            'action': self.action,
            'tag_id': self.tag_id,
            'meta': meta_dict,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def log(cls, actor, action, tag_id=None, meta=None):
        """Helper method to create audit log entries"""
        meta_json = None
        if meta:
            meta_json = json.dumps(meta)
        
        log_entry = cls(
            actor=actor,
            action=action,
            tag_id=tag_id,
            meta=meta_json
        )
        db.session.add(log_entry)
        return log_entry

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<AdminUser {self.email}>'

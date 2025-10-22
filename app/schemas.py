from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, URL, ValidationError
from app.models import TagStatus, PaymentProvider
import re

class ActivationForm(FlaskForm):
    token = StringField('Token', validators=[DataRequired(), Length(min=8, max=16)])
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    payment_handle = StringField('Payment Handle/URL', validators=[DataRequired(), Length(max=500)])
    
    # Zelle-specific fields (optional, only used when payment method is Zelle)
    zelle_account_name = StringField('Zelle Account Name', validators=[Optional(), Length(max=100)])
    zelle_account_identifier = StringField('Zelle Account (Email/Phone)', validators=[Optional(), Length(max=120)])
    
    def validate_token(self, field):
        # Check if token contains only alphanumeric characters
        if not re.match(r'^[a-zA-Z0-9]+$', field.data):
            raise ValidationError('Token must contain only letters and numbers')
    
    def validate_payment_handle(self, field):
        # Basic validation - more detailed validation in utils/normalize.py
        if field.data and len(field.data.strip()) == 0:
            raise ValidationError('Payment handle cannot be empty')
    
    def validate_zelle_account_name(self, field):
        # If payment handle indicates Zelle, account name is required
        if (self.payment_handle.data and 
            'zelle' in self.payment_handle.data.lower() and 
            (not field.data or len(field.data.strip()) == 0)):
            raise ValidationError('Zelle account name is required when using Zelle')
    
    def validate_zelle_account_identifier(self, field):
        # If payment handle indicates Zelle, account identifier is required
        if (self.payment_handle.data and 
            'zelle' in self.payment_handle.data.lower() and 
            (not field.data or len(field.data.strip()) == 0)):
            raise ValidationError('Zelle account identifier (email or phone) is required when using Zelle')
        
        # Basic validation for email or phone format if provided
        if field.data and field.data.strip():
            data = field.data.strip()
            # Check if it's an email
            if '@' in data:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data):
                    raise ValidationError('Invalid email format for Zelle account identifier')
            # Check if it's a phone number
            else:
                phone_clean = data.replace('-', '').replace(' ', '').replace('(', '').replace(')', '').replace('+', '')
                if not re.match(r'^1?[2-9]\d{2}[2-9]\d{2}\d{4}$', phone_clean):
                    raise ValidationError('Invalid phone format for Zelle account identifier')

class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])

class TagEditForm(FlaskForm):
    token = StringField('Token', validators=[DataRequired(), Length(min=8, max=16)])
    status = SelectField('Status', choices=[
        (TagStatus.UNASSIGNED.value, 'Unassigned'),
        (TagStatus.REGISTERED.value, 'Registered'),
        (TagStatus.ACTIVE.value, 'Active'),
        (TagStatus.BLOCKED.value, 'Blocked')
    ], validators=[DataRequired()])
    target_url = StringField('Target URL', validators=[Optional(), URL(), Length(max=500)])
    
    def validate_token(self, field):
        if not re.match(r'^[a-zA-Z0-9]+$', field.data):
            raise ValidationError('Token must contain only letters and numbers')

class CSVImportForm(FlaskForm):
    csv_data = TextAreaField('CSV Data', validators=[DataRequired()], 
                            render_kw={'rows': 10, 'placeholder': 'token,url\nABC123,https://example.com\nDEF456,https://test.com'})
    submit = SubmitField('Import CSV')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        (TagStatus.UNASSIGNED.value, 'Unassigned'),
        (TagStatus.REGISTERED.value, 'Registered'),
        (TagStatus.ACTIVE.value, 'Active'),
        (TagStatus.BLOCKED.value, 'Blocked')
    ], validators=[Optional()])

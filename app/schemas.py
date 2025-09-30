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
    
    def validate_token(self, field):
        # Check if token contains only alphanumeric characters
        if not re.match(r'^[a-zA-Z0-9]+$', field.data):
            raise ValidationError('Token must contain only letters and numbers')
    
    def validate_payment_handle(self, field):
        # Basic validation - more detailed validation in utils/normalize.py
        if field.data and len(field.data.strip()) == 0:
            raise ValidationError('Payment handle cannot be empty')

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

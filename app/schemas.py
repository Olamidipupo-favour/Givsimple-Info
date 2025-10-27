from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, URL, ValidationError
from app.models import TagStatus
import re

class ActivationForm(FlaskForm):
    token = StringField('Token', validators=[DataRequired(), Length(min=8, max=16)])
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    payment_handle = StringField('Card Link URL (Optional)', validators=[Optional(), URL(), Length(max=500)])
    
    def validate_token(self, field):
        # Check if token contains only alphanumeric characters
        if not re.match(r'^[a-zA-Z0-9]+$', field.data):
            raise ValidationError('Token must contain only letters and numbers')
    
    def validate_payment_handle(self, field):
        # If provided, require full HTTPS URL
        data = (field.data or '').strip()
        if data and not data.lower().startswith('https://'):
            raise ValidationError('Card Link URL must start with https://')

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

class UserRegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=1, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = StringField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = StringField('Confirm Password', validators=[DataRequired()])
    
    def validate_username(self, field):
        # usernames: letters, numbers, underscores, hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', field.data or ''):
            raise ValidationError('Username can include letters, numbers, - and _.')
    
    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Passwords do not match.')

class UserLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])

class ProfileForm(FlaskForm):
    display_name = StringField('Display Name', validators=[Optional(), Length(max=100)])
    headline = StringField('Headline', validators=[Optional(), Length(max=140)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=2000)])
    avatar_url = StringField('Avatar URL', validators=[Optional(), URL(), Length(max=500)])
    theme = SelectField('Theme', choices=[('light', 'Light'), ('dark', 'Dark')], validators=[Optional()])
    links_json = TextAreaField('Links (JSON)', validators=[Optional(), Length(max=4000)],
                               render_kw={'rows': 6, 'placeholder': '[{"label":"Website","url":"https://example.com"}]'})
    
    def validate_links_json(self, field):
        data = (field.data or '').strip()
        if not data:
            return
        try:
            import json
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                raise ValidationError('Links must be a JSON array.')
            # Basic validation for objects
            for item in parsed:
                if not isinstance(item, dict) or 'label' not in item or 'url' not in item:
                    raise ValidationError('Each link must be an object with label and url.')
        except Exception:
            raise ValidationError('Invalid JSON format for links.')

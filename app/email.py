from flask import current_app, render_template
from flask_mail import Mail, Message
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Initialize Flask-Mail
mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app"""
    mail.init_app(app)

def send_activation_email(user_email, user_name, token, payment_url):
    """Send activation confirmation email"""
    try:
        # Create message
        msg = Message(
            subject='Your GivSimple Device is Ready!',
            recipients=[user_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render email template
        msg.html = render_template('emails/activation.html', 
                                 user_name=user_name,
                                 token=token,
                                 payment_url=payment_url)
        
        msg.body = render_template('emails/activation.txt',
                                 user_name=user_name,
                                 token=token,
                                 payment_url=payment_url)
        
        # Send email
        mail.send(msg)
        current_app.logger.info(f"Activation email sent to {user_email}")
        
    except Exception as e:
        current_app.logger.error(f"Failed to send activation email to {user_email}: {e}")
        raise

def send_admin_notification(admin_email, subject, message):
    """Send notification to admin"""
    try:
        msg = Message(
            subject=f'[GivSimple] {subject}',
            recipients=[admin_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.body = message
        mail.send(msg)
        current_app.logger.info(f"Admin notification sent to {admin_email}")
        
    except Exception as e:
        current_app.logger.error(f"Failed to send admin notification: {e}")

def send_simple_email(to_email, subject, body):
    """Send simple email without templates"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.body = body
        mail.send(msg)
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {e}")
        raise

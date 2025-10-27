"""
Business Card Generation Utilities
Automatically generates digital business cards for users when no existing card link is provided.
"""

from flask import url_for
from app.models import User, Profile
from app import db
import json
from typing import Dict, Optional


def generate_business_card_data(user: User) -> Dict:
    """
    Generate business card data structure for a user.
    
    Args:
        user: User instance
        
    Returns:
        Dictionary containing business card data
    """
    profile = user.profile
    
    # Basic contact information
    card_data = {
        'name': profile.display_name or user.name,
        'email': user.email,
        'phone': user.phone,
        'headline': profile.headline if profile else None,
        'bio': profile.bio if profile else None,
        'avatar_url': profile.avatar_url if profile else None,
        'theme': profile.theme if profile else 'light',
        'links': profile.links() if profile else [],
        'created_at': user.created_at.isoformat(),
        'profile_url': None  # Will be set after profile creation
    }
    
    # If user has a profile, include the public profile URL
    if profile and profile.username:
        card_data['profile_url'] = url_for('public.profile', username=profile.username, _external=True)
    
    return card_data


def ensure_user_has_profile(user: User) -> Profile:
    """
    Ensure user has a profile, create one if it doesn't exist.
    
    Args:
        user: User instance
        
    Returns:
        Profile instance
    """
    if user.profile:
        return user.profile
    
    # Generate a unique username based on email
    base_username = user.email.split('@')[0].lower()
    username = base_username
    counter = 1
    
    # Ensure username is unique
    while Profile.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Create new profile
    profile = Profile(
        user_id=user.id,
        username=username,
        display_name=user.name,
        headline="Digital Business Card",
        theme='light'
    )
    
    db.session.add(profile)
    db.session.flush()  # Get the profile ID
    
    return profile


def generate_default_business_card_url(user: User) -> str:
    """
    Generate a default business card URL for a user.
    This creates a profile if one doesn't exist and returns the public profile URL.
    
    Args:
        user: User instance
        
    Returns:
        URL string pointing to the user's digital business card
    """
    # Ensure user has a profile
    profile = ensure_user_has_profile(user)
    
    # Return the public profile URL
    return url_for('public.profile', username=profile.username, _external=True)


def create_business_card_links(user: User, additional_links: Optional[list] = None) -> list:
    """
    Create default business card links for a user.
    
    Args:
        user: User instance
        additional_links: Optional list of additional links to include
        
    Returns:
        List of link dictionaries
    """
    links = []
    
    # Add email link
    if user.email:
        links.append({
            'title': 'Email',
            'url': f'mailto:{user.email}',
            'icon': 'fas fa-envelope',
            'type': 'email'
        })
    
    # Add phone link
    if user.phone:
        links.append({
            'title': 'Phone',
            'url': f'tel:{user.phone}',
            'icon': 'fas fa-phone',
            'type': 'phone'
        })
    
    # Add any additional links provided
    if additional_links:
        links.extend(additional_links)
    
    return links


def update_profile_with_business_card_defaults(profile: Profile, user: User):
    """
    Update a profile with default business card settings.
    
    Args:
        profile: Profile instance to update
        user: User instance for contact info
    """
    # Set default links if none exist
    if not profile.links():
        default_links = create_business_card_links(user)
        profile.set_links(default_links)
    
    # Set default headline if none exists
    if not profile.headline:
        profile.headline = "Digital Business Card"
    
    # Set default display name if none exists
    if not profile.display_name:
        profile.display_name = user.name
    
    db.session.add(profile)


def is_business_card_complete(user: User) -> bool:
    """
    Check if a user's business card profile is complete.
    
    Args:
        user: User instance
        
    Returns:
        Boolean indicating if business card is complete
    """
    if not user.profile:
        return False
    
    profile = user.profile
    
    # Check for essential business card elements
    has_name = bool(profile.display_name or user.name)
    has_contact = bool(user.email or user.phone)
    has_username = bool(profile.username)
    
    return has_name and has_contact and has_username
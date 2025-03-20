"""Advanced validation utilities for CyberShield-AI."""

import re
from fastapi import HTTPException
from typing import List, Optional

def validate_email(email: str, allowed_domains: Optional[List[str]] = None) -> bool:
    """
    Validate email format and domain.
    
    Args:
        email: Email address to validate
        allowed_domains: List of allowed domains
        
    Returns:
        bool: True if email is valid
        
    Raises:
        HTTPException: If email is invalid
    """
    if not email:
        raise HTTPException(status_code=400, detail="Email cannot be empty")
        
    # Normalize email
    email = email.strip().lower()
    
    # Check basic email format
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Check domain if allowed domains specified
    if allowed_domains:
        try:
            domain = email.split('@')[1]
            if domain not in allowed_domains:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid email domain. Please use one of: {', '.join(allowed_domains)}"
                )
        except IndexError:
            raise HTTPException(status_code=400, detail="Invalid email format")
    
    return True

def validate_password(
    password: str, 
    min_length: int = 8, 
    max_length: int = 64,
    min_strength: int = 3
) -> bool:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        min_length: Minimum length required
        max_length: Maximum length allowed
        min_strength: Minimum strength score required
        
    Returns:
        bool: True if password is valid
        
    Raises:
        HTTPException: If password fails validation
    """
    if not password:
        raise HTTPException(status_code=400, detail="Password cannot be empty")
        
    # Check length
    if len(password) < min_length:
        raise HTTPException(status_code=400, detail=f"Password must be at least {min_length} characters")
    
    if len(password) > max_length:
        raise HTTPException(status_code=400, detail=f"Password must be at most {max_length} characters")
    
    # Evaluate strength
    strength = evaluate_password_strength(password)
    
    # Check if meets minimum strength
    if strength < min_strength:
        raise HTTPException(
            status_code=400, 
            detail=f"Password is too weak (score: {strength}/4). Please include uppercase, lowercase, numbers, and special characters."
        )
    
    return True

def evaluate_password_strength(password: str) -> int:
    """
    Evaluate password strength on a scale of 0-4.
    
    Criteria:
    - Length >= 8 characters: +1
    - Contains both uppercase and lowercase: +1
    - Contains digits: +1
    - Contains special characters: +1
    
    Args:
        password: Password to evaluate
        
    Returns:
        int: Strength score (0-4)
    """
    strength = 0
    
    # Length check
    if len(password) >= 8:
        strength += 1
    
    # Case check (both upper and lower)
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        strength += 1
    
    # Digit check
    if re.search(r"[0-9]", password):
        strength += 1
    
    # Special character check
    if re.search(r"[^a-zA-Z0-9]", password):
        strength += 1
    
    return strength

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if phone number is valid
        
    Raises:
        HTTPException: If phone number is invalid
    """
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number cannot be empty")
    
    # Remove any non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    
    # Check length
    if len(phone_digits) < 10 or len(phone_digits) > 15:
        raise HTTPException(status_code=400, detail="Phone number must be between 10 and 15 digits")
    
    return True
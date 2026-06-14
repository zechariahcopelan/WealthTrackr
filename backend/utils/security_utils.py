# ~/Documents/WealthTrackr/backend/utils/security_utils.py

import os
import re
import secrets
import string
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import pyotp
import qrcode
import io
from fastapi import HTTPException, status
import logging

# Import your models and auth functions
from backend.models.models_user import User
from backend.auth import get_password_hash, verify_password

logger = logging.getLogger(__name__)

# ─── Password Context ───────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Security Configuration ─────────────────────────────────────────────────────
# Rate limiting settings
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = timedelta(minutes=15)
LOCKOUT_DURATION = timedelta(minutes=30)

# Password requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGITS = True
REQUIRE_SPECIAL_CHARS = True

# Session and token settings
SESSION_TIMEOUT = timedelta(hours=24)
PASSWORD_RESET_TOKEN_EXPIRY = timedelta(hours=1)
EMAIL_VERIFICATION_TOKEN_EXPIRY = timedelta(days=7)

# Two-Factor Authentication
TOTP_ISSUER_NAME = "WealthTrackr"

# ─── Password Security Functions ────────────────────────────────────────────────
def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Comprehensive password strength validation
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    # Length check
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be no more than {MAX_PASSWORD_LENGTH} characters long")
    
    # Character requirements
    if REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if REQUIRE_DIGITS and not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*()_+=\-\[\]{}|;:,.<>?]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
    
    # Common password patterns (basic check)
    common_patterns = [
        r'123456', r'password', r'qwerty', r'abc123', r'admin',
        r'letmein', r'welcome', r'monkey', r'dragon'
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            errors.append("Password contains common patterns that are easily guessed")
            break
    
    # Sequential characters check
    if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
        errors.append("Password should not contain sequential numbers")
    
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
        errors.append("Password should not contain sequential letters")
    
    return len(errors) == 0, errors

def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password"""
    if length < MIN_PASSWORD_LENGTH:
        length = MIN_PASSWORD_LENGTH
    
    # Ensure we have at least one of each required character type
    password_chars = []
    
    if REQUIRE_UPPERCASE:
        password_chars.append(secrets.choice(string.ascii_uppercase))
    if REQUIRE_LOWERCASE:
        password_chars.append(secrets.choice(string.ascii_lowercase))
    if REQUIRE_DIGITS:
        password_chars.append(secrets.choice(string.digits))
    if REQUIRE_SPECIAL_CHARS:
        password_chars.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
    
    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    for _ in range(length - len(password_chars)):
        password_chars.append(secrets.choice(all_chars))
    
    # Shuffle the password characters
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)

def validate_password_change(db: Session, user: User, current_password: str, new_password: str) -> bool:
    """
    Validate and process password change
    """
    try:
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            logger.warning(f"Invalid current password for user: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        is_valid, errors = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {', '.join(errors)}"
            )
        
        # Check if new password is different from current
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        # Hash new password and update
        new_hashed_password = get_password_hash(new_password)
        user.hashed_password = new_hashed_password
        user.password_changed_at = datetime.now(timezone.utc)
        
        # Clear any password reset tokens
        user.password_reset_token = None
        user.password_reset_expires = None
        
        db.commit()
        
        logger.info(f"Password changed successfully for user: {user.username}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password for user {user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

def check_password_history(user: User, new_password: str, history_count: int = 5) -> bool:
    """
    Check if password was used recently (requires password history table)
    This is a placeholder - you'd need to implement password history storage
    """
    # TODO: Implement password history check
    # For now, just return True (password is not in history)
    return True

# ─── Account Security Functions ─────────────────────────────────────────────────
def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def generate_verification_code(length: int = 6) -> str:
    """Generate a numeric verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def hash_token(token: str) -> str:
    """Hash a token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def verify_token_hash(token: str, token_hash: str) -> bool:
    """Verify a token against its hash"""
    return hashlib.sha256(token.encode()).hexdigest() == token_hash

# ─── Rate Limiting Functions ────────────────────────────────────────────────────
# In-memory storage for demo (use Redis in production)
_login_attempts = {}
_lockout_times = {}

def record_login_attempt(identifier: str, success: bool = False):
    """Record a login attempt for rate limiting"""
    now = datetime.now(timezone.utc)
    
    if identifier not in _login_attempts:
        _login_attempts[identifier] = []
    
    # Clean old attempts
    _login_attempts[identifier] = [
        attempt_time for attempt_time in _login_attempts[identifier]
        if now - attempt_time < LOGIN_ATTEMPT_WINDOW
    ]
    
    if not success:
        _login_attempts[identifier].append(now)
        
        # Check if account should be locked
        if len(_login_attempts[identifier]) >= MAX_LOGIN_ATTEMPTS:
            _lockout_times[identifier] = now + LOCKOUT_DURATION
            logger.warning(f"Account locked due to too many failed attempts: {identifier}")

def is_account_locked(identifier: str) -> bool:
    """Check if account is locked due to failed login attempts"""
    if identifier in _lockout_times:
        if datetime.now(timezone.utc) < _lockout_times[identifier]:
            return True
        else:
            # Lockout expired, clean up
            del _lockout_times[identifier]
            if identifier in _login_attempts:
                del _login_attempts[identifier]
    
    return False

def get_remaining_attempts(identifier: str) -> int:
    """Get number of remaining login attempts before lockout"""
    if identifier not in _login_attempts:
        return MAX_LOGIN_ATTEMPTS
    
    now = datetime.now(timezone.utc)
    recent_attempts = [
        attempt_time for attempt_time in _login_attempts[identifier]
        if now - attempt_time < LOGIN_ATTEMPT_WINDOW
    ]
    
    return max(0, MAX_LOGIN_ATTEMPTS - len(recent_attempts))

def clear_login_attempts(identifier: str):
    """Clear login attempts after successful login"""
    if identifier in _login_attempts:
        del _login_attempts[identifier]
    if identifier in _lockout_times:
        del _lockout_times[identifier]

# ─── Two-Factor Authentication Functions ────────────────────────────────────────
def generate_totp_secret() -> str:
    """Generate a new TOTP secret for 2FA"""
    return pyotp.random_base32()

def generate_totp_qr_code(user_email: str, secret: str) -> bytes:
    """Generate QR code for TOTP setup"""
    try:
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=TOTP_ISSUER_NAME
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error generating TOTP QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate QR code"
        )

def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify TOTP code"""
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    except Exception as e:
        logger.error(f"Error verifying TOTP code: {e}")
        return False

def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup codes for 2FA recovery"""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric codes
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        codes.append(f"{code[:4]}-{code[4:]}")  # Format as XXXX-XXXX
    
    return codes

# ─── Security Monitoring Functions ──────────────────────────────────────────────
def log_security_event(user_id: Optional[int], event_type: str, details: Dict, ip_address: Optional[str] = None):
    """Log security events for monitoring"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "event_type": event_type,
        "details": details,
        "ip_address": ip_address
    }
    
    # In production, you'd send this to a security monitoring system
    logger.info(f"Security Event: {log_entry}")

def detect_suspicious_activity(user: User, ip_address: str, user_agent: str) -> List[str]:
    """Detect potentially suspicious login activity"""
    warnings = []
    
    # Check for login from new location (simplified)
    # In production, you'd have a more sophisticated geolocation system
    if hasattr(user, 'last_login_ip') and user.last_login_ip != ip_address:
        warnings.append("Login from new IP address")
    
    # Check for unusual time
    now = datetime.now(timezone.utc)
    hour = now.hour
    if hour < 6 or hour > 22:  # Outside normal hours
        warnings.append("Login outside normal hours")
    
    # Check for rapid successive logins
    if (hasattr(user, 'last_login') and user.last_login and 
        now - user.last_login < timedelta(minutes=5)):
        warnings.append("Rapid successive login detected")
    
    return warnings

# ─── Data Sanitization Functions ────────────────────────────────────────────────
def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not input_string:
        return ""
    
    # Remove or escape potentially dangerous characters
    sanitized = input_string.strip()
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def validate_email_format(email: str) -> bool:
    """Validate email format with regex"""
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    return bool(email_pattern.match(email))

def validate_username_format(username: str) -> Tuple[bool, List[str]]:
    """Validate username format and security"""
    errors = []
    
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    
    if len(username) > 30:
        errors.append("Username must be no more than 30 characters long")
    
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        errors.append("Username can only contain letters, numbers, underscores, periods, and hyphens")
    
    if username.startswith('.') or username.endswith('.'):
        errors.append("Username cannot start or end with a period")
    
    # Check for reserved usernames
    reserved_usernames = [
        'admin', 'administrator', 'root', 'support', 'api', 'www',
        'mail', 'email', 'system', 'null', 'undefined', 'test'
    ]
    
    if username.lower() in reserved_usernames:
        errors.append("This username is reserved and cannot be used")
    
    return len(errors) == 0, errors

# ─── Encryption Helpers ─────────────────────────────────────────────────────────
def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """
    Encrypt sensitive data (placeholder for actual encryption)
    In production, use proper encryption like Fernet or similar
    """
    if not key:
        key = os.getenv("ENCRYPTION_KEY", "default-key-change-in-production")
    
    # This is a simple base64 encoding - replace with real encryption in production
    encoded = base64.b64encode(data.encode()).decode()
    return encoded

def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """
    Decrypt sensitive data (placeholder for actual decryption)
    """
    if not key:
        key = os.getenv("ENCRYPTION_KEY", "default-key-change-in-production")
    
    # This is a simple base64 decoding - replace with real decryption in production
    try:
        decoded = base64.b64decode(encrypted_data.encode()).decode()
        return decoded
    except Exception as e:
        logger.error(f"Error decrypting data: {e}")
        raise ValueError("Failed to decrypt data")

# ─── Session Security ───────────────────────────────────────────────────────────
def generate_session_id() -> str:
    """Generate secure session ID"""
    return secrets.token_urlsafe(32)

def validate_session_security(session_data: Dict) -> bool:
    """Validate session security parameters"""
    required_fields = ['user_id', 'created_at', 'ip_address']
    
    for field in required_fields:
        if field not in session_data:
            return False
    
    # Check session age
    created_at = session_data.get('created_at')
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    if datetime.now(timezone.utc) - created_at > SESSION_TIMEOUT:
        return False
    
    return True

# ─── Security Headers and CSRF Protection ──────────────────────────────────────
def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)

def validate_csrf_token(token: str, expected_token: str) -> bool:
    """Validate CSRF token using constant-time comparison"""
    return secrets.compare_digest(token, expected_token)

def get_security_headers() -> Dict[str, str]:
    """Get recommended security headers"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

# ─── Audit Trail Functions ──────────────────────────────────────────────────────
def create_audit_log(user_id: int, action: str, resource: str, details: Optional[Dict] = None):
    """Create audit log entry"""
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "details": details or {},
        "ip_address": None,  # Would be populated from request context
        "user_agent": None   # Would be populated from request context
    }
    
    # In production, save to audit log table
    logger.info(f"Audit Log: {audit_entry}")

# ─── Export Functions ───────────────────────────────────────────────────────────
__all__ = [
    'validate_password_strength',
    'generate_secure_password', 
    'validate_password_change',
    'generate_secure_token',
    'is_account_locked',
    'record_login_attempt',
    'clear_login_attempts',
    'generate_totp_secret',
    'verify_totp_code',
    'generate_backup_codes',
    'sanitize_input',
    'validate_email_format',
    'validate_username_format',
    'log_security_event',
    'detect_suspicious_activity'
]

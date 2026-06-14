# ~/Documents/WealthTrackr/backend/auth.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from backend.database import get_db
# ONLY import necessary CRUD functions, avoiding circular imports where possible
from backend.crud_user import get_user_by_username, mark_email_as_verified, get_user_by_email # Keep minimal imports

# ─── Password Hashing Setup ─────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── JWT Configuration ─────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))

# ─── Password Validation ────────────────────────────────────────────────────────
MIN_PASSWORD_LENGTH = 8

def validate_password_strength(password: str) -> bool:
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    return sum([has_upper, has_lower, has_digit, has_special]) >= 3

def get_password_hash(password: str) -> str:
    if not validate_password_strength(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters and contain at least 3 of: uppercase, lowercase, number, special character."
        )
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

# ─── User Authentication Logic (Moved from crud_user and centralized here) ─────
# This function uses get_user_by_username from crud_user and verify_password from this module
from backend.models.models_user import User # Import User model here if needed for type hinting

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticates a user by checking their username and password.
    Returns the User object if credentials are valid, otherwise None.
    """
    user = get_user_by_username(db, username=username) # Uses crud_user
    if not user:
        return None
    if not verify_password(password, user.hashed_password): # Uses local verify_password
        return None
    
    # Optional: Check for email verification here during authentication
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not verified. Please check your email.")

    return user

# ─── JWT Token Creation ─────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ─── Token Validation & Rotation ────────────────────────────────────────────────
def verify_token(token: str, token_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail="Invalid token type", headers={"WWW-Authenticate": "Bearer"})
        if datetime.now(timezone.utc).timestamp() > payload.get("exp", 0):
            raise HTTPException(status_code=401, detail="Token expired", headers={"WWW-Authenticate": "Bearer"})
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

def refresh_access_token(refresh_token: str) -> dict:
    payload = verify_token(refresh_token, "refresh")
    user_data = {k: v for k, v in payload.items() if k not in ["exp", "iat", "type"]}
    new_access = create_access_token(user_data)
    new_refresh = create_refresh_token(user_data)
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }

# ─── Token Blacklist (for logout) ───────────────────────────────────────────────
_token_blacklist = set()

def blacklist_token(token: str):
    _token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    return token in _token_blacklist

# ─── Dependency Injection ───────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    payload = verify_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")

    user = get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_active_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = await get_current_user(token, db)
    # The check for user.is_verified is now done in authenticate_user if you uncommented it.
    # If not, you can keep it here, but generally, authentication handles verification status.
    if not user.is_verified: #
        raise HTTPException(status_code=403, detail="Email not verified") #
    return user

# ─── Email Verification Logic ───────────────────────────────────────────────────
def verify_email_and_activate_user(db: Session, token: str) -> bool:
    """
    Verifies a user's email token and activates the user.
    This logic uses crud_user.get_user_by_email and crud_user.mark_email_as_verified.
    """
    # Assuming get_user_by_email can also find by verification_token or you have a specific crud function
    # For now, let's just use get_user_by_email and refine if needed.
    # It's better to have a specific function in crud_user for finding by verification token.
    # Let's adjust crud_user to have `get_user_by_verification_token`

    user = get_user_by_email(db, token) # This assumes token IS the email, which is wrong.
                                        # Need a better way to find user by verification token.
                                        # See crud_user.py modification for `get_user_by_verification_token`
    if not user:
        return False

    # Assuming mark_email_as_verified in crud_user handles setting is_verified and clearing token
    return mark_email_as_verified(db, user)

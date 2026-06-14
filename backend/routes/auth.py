# ~/Documents/WealthTrackr/backend/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone

# Corrected imports for models and schemas
from backend.models.models_user import User as UserModel
from backend.schemas.schemas_user import UserCreate, UserResponse, Token

# Core authentication logic and utilities from backend.auth
from backend.auth import (
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_refresh_token,
    refresh_access_token,
    blacklist_token,
    get_current_user,
    oauth2_scheme,
    verify_password
)

# CRUD operations from backend.crud_user (using only functions that exist)
from backend.crud_user import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_verification_token,
    mark_email_as_verified
)

# Database session dependency
from backend.database import get_db

# Email utility for sending verification emails
from backend.utils.email_utils import send_verification_email

# --------------------------------------------------------------------------------------
# Initialize the router
router = APIRouter(tags=["Authentication"])

# --------------------------------------------------------------------------------------
def authenticate_user_login(db: Session, username: str, password: str) -> UserModel:
    """
    Internal function to authenticate user login since it was removed from crud_user
    """
    # Queries the database to find a user that matches the provided username
    user = get_user_by_username(db, username)
    # If no user was found in the DB, the function exits early by returning None
    if not user:
        return None
    # verify_password compares the plain-text password against the hashed password stored in the DB
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

# --------------------------------------------------------------------------------------
@router.post("/register", response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db), request: Request = None):
    """
    Registers a new user, hashes their password, and sends a verification email.
    """
    # Check if username exists
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    db_email = get_user_by_email(db, email=user.email)
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Hash the password using auth.py function
        hashed_password = get_password_hash(user.password)
        
        # Create user with hashed password (matching your crud_user function signature)
        db_user = create_user(db, user_data=user, hashed_password=hashed_password)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException as he:
        raise he  # Re-raise password validation errors from get_password_hash
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {e}")

    # Send verification email with correct parameters (request, email, username, token)
    try:
        send_verification_email(request, db_user.email, db_user.username, db_user.verification_token)
    except Exception as e:
        # User created but email failed - still return success
        print(f"Failed to send verification email: {e}")

    return {
        "message": "User created successfully. Please check your email to verify your account.",
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email
    }

# --------------------------------------------------------------------------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Handles user login, authenticates credentials, and issues access and refresh tokens.
    """
    user = authenticate_user_login(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before logging in."
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# --------------------------------------------------------------------------------------
@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    Retrieves the current authenticated user's details.
    """
    return current_user

# --------------------------------------------------------------------------------------
@router.post("/refresh", response_model=Token)
async def refresh_token_route(refresh_token: str = Form(...)):
    """
    Refreshes an expired access token using a valid refresh token.
    """
    try:
        new_tokens = refresh_access_token(refresh_token)
        return new_tokens
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not refresh token")

# --------------------------------------------------------------------------------------
@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    Logs out a user by blacklisting their current access token.
    """
    blacklist_token(token)
    return {"message": "Successfully logged out."}

# --------------------------------------------------------------------------------------
@router.get("/verify-email")
async def verify_email_route(token: str, db: Session = Depends(get_db)):
    """
    Verifies a user's email address using a token sent to their email.
    """
    try:
        print(f"🔍 Received token: {token}")
        
        # Try JWT token verification first
        try:
            from backend.auth import verify_token
            payload = verify_token(token, token_type="access")
            username = payload.get("sub")
            print(f"🔍 JWT verification successful, username: {username}")
            
            if username:
                user = get_user_by_username(db, username)
                if user and not user.is_verified:
                    success = mark_email_as_verified(db, user)
                    if success:
                        return {"message": "Email verified successfully!", "verified": True}
        except Exception as jwt_error:
            print(f"🔍 JWT verification failed: {jwt_error}")
        
        # If JWT verification fails, try database token verification
        print("🔍 Trying database token verification...")
        user = get_user_by_verification_token(db, token)
        print(f"🔍 Database lookup result: {user.username if user else 'None'}")
        
        if user:
            print(f"🔍 User found: {user.username}, is_verified: {user.is_verified}")
            if not user.is_verified:
                success = mark_email_as_verified(db, user)
                print(f"🔍 Mark as verified result: {success}")
                if success:
                    return {"message": "Email verified successfully!", "verified": True}
            else:
                return {"message": "Email already verified", "verified": True}
        
        print("🔍 No valid token found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🔍 Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

# --------------------------------------------------------------------------------------
@router.post("/resend-verification")
async def resend_verification_email(
    request: Request,
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Resend verification email to user
    """
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        return {"message": "Email already verified", "verified": True}
    
    try:
        send_verification_email(request, user.email, user.username, user.verification_token)
        return {"message": "Verification email sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

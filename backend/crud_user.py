# ~/Documents/WealthTrackr/backend/crud_user.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from backend.models.models_user import User
from backend.schemas.schemas_user import UserCreate, UserUpdate, PasswordChange

# Set up logging
logger = logging.getLogger(__name__)

# ─── Helper Functions ─────────────────────────────────────────────────────────

def generate_verification_token(length: int = 32) -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

# ─── CRUD Logic ───────────────────────────────────────────────────────────────

def create_user(db: Session, user_data: UserCreate, hashed_password: str) -> User:
    """
    Creates a new user in the database with an already hashed password.
    """
    try:
        existing_user = get_user_by_username(db, user_data.username)
        if existing_user:
            logger.warning(f"Attempt to create user with existing username: {user_data.username}")
            raise ValueError("Username already exists")

        existing_email = get_user_by_email(db, user_data.email)
        if existing_email:
            logger.warning(f"Attempt to create user with existing email: {user_data.email}")
            raise ValueError("Email already exists")

        token = generate_verification_token()

        db_user = User(
            username=user_data.username,
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            is_verified=False,
            verification_token=token,
            verification_sent_at=datetime.now(timezone.utc)
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"User created with verification pending: {db_user.username} ({db_user.email})")
        return db_user

    except ValueError:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error creating user: {str(e)}")
        raise ValueError("Username or email already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating user: {str(e)}")
        raise Exception(f"Failed to create user: {str(e)}")

def get_user_by_verification_token(db: Session, token: str) -> Optional[User]:
    """Get user by verification token"""
    try:
        return db.query(User).filter(User.verification_token == token).first()
    except Exception as e:
        logger.error(f"Error retrieving user by verification token {token}: {str(e)}")
        return None

def mark_email_as_verified(db: Session, user: User) -> bool:
    """Mark a user's email as verified and clear verification token."""
    try:
        if user.is_verified:
            logger.info(f"Email already verified for user: {user.username}")
            return True

        user.is_verified = True
        user.verification_token = None
        user.verification_sent_at = None
        db.commit()
        logger.info(f"Email marked as verified for user: {user.username}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking email as verified for user {user.username}: {str(e)}")
        return False

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    try:
        return db.query(User).filter(User.username == username).first()
    except Exception as e:
        logger.error(f"Error retrieving user by username {username}: {str(e)}")
        return None

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    try:
        return db.query(User).filter(User.email == email.lower()).first()
    except Exception as e:
        logger.error(f"Error retrieving user by email {email}: {str(e)}")
        return None

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception as e:
        logger.error(f"Error retrieving user by ID {user_id}: {str(e)}")
        return None

# ─── NEW FUNCTIONS ADDED FOR USER ROUTES ────────────────────────────────────────

def update_user_profile(db: Session, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
    """
    Update user profile with dictionary of fields to update.
    This replaces the old update_user function to be more flexible.
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to update non-existent user: {user_id}")
            return None

        # Check for unique constraints if username or email is being updated
        if 'username' in update_data and update_data['username'] != user.username:
            existing_user = get_user_by_username(db, update_data['username'])
            if existing_user and existing_user.id != user_id:
                raise ValueError("Username already exists")

        if 'email' in update_data and update_data['email'].lower() != user.email:
            existing_email = get_user_by_email(db, update_data['email'])
            if existing_email and existing_email.id != user_id:
                raise ValueError("Email already exists")
            # If email changes, mark as unverified and generate new token
            update_data['email'] = update_data['email'].lower()
            update_data['is_verified'] = False
            update_data['verification_token'] = generate_verification_token()
            update_data['verification_sent_at'] = datetime.now(timezone.utc)

        # Update all provided fields
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        # Always update the updated_at timestamp
        user.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        logger.info(f"User profile updated successfully: {user.username}")
        return user

    except ValueError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user profile {user_id}: {str(e)}")
        return None

def update_user_bio(db: Session, user_id: int, bio: str) -> Optional[User]:
    """
    Update user bio specifically.
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to update bio for non-existent user: {user_id}")
            return None

        user.bio = bio
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)

        logger.info(f"Bio updated successfully for user: {user.username}")
        return user

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating bio for user {user_id}: {str(e)}")
        return None

def get_users_list(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> list[User]:
    """
    Get a list of users with optional search and pagination.
    """
    try:
        query = db.query(User)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                User.username.ilike(search_pattern) |
                User.email.ilike(search_pattern) |
                User.first_name.ilike(search_pattern) |
                User.last_name.ilike(search_pattern)
            )
        
        return query.offset(skip).limit(limit).all()
        
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        return []

def get_user_count(db: Session, search: Optional[str] = None) -> int:
    """
    Get total count of users (for pagination).
    """
    try:
        query = db.query(User)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                User.username.ilike(search_pattern) |
                User.email.ilike(search_pattern) |
                User.first_name.ilike(search_pattern) |
                User.last_name.ilike(search_pattern)
            )
        
        return query.count()
        
    except Exception as e:
        logger.error(f"Error getting user count: {str(e)}")
        return 0

def soft_delete_user(db: Session, user_id: int) -> bool:
    """
    Soft delete a user (mark as inactive instead of actually deleting).
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to delete non-existent user: {user_id}")
            return False

        # Soft delete by updating status
        user.account_status = "inactive"
        user.is_verified = False
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"User soft deleted successfully: {user.username}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error soft deleting user {user_id}: {str(e)}")
        return False

def reactivate_user(db: Session, user_id: int) -> bool:
    """
    Reactivate a soft-deleted user.
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to reactivate non-existent user: {user_id}")
            return False

        user.account_status = "active"
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"User reactivated successfully: {user.username}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error reactivating user {user_id}: {str(e)}")
        return False

def update_user_preferences(db: Session, user_id: int, preferences: Dict[str, Any]) -> Optional[User]:
    """
    Update user preferences and settings.
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to update preferences for non-existent user: {user_id}")
            return None

        # Update preferences fields
        preference_fields = [
            'language', 'currency', 'timezone', 'theme', 'email_notifications',
            'push_notifications', 'budget_alerts', 'goal_reminders'
        ]
        
        for field in preference_fields:
            if field in preferences:
                setattr(user, field, preferences[field])

        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)

        logger.info(f"Preferences updated successfully for user: {user.username}")
        return user

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
        return None

def update_user_security_settings(db: Session, user_id: int, security_data: Dict[str, Any]) -> Optional[User]:
    """
    Update user security settings like 2FA, security questions, etc.
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to update security settings for non-existent user: {user_id}")
            return None

        # Update security fields
        security_fields = [
            'two_factor_enabled', 'totp_secret', 'backup_codes',
            'security_question_1', 'security_answer_1',
            'security_question_2', 'security_answer_2'
        ]
        
        for field in security_fields:
            if field in security_data:
                setattr(user, field, security_data[field])

        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)

        logger.info(f"Security settings updated successfully for user: {user.username}")
        return user

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating security settings for user {user_id}: {str(e)}")
        return None

def get_user_activity_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get user activity statistics.
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return {}

        # Calculate basic stats
        stats = {
            'user_id': user_id,
            'username': user.username,
            'account_created': user.created_at,
            'last_updated': user.updated_at,
            'is_verified': user.is_verified,
            'account_status': getattr(user, 'account_status', 'active'),
            'login_count': getattr(user, 'login_count', 0),
            'last_login': getattr(user, 'last_login', None),
        }

        # Add profile completion stats
        required_fields = ['first_name', 'last_name', 'bio', 'phone_number', 'location']
        completed_fields = sum(1 for field in required_fields if getattr(user, field, None))
        stats['profile_completion'] = (completed_fields / len(required_fields)) * 100

        return stats

    except Exception as e:
        logger.error(f"Error getting activity stats for user {user_id}: {str(e)}")
        return {}

# ─── EXISTING FUNCTIONS (KEPT FOR COMPATIBILITY) ─────────────────────────────────

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    Updates user information in the database.
    (Kept for backward compatibility - use update_user_profile for new code)
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to update non-existent user: {user_id}")
            return None

        if user_update.username and user_update.username != user.username:
            existing_user = get_user_by_username(db, user_update.username)
            if existing_user and existing_user.id != user_id:
                raise ValueError("Username already exists")
            user.username = user_update.username

        if user_update.email and user_update.email.lower() != user.email:
            existing_email = get_user_by_email(db, user_update.email)
            if existing_email and existing_email.id != user_id:
                raise ValueError("Email already exists")
            user.email = user_update.email.lower()
            user.is_verified = False
            user.verification_token = generate_verification_token()
            user.verification_sent_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        logger.info(f"User updated successfully: {user.username}")
        return user

    except ValueError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return None

def change_password(db: Session, user_id: int, hashed_new_password: str) -> bool:
    """
    Changes a user's password using an already hashed new password.
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to change password for non-existent user: {user_id}")
            return False

        user.hashed_password = hashed_new_password
        user.password_changed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Password changed successfully for user: {user.username}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password for user {user_id}: {str(e)}")
        return False

def delete_user(db: Session, user_id: int) -> bool:
    """
    Hard delete a user from the database.
    (Consider using soft_delete_user instead for production)
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempt to delete non-existent user: {user_id}")
            return False

        username = user.username
        db.delete(user)
        db.commit()

        logger.info(f"User deleted successfully: {username}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return False

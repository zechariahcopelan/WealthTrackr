# ~/Documents/WealthTrackr/backend/routes/users.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

# Database and authentication dependencies
from backend.database import get_db
from backend.auth import get_current_user, get_current_active_user

# Models
from backend.models.models_user import User as UserModel

# Form validation schemas (our Python equivalent of Express validators)
from backend.schemas.forms import (
    UserUpdateForm,
    UserBioUpdateForm,
    PasswordChangeForm,
    NotificationPreferencesForm
)

# User serializers (our Python equivalent of UserSerializer.js)
from backend.schemas.user_serializers import (
    UserDetailSerializer,
    UserPublicSerializer,
    ProfileCompletionSerializer,
    UserSettingsSerializer,
    UserUpdateResponseSerializer,
    calculate_profile_completion,
    serialize_user_for_response
)

# CRUD operations
from backend.crud_user import (
    get_user_by_id,
    update_user_profile,
    update_user_bio,
    get_user_by_username
)

# Utility functions
from backend.utils.file_utils import save_profile_picture, validate_image_file
from backend.utils.security_utils import validate_password_change


# ─── Initialize Router ──────────────────────────────────────────────────────────
router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_active_user)]  # All routes require authentication
)


# ─── User Profile Routes ────────────────────────────────────────────────────────
@router.get("/{user_id}", response_model=UserDetailSerializer)
async def get_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID
    Equivalent to: router.get('/:id', auth, getUser);
    """
    # Check if user is requesting their own profile or has permission
    if user_id != current_user.id and current_user.user_role not in ["admin", "moderator"]:
        # Return public profile for other users
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserPublicSerializer.from_orm(user)
    
    # Return full profile for own account or admin access
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserDetailSerializer.from_orm(user)


@router.put("/{user_id}", response_model=UserUpdateResponseSerializer)
async def update_user(
    user_id: int,
    user_data: UserUpdateForm,  # This replaces updateUserValidation middleware
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile
    Equivalent to: router.put('/:id', auth, updateUserValidation, updateUser);
    """
    # Verify user can update this profile
    if user_id != current_user.id and current_user.user_role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile"
        )
    
    try:
        # Get the user to update
        user_to_update = get_user_by_id(db, user_id)
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Extract only the fields that were provided (exclude None values)
        update_data = user_data.dict(exclude_unset=True)
        
        # Add timestamp
        update_data['updated_at'] = datetime.now()
        
        # Update user in database
        updated_user = update_user_profile(db, user_id, update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user"
            )
        
        # Calculate profile completion
        completion_data = calculate_profile_completion(updated_user)
        
        return UserUpdateResponseSerializer(
            success=True,
            message="User updated successfully",
            user=UserDetailSerializer.from_orm(updated_user),
            updated_fields=list(update_data.keys()),
            profile_completion_percentage=completion_data.profile_completion_percentage,
            missing_fields=completion_data.missing_fields,
            recommendations=completion_data.recommendations
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.patch("/{user_id}/bio", response_model=dict)
async def update_bio(
    user_id: int,
    bio_data: UserBioUpdateForm,  # This replaces updateBioValidation middleware
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user bio specifically
    Equivalent to: router.patch('/:id/bio', auth, updateBioValidation, updateBio);
    """
    # Verify user can update this bio
    if user_id != current_user.id and current_user.user_role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this bio"
        )
    
    try:
        # Get the user to update
        user_to_update = get_user_by_id(db, user_id)
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update bio in database
        updated_user = update_user_bio(db, user_id, bio_data.bio)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update bio"
            )
        
        return {
            "success": True,
            "message": "Bio updated successfully",
            "user": UserDetailSerializer.from_orm(updated_user).dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bio update failed: {str(e)}"
        )


@router.patch("/{user_id}/profile-picture", response_model=dict)
async def update_profile_picture(
    user_id: int,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile picture
    Equivalent to: router.patch('/:id/profile-picture', auth, updateProfilePicture);
    """
    # Verify user can update this profile picture
    if user_id != current_user.id and current_user.user_role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile picture"
        )
    
    try:
        # Validate file
        if not validate_image_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file. Please upload a JPG, PNG, or GIF file under 5MB."
            )
        
        # Get the user to update
        user_to_update = get_user_by_id(db, user_id)
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Save the uploaded file
        file_url = await save_profile_picture(file, user_id)
        
        # Update user profile picture URL in database
        update_data = {
            "profile_pic_url": file_url,
            "updated_at": datetime.now()
        }
        
        updated_user = update_user_profile(db, user_id, update_data)
        
        return {
            "success": True,
            "message": "Profile picture updated successfully",
            "profile_pic_url": file_url,
            "user": UserDetailSerializer.from_orm(updated_user).dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile picture update failed: {str(e)}"
        )


@router.get("/{user_id}/completion", response_model=ProfileCompletionSerializer)
async def get_profile_completion(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get profile completion percentage and recommendations
    Equivalent to: router.get('/:id/completion', auth, getProfileCompletion);
    """
    # Verify user can access this profile completion data
    if user_id != current_user.id and current_user.user_role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile completion data"
        )
    
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Calculate profile completion using our helper function
        completion_data = calculate_profile_completion(user)
        
        return completion_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile completion: {str(e)}"
        )


@router.patch("/{user_id}/security", response_model=dict)
async def update_security_settings(
    user_id: int,
    security_data: PasswordChangeForm,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user security settings (password change)
    Equivalent to: router.patch('/:id/security', auth, updateSecuritySettings);
    """
    # Verify user can update security settings
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update security settings for this user"
        )
    
    try:
        # Get the user
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate password change
        success = validate_password_change(
            db, 
            user, 
            security_data.current_password,
            security_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
        
        return {
            "success": True,
            "message": "Security settings updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security update failed: {str(e)}"
        )


@router.patch("/{user_id}/preferences", response_model=dict)
async def update_preferences(
    user_id: int,
    preferences_data: NotificationPreferencesForm,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences and notification settings
    Equivalent to: router.patch('/:id/preferences', auth, updatePreferences);
    """
    # Verify user can update preferences
    if user_id != current_user.id and current_user.user_role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update preferences for this user"
        )
    
    try:
        # Get the user
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update preferences in database
        preferences_dict = preferences_data.dict()
        preferences_dict['updated_at'] = datetime.now()
        
        updated_user = update_user_profile(db, user_id, preferences_dict)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preferences"
            )
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": preferences_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preferences update failed: {str(e)}"
        )


# ─── Additional User Management Routes ──────────────────────────────────────────
@router.get("/", response_model=List[UserPublicSerializer])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all users (admin only or public profiles)"""
    # For now, return public profiles for all users
    # You can add admin-only logic here if needed
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return [UserPublicSerializer.from_orm(user) for user in users]


@router.get("/{user_id}/settings", response_model=UserSettingsSerializer)
async def get_user_settings(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user settings and preferences"""
    if user_id != current_user.id and current_user.user_role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view settings for this user"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create settings response (you may need to adjust based on your user model)
    return UserSettingsSerializer(
        user_id=user.id,
        # Map your user model fields to settings fields
        language=getattr(user, 'language', 'en'),
        currency=getattr(user, 'currency', 'USD'),
        timezone=getattr(user, 'timezone', 'UTC'),
        updated_at=user.updated_at
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account (soft delete)"""
    # Only allow users to delete their own account or admin to delete any
    if user_id != current_user.id and current_user.user_role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this account"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Perform soft delete (update account_status instead of actual deletion)
    update_data = {
        "account_status": "inactive",
        "updated_at": datetime.now(),
        "is_verified": False
    }
    
    update_user_profile(db, user_id, update_data)
    
    return {
        "success": True,
        "message": "Account has been deactivated successfully"
    }

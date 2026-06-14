# ~/Documents/WealthTrackr/backend/schemas/user_serializers.py

from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ─── Enums for User Serialization ───────────────────────────────────────────────
class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserRole(str, Enum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    MODERATOR = "moderator"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# ─── Base User Serializer ───────────────────────────────────────────────────────
class UserBaseSerializer(BaseModel):
    """Base user serializer with essential fields"""
    id: int
    username: str
    email: EmailStr
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # For SQLAlchemy models
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }


# ─── Comprehensive User Serializer ──────────────────────────────────────────────
class UserDetailSerializer(UserBaseSerializer):
    """Comprehensive user serializer matching your JavaScript version"""
    
    # Basic Profile Info
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    
    # Profile Pictures
    profile_pic_url: Optional[HttpUrl] = None
    profile_picture_url: Optional[HttpUrl] = None  # Alternative field name
    
    # Contact & Personal Info
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    
    # Location & Preferences
    location: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    
    # Professional Info
    occupation: Optional[str] = None
    company: Optional[str] = None
    
    # Account Management
    account_status: Optional[AccountStatus] = AccountStatus.ACTIVE
    user_role: Optional[UserRole] = UserRole.USER
    
    # Gamification Fields
    level: Optional[int] = 1
    experience_points: Optional[int] = 0
    achievement_count: Optional[int] = 0
    badges: Optional[List[str]] = []
    streak_days: Optional[int] = 0
    
    @property
    def full_name(self) -> Optional[str]:
        """Computed field for full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.name

    @property
    def profile_completion_percentage(self) -> int:
        """Calculate profile completion percentage"""
        required_fields = [
            'first_name', 'last_name', 'bio', 'phone_number',
            'date_of_birth', 'location', 'occupation'
        ]
        
        completed_fields = sum(1 for field in required_fields 
                             if getattr(self, field, None) is not None)
        
        return int((completed_fields / len(required_fields)) * 100)


# ─── Public User Serializer ─────────────────────────────────────────────────────
class UserPublicSerializer(BaseModel):
    """Public user serializer for displaying to other users"""
    id: int
    username: str
    display_name: Optional[str] = None
    profile_pic_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    level: Optional[int] = 1
    achievement_count: Optional[int] = 0
    badges: Optional[List[str]] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ─── User List Serializer ───────────────────────────────────────────────────────
class UserListSerializer(BaseModel):
    """Minimal user serializer for lists"""
    id: int
    username: str
    name: Optional[str] = None
    email: EmailStr
    is_verified: bool
    account_status: Optional[AccountStatus] = AccountStatus.ACTIVE
    created_at: datetime

    class Config:
        from_attributes = True


# ─── User Profile Update Response ───────────────────────────────────────────────
class UserUpdateResponseSerializer(BaseModel):
    """Response serializer after user profile updates"""
    success: bool = True
    message: str
    user: UserDetailSerializer
    updated_fields: List[str]
    profile_completion_percentage: int
    missing_fields: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

    class Config:
        from_attributes = True


# ─── Authentication Response Serializers ────────────────────────────────────────
class UserAuthResponseSerializer(UserBaseSerializer):
    """User serializer for authentication responses"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    profile_pic_url: Optional[HttpUrl] = None
    user_role: Optional[UserRole] = UserRole.USER
    account_status: Optional[AccountStatus] = AccountStatus.ACTIVE


class LoginResponseSerializer(BaseModel):
    """Complete login response serializer"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserAuthResponseSerializer

    class Config:
        from_attributes = True


# ─── Profile Completion Analysis ────────────────────────────────────────────────
class ProfileCompletionSerializer(BaseModel):
    """Detailed profile completion analysis"""
    success: bool = True
    user_id: int
    profile_completion_percentage: int
    completed_fields: List[str]
    missing_fields: List[str]
    recommendations: List[str]
    next_steps: List[str]
    priority_fields: List[str]  # Most important missing fields
    
    class Config:
        from_attributes = True


# ─── User Settings Serializer ───────────────────────────────────────────────────
class UserSettingsSerializer(BaseModel):
    """User preferences and settings"""
    user_id: int
    
    # Privacy Settings
    profile_visibility: str = "public"  # public, friends, private
    show_email: bool = False
    show_phone: bool = False
    show_location: bool = True
    
    # Notification Settings
    email_notifications: bool = True
    push_notifications: bool = True
    budget_alerts: bool = True
    goal_reminders: bool = True
    weekly_summary: bool = True
    
    # App Preferences
    theme: str = "light"  # light, dark, auto
    language: str = "en"
    currency: str = "USD"
    timezone: str = "UTC"
    date_format: str = "MM/DD/YYYY"
    
    # Financial Preferences
    default_budget_period: str = "monthly"
    spending_categories_visible: bool = True
    investment_tracking: bool = False
    
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── User Statistics Serializer ─────────────────────────────────────────────────
class UserStatsSerializer(BaseModel):
    """User activity and financial statistics"""
    user_id: int
    
    # Activity Stats
    login_streak: int = 0
    total_logins: int = 0
    last_login: Optional[datetime] = None
    
    # Financial Stats
    total_expenses: int = 0
    total_income_records: int = 0
    active_budgets: int = 0
    completed_goals: int = 0
    
    # Engagement Stats
    profile_views: int = 0
    badges_earned: int = 0
    current_level: int = 1
    total_experience: int = 0
    
    # Time-based Stats
    days_since_signup: int = 0
    most_active_day: Optional[str] = None
    average_daily_expenses: float = 0.0
    
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Helper Functions for Serialization ─────────────────────────────────────────
def serialize_user_for_response(user_model, include_sensitive: bool = False) -> Dict[str, Any]:
    """
    Helper function to serialize user model to dictionary
    Similar to your JavaScript serializeUser function
    """
    if include_sensitive:
        return UserDetailSerializer.from_orm(user_model).dict()
    else:
        return UserPublicSerializer.from_orm(user_model).dict()


def serialize_user_list(users, include_stats: bool = False) -> List[Dict[str, Any]]:
    """Serialize a list of users"""
    if include_stats:
        return [UserListSerializer.from_orm(user).dict() for user in users]
    else:
        return [UserPublicSerializer.from_orm(user).dict() for user in users]


def calculate_profile_completion(user_model) -> ProfileCompletionSerializer:
    """Calculate and return profile completion analysis"""
    required_fields = [
        'first_name', 'last_name', 'bio', 'phone_number',
        'date_of_birth', 'location', 'occupation', 'company'
    ]
    
    completed_fields = []
    missing_fields = []
    
    for field in required_fields:
        value = getattr(user_model, field, None)
        if value is not None and str(value).strip():
            completed_fields.append(field)
        else:
            missing_fields.append(field)
    
    completion_percentage = int((len(completed_fields) / len(required_fields)) * 100)
    
    # Generate recommendations
    recommendations = []
    priority_fields = []
    
    if 'first_name' in missing_fields or 'last_name' in missing_fields:
        recommendations.append("Complete your full name for better personalization")
        priority_fields.extend(['first_name', 'last_name'])
    
    if 'bio' in missing_fields:
        recommendations.append("Add a bio to tell others about yourself")
        
    if 'phone_number' in missing_fields:
        recommendations.append("Add your phone number for account security")
        priority_fields.append('phone_number')
    
    if 'location' in missing_fields:
        recommendations.append("Add your location for localized features")
    
    # Next steps based on completion percentage
    next_steps = []
    if completion_percentage < 25:
        next_steps.append("Start by completing your basic information")
    elif completion_percentage < 50:
        next_steps.append("Add your contact information and preferences")
    elif completion_percentage < 75:
        next_steps.append("Complete your professional and personal details")
    else:
        next_steps.append("Your profile is nearly complete! Add the finishing touches")
    
    return ProfileCompletionSerializer(
        user_id=user_model.id,
        profile_completion_percentage=completion_percentage,
        completed_fields=completed_fields,
        missing_fields=missing_fields,
        recommendations=recommendations,
        next_steps=next_steps,
        priority_fields=priority_fields
    )


# ─── Error Response Serializers ─────────────────────────────────────────────────
class UserErrorSerializer(BaseModel):
    """Standard user-related error responses"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ─── Batch Operation Serializers ────────────────────────────────────────────────
class BulkUserUpdateSerializer(BaseModel):
    """Response for bulk user operations"""
    success: bool = True
    message: str
    updated_count: int
    failed_count: int
    updated_users: List[UserListSerializer]
    failed_updates: Optional[List[Dict[str, Any]]] = None


# ─── Export commonly used serializers ───────────────────────────────────────────
__all__ = [
    'UserDetailSerializer',
    'UserPublicSerializer',
    'UserListSerializer',
    'UserAuthResponseSerializer',
    'LoginResponseSerializer',
    'ProfileCompletionSerializer',
    'UserSettingsSerializer',
    'UserStatsSerializer',
    'serialize_user_for_response',
    'calculate_profile_completion'
]

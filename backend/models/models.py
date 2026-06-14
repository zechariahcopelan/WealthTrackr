# /home/kenneth-copeland/Documents/WealthTrackr/backend/models.py
import enum
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean, Text, 
    ForeignKey, JSON, Enum, UniqueConstraint, Index, CheckConstraint,
    DECIMAL, BigInteger, SmallInteger
)
from sqlalchemy.dialects.postgresql import INET, ARRAY
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

# Import Base from your existing database configuration
from backend.database import Base



# =====================================================
# ENUMS
# =====================================================

class AccountStatus(enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    LOCKED = "locked"

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPER_ADMIN = "super_admin"

class TwoFactorMethod(enum.Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"

class BiometricType(enum.Enum):
    FINGERPRINT = "fingerprint"
    FACE_ID = "face_id"
    IRIS = "iris"
    VOICE = "voice"

class RiskTolerance(enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"

class InvestmentExperience(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class SubscriptionPlan(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class BillingCycle(enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class DeviceType(enum.Enum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    DESKTOP = "desktop"

class OnboardingStep(enum.Enum):
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    FINANCIAL_GOALS = "financial_goals"
    PREFERENCES = "preferences"
    COMPLETE = "complete"

class SecurityLevel(enum.Enum):
    BASIC = "basic"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class RecurrenceType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

# =====================================================
# ENHANCED USER MODEL
# =====================================================

class User(Base):
    __tablename__ = "users"
    
    # =====================================================
    # PRIMARY IDENTIFICATION
    # =====================================================
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Original fields (maintained for compatibility)
    name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    profile_pic_url = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # =====================================================
    # ENHANCED PROFILE INFORMATION
    # =====================================================
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=True)
    phone_number = Column(String(20), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    age = Column(SmallInteger, nullable=True)
    gender = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    timezone = Column(String(50), nullable=True, default='UTC')
    language = Column(String(10), nullable=False, default='en')
    country = Column(String(100), nullable=True)
    currency = Column(String(10), nullable=False, default='USD')
    occupation = Column(String(200), nullable=True)
    company = Column(String(200), nullable=True)
    
    # =====================================================
    # ACCOUNT STATUS & SECURITY
    # =====================================================
    account_status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)
    user_role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    phone_verified = Column(Boolean, default=False, nullable=False)
    phone_verified_at = Column(DateTime, nullable=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_methods = Column(JSON, default=list, nullable=False)
    biometric_enabled = Column(Boolean, default=False, nullable=False)
    biometric_types = Column(JSON, default=list, nullable=False)
    pin_enabled = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(INET, nullable=True)
    last_login_device = Column(String(255), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    account_locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    security_questions_set = Column(Boolean, default=False, nullable=False)
    
    # =====================================================
    # FINANCIAL PROFILE
    # =====================================================
    monthly_income = Column(DECIMAL(12, 2), nullable=True)
    financial_goals = Column(JSON, default=list, nullable=False)
    risk_tolerance = Column(Enum(RiskTolerance), nullable=True)
    investment_experience = Column(Enum(InvestmentExperience), nullable=True)
    has_financial_advisor = Column(Boolean, default=False, nullable=False)
    credit_score = Column(SmallInteger, nullable=True)
    credit_score_updated_at = Column(DateTime, nullable=True)
    
    # =====================================================
    # SUBSCRIPTION & PLAN
    # =====================================================
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE, nullable=False)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    billing_cycle = Column(Enum(BillingCycle), nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)
    
    # =====================================================
    # SOCIAL & CONNECTIONS
    # =====================================================
    social_accounts = Column(JSON, default=list, nullable=False)
    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_count = Column(Integer, default=0, nullable=False)
    total_referral_rewards = Column(DECIMAL(10, 2), default=0.0, nullable=False)
    
    # =====================================================
    # GAMIFICATION & ENGAGEMENT
    # =====================================================
    level = Column(Integer, default=1, nullable=False)
    experience_points = Column(Integer, default=0, nullable=False)
    achievement_count = Column(Integer, default=0, nullable=False)
    badges = Column(JSON, default=list, nullable=False)
    streak_days = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(Date, nullable=True)
    
    # =====================================================
    # APP USAGE & ANALYTICS
    # =====================================================
    app_version = Column(String(20), nullable=True)
    device_type = Column(Enum(DeviceType), nullable=True)
    push_token = Column(String(500), nullable=True)
    sessions_count = Column(Integer, default=0, nullable=False)
    total_app_time_minutes = Column(BigInteger, default=0, nullable=False)
    average_session_time_minutes = Column(DECIMAL(8, 2), default=0.0, nullable=False)
    favorite_features = Column(JSON, default=list, nullable=False)
    
    # =====================================================
    # PREFERENCES & SETTINGS
    # =====================================================
    notification_preferences = Column(JSON, default=dict, nullable=False)
    privacy_settings = Column(JSON, default=dict, nullable=False)
    app_preferences = Column(JSON, default=dict, nullable=False)
    
    # =====================================================
    # METADATA & TIMESTAMPS
    # =====================================================
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete support
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_step = Column(Enum(OnboardingStep), nullable=True)
    onboarding_completed_at = Column(DateTime, nullable=True)
    terms_accepted_at = Column(DateTime, nullable=True)
    privacy_policy_accepted_at = Column(DateTime, nullable=True)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    data_processing_consent = Column(Boolean, default=False, nullable=False)
    
    # =====================================================
    # BACKUP & SYNC
    # =====================================================
    cloud_backup_enabled = Column(Boolean, default=True, nullable=False)
    last_backup_at = Column(DateTime, nullable=True)
    sync_enabled = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    data_version = Column(Integer, default=1, nullable=False)
    
    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    financial_goals_rel = relationship("FinancialGoal", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("UserAPIKey", back_populates="user", cascade="all, delete-orphan")
    
    # Self-referential relationship for referrals
    referrals = relationship("User", backref="referrer", remote_side=[id])
    
    # =====================================================
    # INDEXES AND CONSTRAINTS
    # =====================================================
    __table_args__ = (
        Index('idx_user_email_verified', 'email', 'is_verified'),
        Index('idx_user_status_role', 'account_status', 'user_role'),
        Index('idx_user_subscription', 'subscription_plan', 'subscription_status'),
        Index('idx_user_activity', 'last_activity_at'),
        Index('idx_user_created', 'created_at'),
        Index('idx_user_level_xp', 'level', 'experience_points'),
        Index('idx_user_referral', 'referral_code'),
        CheckConstraint('age >= 13 AND age <= 120', name='check_valid_age'),
        CheckConstraint('credit_score >= 300 AND credit_score <= 850', name='check_valid_credit_score'),
        CheckConstraint('level >= 1', name='check_positive_level'),
        CheckConstraint('experience_points >= 0', name='check_non_negative_xp'),
        CheckConstraint('failed_login_attempts >= 0', name='check_non_negative_failed_attempts'),
    )
    
    # =====================================================
    # VALIDATION
    # =====================================================
    @validates('email')
    def validate_email(self, key, email):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()
    
    @validates('phone_number')
    def validate_phone_number(self, key, phone_number):
        if phone_number and not phone_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Invalid phone number format')
        return phone_number
    
    @validates('currency')
    def validate_currency(self, key, currency):
        valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR']
        if currency not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return currency
    
    # =====================================================
    # COMPUTED PROPERTIES
    # =====================================================
    @hybrid_property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        elif self.display_name:
            return self.display_name
        elif self.name:
            return self.name
        else:
            return self.username
    
    @hybrid_property
    def ui_display_name(self):
        return self.display_name or self.full_name or self.name or self.username
    
    @hybrid_property
    def best_profile_picture_url(self):
        return self.profile_picture_url or self.profile_pic_url
    
    @hybrid_property
    def is_account_active(self):
        return (self.account_status == AccountStatus.ACTIVE and 
                self.is_verified and 
                self.deleted_at is None)
    
    @hybrid_property
    def is_deleted(self):
        return self.deleted_at is not None
    
    @hybrid_property
    def is_account_locked(self):
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False
    
    @hybrid_property
    def has_premium_features(self):
        return (self.subscription_plan in [SubscriptionPlan.PREMIUM, SubscriptionPlan.ENTERPRISE] and
                self.subscription_status == SubscriptionStatus.ACTIVE)
    
    @hybrid_property
    def is_on_trial(self):
        if self.subscription_status == SubscriptionStatus.TRIAL and self.trial_ends_at:
            return datetime.utcnow() < self.trial_ends_at
        return False
    
    @hybrid_property
    def needs_onboarding(self):
        return not self.onboarding_completed
    
    @property
    def security_level(self):
        score = 0
        if self.two_factor_enabled:
            score += 2
        if self.biometric_enabled:
            score += 2
        if self.pin_enabled:
            score += 1
        if self.security_questions_set:
            score += 1
        
        if score >= 5:
            return SecurityLevel.VERY_HIGH
        elif score >= 4:
            return SecurityLevel.HIGH
        elif score >= 2:
            return SecurityLevel.MEDIUM
        elif score >= 1:
            return SecurityLevel.LOW
        else:
            return SecurityLevel.BASIC
    
    @property
    def calculated_age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return self.age
    
    @property
    def is_profile_complete(self):
        required_fields = [
            self.first_name, self.last_name, self.date_of_birth,
            self.phone_number, self.bio, self.location
        ]
        return all(field is not None for field in required_fields)
    
    @property
    def profile_completion_percentage(self):
        fields = [
            self.first_name is not None,
            self.last_name is not None,
            self.date_of_birth is not None,
            self.phone_number is not None,
            self.bio is not None,
            self.location is not None,
            self.occupation is not None,
            self.best_profile_picture_url is not None
        ]
        return int((sum(fields) / len(fields)) * 100)
    
    @property
    def can_access_premium_features(self):
        return self.has_premium_features or self.is_on_trial
    
    @property
    def member_since_days(self):
        return (datetime.utcnow() - self.created_at).days
    
    @property
    def is_new_user(self):
        return self.member_since_days <= 7
    
    @property
    def subscription_days_remaining(self):
        if self.subscription_expires_at:
            remaining = (self.subscription_expires_at - datetime.utcnow()).days
            return max(0, remaining)
        return None
    
    @property
    def is_subscription_expiring_soon(self):
        remaining = self.subscription_days_remaining
        return remaining is not None and 1 <= remaining <= 7
    
    @property
    def is_on_streak(self):
        if self.streak_days > 0 and self.last_activity_date:
            days_since_activity = (date.today() - self.last_activity_date).days
            return days_since_activity <= 1
        return False
    
    @property
    def next_level_xp_required(self):
        return (self.level * 1000) - (self.experience_points % (self.level * 1000))
    
    @property
    def level_progress_percentage(self):
        current_level_xp = self.experience_points % (self.level * 1000)
        total_level_xp = self.level * 1000
        return int((current_level_xp / total_level_xp) * 100) if total_level_xp > 0 else 0
    
    # =====================================================
    # INSTANCE METHODS
    # =====================================================
    def get_initials(self):
        """Get user initials for avatar"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0].upper()}{self.last_name[0].upper()}"
        elif self.display_name and ' ' in self.display_name:
            parts = self.display_name.split(' ', 1)
            return f"{parts[0][0].upper()}{parts[1][0].upper()}"
        elif self.display_name:
            return self.display_name[:2].upper()
        elif ' ' in self.name:
            parts = self.name.split(' ', 1)
            return f"{parts[0][0].upper()}{parts[1][0].upper()}"
        elif self.name:
            return self.name[:2].upper()
        else:
            return self.username[:2].upper()
    
    def can_access_premium_feature(self, feature_name=None):
        """Check if user can access premium feature"""
        if self.can_access_premium_features:
            return True
        if feature_name and feature_name in self.favorite_features:
            return True
        if self.level >= 10:  # High-level users get some premium features
            return True
        return False
    
    def should_show_upgrade_prompt(self):
        """Check if user should see upgrade prompt"""
        if self.subscription_plan == SubscriptionPlan.FREE:
            return True
        if self.is_on_trial and (self.subscription_days_remaining or 0) <= 7:
            return True
        if self.is_subscription_expiring_soon:
            return True
        return False
    
    def update_activity(self):
        """Update user activity timestamp"""
        self.last_activity_at = datetime.utcnow()
        self.last_activity_date = date.today()
    
    def add_experience_points(self, points):
        """Add experience points and handle level up"""
        self.experience_points += points
        new_level = (self.experience_points // 1000) + 1
        if new_level > self.level:
            self.level = new_level
            return True  # Level up occurred
        return False
    
    def increment_streak(self):
        """Increment daily streak if valid"""
        today = date.today()
        if self.last_activity_date == today - timedelta(days=1):
            self.streak_days += 1
        elif self.last_activity_date != today:
            self.streak_days = 1
        self.last_activity_date = today
    
    def reset_failed_login_attempts(self):
        """Reset failed login attempts counter"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        from datetime import timedelta
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.account_status = AccountStatus.LOCKED
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


# =====================================================
# ENHANCED CATEGORY MODEL
# =====================================================

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon identifier
    color = Column(String(7), nullable=True)  # Hex color code
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System vs user-created
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Budget settings
    monthly_budget = Column(DECIMAL(10, 2), nullable=True)
    budget_warning_threshold = Column(DECIMAL(5, 2), default=80.0, nullable=False)  # Percentage
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    expenses = relationship("Expense", back_populates="category")
    transactions = relationship("Transaction", back_populates="category")
    creator = relationship("User", backref="created_categories")
    
    __table_args__ = (
        UniqueConstraint('name', 'parent_id', 'created_by', name='uq_category_name_parent_user'),
        Index('idx_category_active', 'is_active'),
        Index('idx_category_system', 'is_system'),
        Index('idx_category_parent', 'parent_id'),
    )
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


# =====================================================
# ENHANCED INCOME MODEL
# =====================================================

class Income(Base):
    __tablename__ = "incomes"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    date_received = Column(DateTime, nullable=False)
    
    # Enhanced fields
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_type = Column(Enum(RecurrenceType), nullable=True)
    recurrence_interval = Column(Integer, default=1, nullable=False)
    next_occurrence = Column(DateTime, nullable=True)
    
    # Tax information
    is_taxable = Column(Boolean, default=True, nullable=False)
    tax_category = Column(String(100), nullable=True)
    tax_withheld = Column(DECIMAL(10, 2), default=0.0, nullable=False)
    
    # Metadata
    tags = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="incomes")
    category = relationship("Category")
    
    __table_args__ = (
        Index('idx_income_user_date', 'user_id', 'date_received'),
        Index('idx_income_recurring', 'is_recurring', 'next_occurrence'),
        Index('idx_income_amount', 'amount'),
        CheckConstraint('amount > 0', name='check_positive_income_amount'),
        CheckConstraint('tax_withheld >= 0', name='check_non_negative_tax_withheld'),
    )
    
    def __repr__(self):
        return f"<Income(id={self.id}, source='{self.source}', amount={self.amount})>"


# =====================================================
# ENHANCED EXPENSE MODEL
# =====================================================

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(200), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Enhanced fields
    merchant = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_type = Column(Enum(RecurrenceType), nullable=True)
    recurrence_interval = Column(Integer, default=1, nullable=False)
    next_occurrence = Column(DateTime, nullable=True)
    
    # Business expense tracking
    is_business_expense = Column(Boolean, default=False, nullable=False)
    is_reimbursable = Column(Boolean, default=False, nullable=False)
    reimbursement_status = Column(String(50), default='not_applicable', nullable=False)
    receipt_url = Column(String(500), nullable=True)
    
    # Metadata
    tags = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign keys
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
    
    __table_args__ = (
        Index('idx_expense_user_date', 'user_id', 'date'),
        Index('idx_expense_category_date', 'category_id', 'date'),
        Index('idx_expense_recurring', 'is_recurring', 'next_occurrence'),
        Index('idx_expense_amount', 'amount'),
        Index('idx_expense_merchant', 'merchant'),
        CheckConstraint('amount > 0', name='check_positive_expense_amount'),
    )
    
    def __repr__(self):
        return f"<Expense(id={self.id}, description='{self.description}', amount={self.amount})>"


# =====================================================
# COMPREHENSIVE TRANSACTION MODEL
# =====================================================

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core transaction data
    description = Column(String(200), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.COMPLETED, nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Enhanced transaction details
    merchant = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    reference_number = Column(String(100), nullable=True)
    external_id = Column(String(100), nullable=True)  # For bank imports
    
    # Recurrence
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_type = Column(Enum(RecurrenceType), nullable=True)
    recurrence_interval = Column(Integer, default=1, nullable=False)
    next_occurrence = Column(DateTime, nullable=True)
    parent_transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=True)
    
    # Organization
    tags = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    is_flagged = Column(Boolean, default=False, nullable=False)
    has_attachments = Column(Boolean, default=False, nullable=False)
    
    # Business/Tax tracking
    is_business_expense = Column(Boolean, default=False, nullable=False)
    is_tax_deductible = Column(Boolean, default=False, nullable=False)
    tax_category = Column(String(100), nullable=True)
    
    # Transfer specific fields
    transfer_from_account = Column(String(100), nullable=True)
    transfer_to_account = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    parent_transaction = relationship("Transaction", remote_side=[id], backref="recurring_transactions")
    attachments = relationship("TransactionAttachment", back_populates="transaction", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_transaction_user_date', 'user_id', 'date'),
        Index('idx_transaction_type_status', 'type', 'status'),
        Index('idx_transaction_category_date', 'category_id', 'date'),
        Index('idx_transaction_recurring', 'is_recurring', 'next_occurrence'),
        Index('idx_transaction_amount', 'amount'),
        Index('idx_transaction_merchant', 'merchant'),
        Index('idx_transaction_reference', 'reference_number'),
        Index('idx_transaction_external', 'external_id'),
        CheckConstraint('amount > 0', name='check_positive_transaction_amount'),
    )
    
    @property
    def formatted_amount(self):
        """Get formatted amount with proper sign"""
        if self.type == TransactionType.INCOME:
            return f"+${self.amount:.2f}"
        elif self.type == TransactionType.EXPENSE:
            return f"-${self.amount:.2f}"
        else:  # TRANSFER
            return f"${self.amount:.2f}"
    
    @property
    def type_color(self):
        """Get color for transaction type"""
        color_map = {
            TransactionType.INCOME: "#4CAF50",
            TransactionType.EXPENSE: "#F44336",
            TransactionType.TRANSFER: "#2196F3"
        }
        return color_map.get(self.type, "#757575")
    
    @property
    def status_color(self):
        """Get color for transaction status"""
        color_map = {
            TransactionStatus.COMPLETED: "#4CAF50",
            TransactionStatus.PENDING: "#FF9800",
            TransactionStatus.CANCELLED: "#757575",
            TransactionStatus.FAILED: "#F44336"
        }
        return color_map.get(self.status, "#757575")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.type}, amount={self.amount})>"


# =====================================================
# SUPPORTING MODELS
# =====================================================

class TransactionAttachment(Base):
    __tablename__ = "transaction_attachments"
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    transaction = relationship("Transaction", back_populates="attachments")


class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    period = Column(String(20), default='monthly', nullable=False)  # monthly, weekly, yearly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    
    # Settings
    alert_threshold = Column(DECIMAL(5, 2), default=80.0, nullable=False)  # Percentage
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("Category")
    
    __table_args__ = (
        Index('idx_budget_user_period', 'user_id', 'period'),
        Index('idx_budget_category', 'category_id'),
        Index('idx_budget_active', 'is_active'),
        CheckConstraint('amount > 0', name='check_positive_budget_amount'),
        CheckConstraint('alert_threshold >= 0 AND alert_threshold <= 100', name='check_valid_threshold'),
    )


class FinancialGoal(Base):
    __tablename__ = "financial_goals"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(DECIMAL(12, 2), nullable=False)
    current_amount = Column(DECIMAL(12, 2), default=0.0, nullable=False)
    target_date = Column(Date, nullable=True)
    category = Column(String(100), nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    is_achieved = Column(Boolean, default=False, nullable=False)
    achieved_date = Column(Date, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="financial_goals_rel")
    
    __table_args__ = (
        Index('idx_goal_user_priority', 'user_id', 'priority'),
        Index('idx_goal_target_date', 'target_date'),
        Index('idx_goal_achieved', 'is_achieved'),
        CheckConstraint('target_amount > 0', name='check_positive_target_amount'),
        CheckConstraint('current_amount >= 0', name='check_non_negative_current_amount'),
        CheckConstraint('priority >= 1', name='check_positive_priority'),
    )
    
    @property
    def progress_percentage(self):
        """Calculate goal progress percentage"""
        if self.target_amount > 0:
            return min(100, (self.current_amount / self.target_amount) * 100)
        return 0
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(0, self.target_amount - self.current_amount)


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # alert, info, success, warning, error
    is_read = Column(Boolean, default=False, nullable=False)
    is_dismissed = Column(Boolean, default=False, nullable=False)
    
    # Action data
    action_url = Column(String(500), nullable=True)
    action_data = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
        Index('idx_notification_type', 'type'),
        Index('idx_notification_created', 'created_at'),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True)
    session_token = Column(String(255), unique=True, nullable=False)
    device_info = Column(JSON, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_activity = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_token', 'session_token'),
        Index('idx_session_expires', 'expires_at'),
    )


class UserAPIKey(Base):
    __tablename__ = "user_api_keys"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index('idx_api_key_user', 'user_id'),
        Index('idx_api_key_hash', 'key_hash'),
        Index('idx_api_key_active', 'is_active'),
    )

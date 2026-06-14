# ~/Documents/WealthTrackr/backend/schemas/forms.py

from pydantic import BaseModel, EmailStr, validator, Field, HttpUrl
from typing import Optional, List, Union
from datetime import datetime, date
from enum import Enum
import re
from decimal import Decimal


# ─── Enums for Validation ───────────────────────────────────────────────────────
class LanguageEnum(str, Enum):
    EN = "en"
    ES = "es" 
    FR = "fr"
    DE = "de"
    ZH = "zh"
    JA = "ja"


class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"


class PaymentMethodEnum(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"
    CHECK = "check"
    VENMO = "venmo"
    ZELLE = "zelle"
    OTHER = "other"


class FrequencyEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


# ─── Base Validation Mixins ─────────────────────────────────────────────────────
class TimestampMixin(BaseModel):
    """Mixin for automatic timestamp handling"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class ValidationMixin:
    """Common validation methods"""
    
    @classmethod
    def validate_phone_number(cls, v):
        if v is None:
            return v
        # Basic phone number validation (can be enhanced)
        phone_pattern = re.compile(r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$')
        if not phone_pattern.match(str(v).strip()):
            raise ValueError('Invalid phone number format')
        return str(v).strip()
    
    @classmethod
    def validate_positive_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @classmethod
    def validate_non_empty_string(cls, v, field_name="Field"):
        if v is not None and not str(v).strip():
            raise ValueError(f'{field_name} cannot be empty or just whitespace')
        return str(v).strip() if v is not None else v


# ─── User Profile Forms ─────────────────────────────────────────────────────────
class UserUpdateForm(BaseModel, ValidationMixin):
    """Comprehensive user profile update form"""
    
    # Basic Info
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    
    # Contact Info
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    
    # Profile Details
    profile_pic_url: Optional[HttpUrl] = None
    date_of_birth: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    occupation: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    
    # Preferences
    language: Optional[LanguageEnum] = LanguageEnum.EN
    currency: Optional[CurrencyEnum] = CurrencyEnum.USD
    timezone: Optional[str] = Field(None, max_length=50)
    
    # Financial Profile
    annual_income: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    financial_goals: Optional[str] = Field(None, max_length=500)
    risk_tolerance: Optional[str] = Field(None, regex="^(low|medium|high)$")
    
    @validator('name', 'first_name', 'last_name', 'location', 'occupation', 'company')
    def validate_string_fields(cls, v):
        return cls.validate_non_empty_string(v)
    
    @validator('bio')
    def validate_bio(cls, v):
        if v is not None:
            v = str(v).strip()
            if len(v) > 1000:
                raise ValueError('Bio must be 1000 characters or less')
        return v
    
    @validator('phone_number')
    def validate_phone(cls, v):
        return cls.validate_phone_number(v)
    
    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v is not None:
            if v > date.today():
                raise ValueError('Birth date cannot be in the future')
            if v < date(1900, 1, 1):
                raise ValueError('Birth date must be after 1900')
        return v
    
    @validator('annual_income')
    def validate_income(cls, v):
        return cls.validate_positive_amount(v) if v is not None else v


class UserBioUpdateForm(BaseModel, ValidationMixin):
    """Simplified form for updating just the bio"""
    bio: Optional[str] = Field(None, max_length=1000)
    
    @validator('bio')
    def validate_bio(cls, v):
        if v is not None:
            v = str(v).strip()
            if len(v) > 1000:
                raise ValueError('Bio must be 1000 characters or less')
        return v


# ─── Financial Forms ────────────────────────────────────────────────────────────
class IncomeCreateForm(BaseModel, ValidationMixin, TimestampMixin):
    """Form for creating income records"""
    source: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    date_received: Optional[datetime] = Field(default_factory=datetime.now)
    description: Optional[str] = Field(None, max_length=500)
    is_recurring: bool = False
    frequency: Optional[FrequencyEnum] = None
    
    @validator('source')
    def validate_source(cls, v):
        return cls.validate_non_empty_string(v, "Income source")
    
    @validator('amount')
    def validate_amount(cls, v):
        return cls.validate_positive_amount(v)
    
    @validator('frequency')
    def validate_frequency_with_recurring(cls, v, values):
        if values.get('is_recurring') and v is None:
            raise ValueError('Frequency is required for recurring income')
        return v


class ExpenseCreateForm(BaseModel, ValidationMixin, TimestampMixin):
    """Enhanced form for creating expenses"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    date: datetime = Field(default_factory=datetime.now)
    category_id: int = Field(..., gt=0)
    
    # Enhanced expense fields
    is_recurring: bool = False
    frequency: Optional[FrequencyEnum] = None
    payment_method: Optional[PaymentMethodEnum] = None
    notes: Optional[str] = Field(None, max_length=1000)
    receipt_url: Optional[HttpUrl] = None
    is_tax_deductible: bool = False
    tags: Optional[List[str]] = Field(None, max_items=10)
    
    @validator('name')
    def validate_name(cls, v):
        return cls.validate_non_empty_string(v, "Expense name")
    
    @validator('amount')
    def validate_amount(cls, v):
        return cls.validate_positive_amount(v)
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            # Clean and validate tags
            cleaned_tags = []
            for tag in v:
                tag = str(tag).strip().lower()
                if tag and len(tag) <= 50:
                    cleaned_tags.append(tag)
            return cleaned_tags[:10]  # Limit to 10 tags
        return v
    
    @validator('frequency')
    def validate_frequency_with_recurring(cls, v, values):
        if values.get('is_recurring') and v is None:
            raise ValueError('Frequency is required for recurring expenses')
        return v


class CategoryCreateForm(BaseModel, ValidationMixin):
    """Form for creating expense categories"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    budget_limit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        return cls.validate_non_empty_string(v, "Category name")


# ─── Financial Goal Forms ───────────────────────────────────────────────────────
class FinancialGoalCreateForm(BaseModel, ValidationMixin, TimestampMixin):
    """Form for creating financial goals"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    target_amount: Decimal = Field(..., gt=0, decimal_places=2)
    current_amount: Optional[Decimal] = Field(0, ge=0, decimal_places=2)
    target_date: Optional[date] = None
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = Field("medium", regex="^(low|medium|high|critical)$")
    is_active: bool = True
    
    @validator('title')
    def validate_title(cls, v):
        return cls.validate_non_empty_string(v, "Goal title")
    
    @validator('target_amount', 'current_amount')
    def validate_amounts(cls, v):
        return cls.validate_positive_amount(v) if v is not None else v
    
    @validator('target_date')
    def validate_target_date(cls, v):
        if v is not None and v <= date.today():
            raise ValueError('Target date must be in the future')
        return v
    
    @validator('current_amount')
    def validate_current_vs_target(cls, v, values):
        target = values.get('target_amount')
        if v is not None and target is not None and v > target:
            raise ValueError('Current amount cannot exceed target amount')
        return v


# ─── Budget Forms ───────────────────────────────────────────────────────────────
class BudgetCreateForm(BaseModel, ValidationMixin, TimestampMixin):
    """Form for creating budgets"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    total_budget: Decimal = Field(..., gt=0, decimal_places=2)
    period: str = Field(..., regex="^(weekly|monthly|quarterly|yearly)$")
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        return cls.validate_non_empty_string(v, "Budget name")
    
    @validator('total_budget')
    def validate_budget(cls, v):
        return cls.validate_positive_amount(v)
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        start_date = values.get('start_date')
        if v is not None and start_date is not None and v <= start_date:
            raise ValueError('End date must be after start date')
        return v


# ─── Investment Forms ───────────────────────────────────────────────────────────
class InvestmentCreateForm(BaseModel, ValidationMixin, TimestampMixin):
    """Form for creating investment records"""
    symbol: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=200)
    investment_type: str = Field(..., regex="^(stock|bond|etf|mutual_fund|crypto|real_estate|other)$")
    shares: Optional[Decimal] = Field(None, gt=0, decimal_places=8)
    purchase_price: Decimal = Field(..., gt=0, decimal_places=2)
    purchase_date: date = Field(default_factory=date.today)
    current_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return str(v).strip().upper()
    
    @validator('name')
    def validate_name(cls, v):
        return cls.validate_non_empty_string(v, "Investment name")
    
    @validator('purchase_price', 'current_price')
    def validate_prices(cls, v):
        return cls.validate_positive_amount(v) if v is not None else v


# ─── Search and Filter Forms ────────────────────────────────────────────────────
class ExpenseSearchForm(BaseModel):
    """Form for searching and filtering expenses"""
    query: Optional[str] = Field(None, max_length=200)
    category_ids: Optional[List[int]] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    payment_methods: Optional[List[PaymentMethodEnum]] = None
    is_recurring: Optional[bool] = None
    tags: Optional[List[str]] = None
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        min_amount = values.get('min_amount')
        if v is not None and min_amount is not None and v <= min_amount:
            raise ValueError('Maximum amount must be greater than minimum amount')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if v is not None and start_date is not None and v <= start_date:
            raise ValueError('End date must be after start date')
        return v


class IncomeSearchForm(BaseModel):
    """Form for searching and filtering income"""
    query: Optional[str] = Field(None, max_length=200)
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    frequency: Optional[FrequencyEnum] = None


# ─── Notification Forms ─────────────────────────────────────────────────────────
class NotificationPreferencesForm(BaseModel):
    """Form for updating notification preferences"""
    email_notifications: bool = True
    push_notifications: bool = True
    budget_alerts: bool = True
    goal_reminders: bool = True
    spending_alerts: bool = True
    weekly_summary: bool = True
    monthly_report: bool = True
    investment_updates: bool = False
    
    # Notification thresholds
    daily_spending_threshold: Optional[Decimal] = Field(None, ge=0)
    budget_warning_threshold: Optional[int] = Field(80, ge=50, le=100)  # Percentage


# ─── AI Insight Forms ───────────────────────────────────────────────────────────
class AIAnalysisRequestForm(BaseModel):
    """Form for requesting AI financial analysis"""
    analysis_type: str = Field(..., regex="^(spending|budget|investment|goal|comprehensive)$")
    time_period: Optional[str] = Field("month", regex="^(week|month|quarter|year|all)$")
    include_projections: bool = False
    include_recommendations: bool = True
    focus_areas: Optional[List[str]] = Field(None, max_items=5)
    
    @validator('focus_areas')
    def validate_focus_areas(cls, v):
        if v is not None:
            valid_areas = ['spending', 'saving', 'budgeting', 'investments', 'debt', 'goals']
            return [area for area in v if area in valid_areas]
        return v


# ─── Response Validation Models ─────────────────────────────────────────────────
class ValidationErrorResponse(BaseModel):
    """Standard validation error response"""
    success: bool = False
    message: str
    errors: List[dict]
    field_errors: Optional[dict] = None


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ProfileCompletionResponse(BaseModel):
    """Response for profile completion analysis"""
    success: bool = True
    user_id: int
    profile_completion_percentage: int
    missing_fields: List[str]
    recommendations: List[str]
    next_steps: Optional[List[str]] = None


# ─── Custom Validators ──────────────────────────────────────────────────────────
def validate_password_strength(password: str) -> str:
    """Enhanced password validation"""
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long')
    
    if not re.search(r'[A-Z]', password):
        raise ValueError('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', password):
        raise ValueError('Password must contain at least one lowercase letter')
    
    if not re.search(r'\d', password):
        raise ValueError('Password must contain at least one digit')
    
    if not re.search(r'[!@#$%^&*()_+=\-\[\]{}|;:,.<>?]', password):
        raise ValueError('Password must contain at least one special character')
    
    return password


class PasswordChangeForm(BaseModel):
    """Form for changing user password"""
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        return validate_password_strength(v)
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        if v != values.get('new_password'):
            raise ValueError('Passwords do not match')
        return v


# ─── Batch Operation Forms ──────────────────────────────────────────────────────
class BatchExpenseCreateForm(BaseModel):
    """Form for creating multiple expenses at once"""
    expenses: List[ExpenseCreateForm] = Field(..., max_items=50)
    
    @validator('expenses')
    def validate_expenses_list(cls, v):
        if len(v) == 0:
            raise ValueError('At least one expense is required')
        return v


class BatchIncomeCreateForm(BaseModel):
    """Form for creating multiple income records at once"""
    incomes: List[IncomeCreateForm] = Field(..., max_items=50)
    
    @validator('incomes')
    def validate_incomes_list(cls, v):
        if len(v) == 0:
            raise ValueError('At least one income record is required')
        return v

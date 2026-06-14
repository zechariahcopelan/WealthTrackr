# /home/kenneth-copeland/Documents/WealthTrackr/backend/config.py

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """
    Application configuration using Pydantic settings.
    Automatically loads from environment variables and .env file.
    """
    
    # =====================================================
    # APPLICATION SETTINGS
    # =====================================================
    app_name: str = "WealthTrackr API"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production
    
    # =====================================================
    # DATABASE SETTINGS
    # =====================================================
    database_url: str = "postgresql://zack:newsecurepassword@localhost:5432/wealthtrackr"
    database_echo: bool = False  # Set to True for SQL query logging
    
    # Connection pool settings
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # =====================================================
    # SECURITY SETTINGS
    # =====================================================
    secret_key: str = "dev-key-change-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    
    # Password requirements
    min_password_length: int = 8
    require_password_complexity: bool = True
    
    # Account lockout settings
    max_failed_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    
    # =====================================================
    # EMAIL SETTINGS
    # =====================================================
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_use_tls: bool = True
    email_user: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    email_from_name: str = "WealthTrackr"
    
    # Email verification settings
    email_verification_expire_hours: int = 24
    password_reset_expire_hours: int = 2
    
    # =====================================================
    # AI & EXTERNAL API SETTINGS
    # =====================================================
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.7
    
    # Financial data APIs (for market data, etc.)
    alpha_vantage_api_key: Optional[str] = None
    polygon_api_key: Optional[str] = None
    
    # =====================================================
    # CORS SETTINGS
    # =====================================================
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # =====================================================
    # FILE UPLOAD SETTINGS
    # =====================================================
    max_file_size_mb: int = 10
    allowed_file_types: list = [".jpg", ".jpeg", ".png", ".pdf", ".csv", ".xlsx"]
    upload_directory: str = "uploads"
    
    # =====================================================
    # REDIS SETTINGS (for caching and background tasks)
    # =====================================================
    redis_url: str = "redis://localhost:6379/0"
    redis_expire_seconds: int = 3600
    
    # =====================================================
    # LOGGING SETTINGS
    # =====================================================
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # =====================================================
    # FEATURE FLAGS
    # =====================================================
    enable_ai_features: bool = True
    enable_email_verification: bool = True
    enable_two_factor_auth: bool = True
    enable_biometric_auth: bool = True
    enable_social_login: bool = False
    enable_premium_features: bool = True
    enable_analytics: bool = True
    enable_background_tasks: bool = True
    
    # =====================================================
    # RATE LIMITING
    # =====================================================
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 200
    
    # =====================================================
    # MONITORING & HEALTH CHECKS
    # =====================================================
    health_check_interval_seconds: int = 30
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # =====================================================
    # VALIDATORS
    # =====================================================
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('Database URL must be a PostgreSQL connection string')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {", ".join(allowed_envs)}')
        return v
    
    @validator('cors_origins', pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {", ".join(allowed_levels)}')
        return v.upper()
    
    # =====================================================
    # COMPUTED PROPERTIES
    # =====================================================
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy 2.0"""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return all([self.smtp_server, self.email_user, self.email_password])
    
    @property
    def ai_configured(self) -> bool:
        """Check if AI features are properly configured"""
        return self.openai_api_key is not None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow environment variables to override settings
        # For example: WEALTHTRACKR_DATABASE_URL=postgresql://...
        env_prefix = "WEALTHTRACKR_"


# =====================================================
# GLOBAL SETTINGS INSTANCE
# =====================================================
settings = Settings()


# =====================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# =====================================================
class DevelopmentSettings(Settings):
    """Development-specific settings"""
    debug: bool = True
    database_echo: bool = True
    log_level: str = "DEBUG"
    
    class Config(Settings.Config):
        env_file = ".env.development"


class ProductionSettings(Settings):
    """Production-specific settings"""
    debug: bool = False
    database_echo: bool = False
    log_level: str = "INFO"
    
    # Enhanced security for production
    min_password_length: int = 12
    require_password_complexity: bool = True
    access_token_expire_minutes: int = 30
    
    class Config(Settings.Config):
        env_file = ".env.production"


class TestingSettings(Settings):
    """Testing-specific settings"""
    debug: bool = True
    database_url: str = "postgresql://zack:newsecurepassword@localhost:5432/wealthtrackr_test"
    
    # Disable external services during testing
    enable_email_verification: bool = False
    enable_ai_features: bool = False
    
    class Config(Settings.Config):
        env_file = ".env.testing"


# =====================================================
# SETTINGS FACTORY
# =====================================================
def get_settings() -> Settings:
    """
    Factory function to get the appropriate settings based on environment.
    """
    env = os.getenv("WEALTHTRACKR_ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# =====================================================
# CONVENIENCE FUNCTIONS
# =====================================================
def get_database_url() -> str:
    """Get the database URL for the current environment"""
    return get_settings().database_url


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a specific feature is enabled"""
    settings_instance = get_settings()
    return getattr(settings_instance, f"enable_{feature_name}", False)

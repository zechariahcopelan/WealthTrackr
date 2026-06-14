# /home/kenneth-copeland/Documents/WealthTrackr/backend/database.py

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

# Import configuration
try:
    from backend.config import get_settings
    settings = get_settings()
    SQLALCHEMY_DATABASE_URL = settings.database_url
    DATABASE_ECHO = settings.database_echo
    POOL_SIZE = settings.database_pool_size
    MAX_OVERFLOW = settings.database_max_overflow
    POOL_TIMEOUT = settings.database_pool_timeout
    POOL_RECYCLE = settings.database_pool_recycle
except ImportError:
    # Fallback to original configuration if config.py doesn't exist
    logging.warning("Config file not found, using fallback database configuration")
    SQLALCHEMY_DATABASE_URL = "postgresql://zack:newsecurepassword@localhost:5432/wealthtrackr"
    DATABASE_ECHO = False
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600

# ─── Enhanced Engine Setup ──────────────────────────────────────────────────
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=DATABASE_ECHO,  # Set to True for SQL query logging
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    connect_args={
        "options": "-csearch_path=public",
        # Additional PostgreSQL-specific optimizations
        "application_name": "WealthTrackr_API",
        "connect_timeout": 10,
    }
)

# ─── Connection Event Listeners ────────────────────────────────────────────
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure database connection on connect"""
    if "postgresql" in str(dbapi_connection):
        # PostgreSQL-specific optimizations
        with dbapi_connection.cursor() as cursor:
            # Set timezone to UTC for consistency
            cursor.execute("SET timezone TO 'UTC'")
            # Optimize for read-heavy workloads
            cursor.execute("SET default_statistics_target = 100")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when connections are checked out (useful for debugging)"""
    if DATABASE_ECHO:
        logging.debug(f"Connection checked out: {id(dbapi_connection)}")

# ─── Base Model for All ORM Tables ──────────────────────────────────────────
Base = declarative_base()

# ─── Session Factory ────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent SQLAlchemy from expiring objects after commit
)

# ─── DB Dependency (for FastAPI routes) ─────────────────────────────────────
def get_db():
    """
    Database dependency for FastAPI routes.
    Automatically handles session lifecycle and cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logging.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()

# ─── Database Health Check ──────────────────────────────────────────────────
def check_database_health() -> bool:
    """
    Check if the database is accessible and responsive.
    Used for health check endpoints.
    """
    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logging.error(f"Database health check failed: {str(e)}")
        return False

# ─── Database Initialization ────────────────────────────────────────────────
def init_db():
    """
    Initialize database with all tables.
    This will be called from main.py on startup.
    """
    try:
        # Import all models to ensure they're registered with Base
        from backend.models.models import (
            User, Category, Income, Expense, Transaction,
            Budget, FinancialGoal, Notification, UserSession, UserAPIKey,
            TransactionAttachment
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Database tables created successfully")
        
        # Optionally seed initial data
        seed_initial_data()
        
    except Exception as e:
        logging.error(f"❌ Failed to initialize database: {str(e)}")
        raise

def seed_initial_data():
    """
    Seed the database with initial data (categories, etc.)
    """
    try:
        db = SessionLocal()
        
        # Import models
        from backend.models import Category
        
        # Check if categories already exist
        existing_categories = db.query(Category).filter(Category.is_system == True).count()
        
        if existing_categories == 0:
            # Create default system categories
            default_categories = [
                # Income categories
                {"name": "Salary", "icon": "💰", "color": "#4CAF50", "is_system": True},
                {"name": "Freelance", "icon": "💼", "color": "#2196F3", "is_system": True},
                {"name": "Investment Income", "icon": "📈", "color": "#9C27B0", "is_system": True},
                {"name": "Other Income", "icon": "💵", "color": "#607D8B", "is_system": True},
                
                # Expense categories
                {"name": "Food & Dining", "icon": "🍽️", "color": "#FF5722", "is_system": True},
                {"name": "Transportation", "icon": "🚗", "color": "#FF9800", "is_system": True},
                {"name": "Shopping", "icon": "🛒", "color": "#E91E63", "is_system": True},
                {"name": "Entertainment", "icon": "🎬", "color": "#9C27B0", "is_system": True},
                {"name": "Bills & Utilities", "icon": "📋", "color": "#795548", "is_system": True},
                {"name": "Healthcare", "icon": "🏥", "color": "#00BCD4", "is_system": True},
                {"name": "Education", "icon": "📚", "color": "#3F51B5", "is_system": True},
                {"name": "Travel", "icon": "✈️", "color": "#009688", "is_system": True},
                {"name": "Home & Garden", "icon": "🏠", "color": "#8BC34A", "is_system": True},
                {"name": "Personal Care", "icon": "💄", "color": "#E91E63", "is_system": True},
                {"name": "Gifts & Donations", "icon": "🎁", "color": "#FF5722", "is_system": True},
                {"name": "Other Expenses", "icon": "📦", "color": "#757575", "is_system": True},
            ]
            
            for cat_data in default_categories:
                category = Category(**cat_data)
                db.add(category)
            
            db.commit()
            logging.info(f"✅ Seeded {len(default_categories)} default categories")
        
        db.close()
        
    except Exception as e:
        logging.error(f"❌ Failed to seed initial data: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()

# ─── Import Models to Register Tables ───────────────────────────────────────
# Import the new comprehensive models instead of the separate files
try:
    # Try to import from the new comprehensive models file
    from backend.models import User, Category, Income, Expense, Transaction
    logging.info("✅ Using comprehensive models from backend.models")
except ImportError:
    # Fallback to individual model files if they still exist
    try:
        from backend.models.models_user import User
        from backend.models.models_income import Income
        from backend.models.models_expense import Expense
        from backend.models.models_category import Category
        logging.info("✅ Using individual model files (legacy mode)")
    except ImportError as e:
        logging.warning(f"⚠️ Could not import models: {str(e)}")
        logging.warning("Make sure to replace individual model files with the comprehensive models.py")

# ─── Connection Pool Monitoring ────────────────────────────────────────────
def get_db_pool_status():
    """
    Get current database connection pool status.
    Useful for monitoring and debugging.
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }

# ─── Async Database Support (for future use) ────────────────────────────────
"""
Uncomment this section if you want to add async database support in the future:

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Async engine for high-performance operations
async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=DATABASE_ECHO,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
"""

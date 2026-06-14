# /home/kenneth-copeland/Documents/WealthTrackr/backend/main.py

import os
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import hashlib
import jwt

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from dotenv import load_dotenv

# Pydantic models
from pydantic import BaseModel, EmailStr

# SQLAlchemy
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

# ─── Load Environment Variables ─────────────────────────────────────────────
load_dotenv()  # Load from .env file

# ─── Import Configuration ───────────────────────────────────────────────────
try:
    from backend.config import get_settings
    settings = get_settings()
except ImportError:
    # Fallback configuration if config.py doesn't exist
    logging.warning("Configuration file not found, using environment variables")
    
    class FallbackSettings:
        app_name = "WealthTrackr AI-Powered Financial API"
        app_version = "2.0.0"
        debug = True
        environment = "development"
        log_level = "INFO"
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_file = None
        cors_origins = ["http://localhost:3000", "http://localhost:8080", "http://10.0.2.2:8000"]
        cors_allow_credentials = True
        cors_allow_methods = ["*"]
        cors_allow_headers = ["*"]
        enable_ai_features = True
        ai_configured = bool(os.getenv("OPENAI_API_KEY"))
        enable_email_verification = False
        enable_two_factor_auth = False
        enable_premium_features = False
        database_echo = False
        database_pool_size = 5
        database_url = os.getenv("DATABASE_URL", "sqlite:///./wealthtrackr.db")
    
    settings = FallbackSettings()

# ─── Database Setup ──────────────────────────────────────────────────────────
DATABASE_URL = getattr(settings, 'database_url', "sqlite:///./wealthtrackr.db")
engine = create_engine(DATABASE_URL, echo=getattr(settings, 'database_echo', False))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─── Security Configuration ─────────────────────────────────────────────────
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ─── Database Models ────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class FinancialProfile(Base):
    __tablename__ = "financial_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    risk_tolerance = Column(String)  # conservative, moderate, aggressive
    investment_goals = Column(String)
    annual_income = Column(Float, nullable=True)
    net_worth = Column(Float, nullable=True)
    investment_experience = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String, index=True)
    price = Column(Float)
    change_percent = Column(Float)
    timestamp = Column(DateTime, default=func.now())

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    name = Column(String)
    color = Column(String, default="#3B82F6")
    icon = Column(String, default="📊")
    created_at = Column(DateTime, default=func.now())

class Income(Base):
    __tablename__ = "incomes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    amount = Column(Float)
    description = Column(String)
    source = Column(String)
    date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    amount = Column(Float)
    description = Column(String)
    category_id = Column(String)
    date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

# ─── Pydantic Models ────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_verified: bool

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class RegisterResponse(BaseModel):
    success: bool
    message: str
    user_id: str

class FinancialProfileRequest(BaseModel):
    risk_tolerance: str
    investment_goals: str
    annual_income: Optional[float] = None
    net_worth: Optional[float] = None
    investment_experience: Optional[str] = None

class FinancialProfileResponse(BaseModel):
    risk_tolerance: str
    investment_goals: str
    annual_income: Optional[float]
    net_worth: Optional[float]
    investment_experience: Optional[str]

class MarketInsightsResponse(BaseModel):
    spy_price: float
    trend: str
    change_percent: float
    timestamp: datetime

class AIAdviceRequest(BaseModel):
    query: str
    user_profile: Optional[str] = None

class AIAdviceResponse(BaseModel):
    advice: str
    confidence: float
    timestamp: datetime

# ─── Database Functions ─────────────────────────────────────────────────────
def init_db():
    """Initialize database and create tables"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def check_database_health():
    """Check database connection health"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False

def get_db_pool_status():
    """Get database pool status"""
    try:
        return {
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalidated()
        }
    except Exception:
        return {"status": "unavailable"}

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── Utility Functions ──────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# ─── Enhanced Logger Setup ──────────────────────────────────────────────────
def setup_logging():
    """Configure application logging"""
    log_level = getattr(settings, 'log_level', 'INFO')
    log_format = getattr(settings, 'log_format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(settings.log_file)] if hasattr(settings, 'log_file') and settings.log_file else [])
        ]
    )
    
    logger = logging.getLogger("wealthtrackr")
    logger.setLevel(getattr(logging, log_level))
    return logger

logger = setup_logging()

# ─── App Initialization ─────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """Application factory"""
    
    app_name = getattr(settings, 'app_name', 'WealthTrackr AI-Powered Financial API')
    app_version = getattr(settings, 'app_version', '2.0.0')
    debug_mode = getattr(settings, 'debug', False)
    
    app = FastAPI(
        title=app_name,
        description="Advanced personal finance tracking with AI insights, investment recommendations, and smart financial analysis.",
        version=app_version,
        debug=debug_mode,
        docs_url="/docs" if debug_mode else None,
        redoc_url="/redoc" if debug_mode else None,
    )
    
    return app

app = create_app()

# ─── Security Middleware ────────────────────────────────────────────────────
if hasattr(settings, 'debug') and not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )

# ─── Enhanced Logging Middleware ────────────────────────────────────────────
class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        import time
        start_time = time.time()
        
        logger.info(f"🔍 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'Unknown'}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(f"✅ {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
            raise

app.add_middleware(EnhancedLoggingMiddleware)

# ─── CORS Configuration ────────────────────────────────────────────────────
cors_origins = getattr(settings, 'cors_origins', ["http://localhost:3000", "http://localhost:8080", "http://10.0.2.2:8000"])
cors_credentials = getattr(settings, 'cors_allow_credentials', True)
cors_methods = getattr(settings, 'cors_allow_methods', ["*"])
cors_headers = getattr(settings, 'cors_allow_headers', ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

# ─── Global Exception Handler ───────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)} - Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )

# ─── Core Authentication Endpoints ─────────────────────────────────────────
@app.post("/auth/register", response_model=RegisterResponse, tags=["Authentication"])
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already registered")
    
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        is_verified=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return RegisterResponse(
        success=True,
        message="Account created successfully!",
        user_id=user.id
    )

@app.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_verified=user.is_verified
        )
    )

@app.post("/auth/logout", tags=["Authentication"])
def logout_user(current_user: User = Depends(verify_token)):
    return {"message": "Successfully logged out"}

@app.get("/auth/profile", response_model=UserResponse, tags=["Authentication"])
def get_user_profile(current_user: User = Depends(verify_token)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_verified=current_user.is_verified
    )

# ─── Financial Profile Endpoints ───────────────────────────────────────────
@app.post("/profile/financial", tags=["Financial Profile"])
def create_financial_profile(
    request: FinancialProfileRequest,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    existing_profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        db.delete(existing_profile)
    
    profile = FinancialProfile(
        user_id=current_user.id,
        risk_tolerance=request.risk_tolerance,
        investment_goals=request.investment_goals,
        annual_income=request.annual_income,
        net_worth=request.net_worth,
        investment_experience=request.investment_experience
    )
    
    db.add(profile)
    db.commit()
    
    return {"message": "Financial profile created successfully"}

@app.get("/profile/financial", response_model=FinancialProfileResponse, tags=["Financial Profile"])
def get_financial_profile(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        return FinancialProfileResponse(
            risk_tolerance="moderate",
            investment_goals="Long-term growth",
            annual_income=None,
            net_worth=None,
            investment_experience="Beginner"
        )
    
    return FinancialProfileResponse(
        risk_tolerance=profile.risk_tolerance,
        investment_goals=profile.investment_goals,
        annual_income=profile.annual_income,
        net_worth=profile.net_worth,
        investment_experience=profile.investment_experience
    )

# ─── Market Data Endpoints ──────────────────────────────────────────────────
@app.get("/market/insights", response_model=MarketInsightsResponse, tags=["Market Data"])
def get_market_insights(current_user: User = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        import yfinance as yf
        spy = yf.Ticker("SPY")
        hist = spy.history(period="2d")
        
        if len(hist) >= 2:
            current_price = float(hist['Close'].iloc[-1])
            previous_price = float(hist['Close'].iloc[-2])
            change_percent = ((current_price - previous_price) / previous_price) * 100
            trend = "bullish" if change_percent > 0 else "bearish" if change_percent < 0 else "neutral"
        else:
            current_price = 450.0
            change_percent = 0.5
            trend = "bullish"
        
        market_data = MarketData(
            symbol="SPY",
            price=current_price,
            change_percent=change_percent
        )
        db.add(market_data)
        db.commit()
        
        return MarketInsightsResponse(
            spy_price=current_price,
            trend=trend,
            change_percent=change_percent,
            timestamp=datetime.utcnow()
        )
    except Exception:
        return MarketInsightsResponse(
            spy_price=450.0,
            trend="neutral",
            change_percent=0.0,
            timestamp=datetime.utcnow()
        )

# ─── AI Advisor Endpoints ───────────────────────────────────────────────────
@app.post("/ai/advice", response_model=AIAdviceResponse, tags=["AI Financial Advisor"])
def get_ai_advice(
    request: AIAdviceRequest,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        profile = db.query(FinancialProfile).filter(
            FinancialProfile.user_id == current_user.id
        ).first()
        
        profile_context = ""
        if profile:
            profile_context = f"""
            User Profile:
            - Risk Tolerance: {profile.risk_tolerance}
            - Investment Goals: {profile.investment_goals}
            - Experience Level: {profile.investment_experience or 'Not specified'}
            """
        
        # Try OpenAI if available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            import openai
            openai.api_key = openai_key
            
            prompt = f"""
            You are a professional financial advisor AI. Provide helpful, personalized financial advice.
            
            {profile_context}
            
            User Question: {request.query}
            
            Please provide clear, actionable financial advice. Keep responses concise but informative.
            Include relevant disclaimers about not being personalized financial advice.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            advice = response.choices[0].message.content
            confidence = 0.85
        else:
            # Fallback advice
            advice = f"""
            Based on your query about {request.query}, here are some general financial considerations:
            
            1. Always diversify your investments across different asset classes
            2. Consider your risk tolerance and investment timeline
            3. Regular contributions to retirement accounts can provide tax advantages
            4. Emergency funds are crucial for financial stability
            5. Consider consulting with a qualified financial advisor for personalized advice
            
            Please note: This is general information and not personalized financial advice.
            """
            confidence = 0.7
        
        return AIAdviceResponse(
            advice=advice,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )
    
    except Exception:
        return AIAdviceResponse(
            advice="I apologize, but I'm currently unable to provide personalized advice. Please try again later or consult with a qualified financial advisor.",
            confidence=0.0,
            timestamp=datetime.utcnow()
        )

# ─── Startup Events ─────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    try:
        logger.info("🚀 Starting WealthTrackr API...")
        
        # Initialize database
        if init_db():
            logger.info("✅ Database initialized successfully")
        else:
            logger.error("❌ Database initialization failed")
            
        # Check database health
        if check_database_health():
            logger.info("✅ Database health check passed")
        else:
            logger.error("❌ Database health check failed")
            
        # Log configuration
        logger.info(f"🔧 Environment: {getattr(settings, 'environment', 'development')}")
        logger.info(f"🔧 Debug mode: {getattr(settings, 'debug', True)}")
        logger.info(f"🤖 AI features enabled: {getattr(settings, 'enable_ai_features', True)}")
        
        # Check AI configuration
        if getattr(settings, 'enable_ai_features', True) and os.getenv("OPENAI_API_KEY"):
            logger.info("🤖 AI Financial Advisor ready!")
        elif getattr(settings, 'enable_ai_features', True):
            logger.warning("⚠️ AI features enabled but OpenAI API key not configured")
            
        logger.info("✅ WealthTrackr API startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("🛑 Shutting down WealthTrackr API...")
    logger.info("✅ Shutdown completed successfully")

# ─── Enhanced Health Check Endpoints ───────────────────────────────────────
@app.get("/", tags=["Health Check"])
async def root():
    """Root endpoint with API information"""
    base_features = [
        "💰 Income & Expense Tracking",
        "📊 Category Management", 
        "🔐 Secure Authentication",
        "📱 Mobile & Web Support"
    ]
    
    ai_features = [
        "🤖 AI Financial Advisor",
        "📈 Market Insights",
        "🔄 Investment Recommendations",
        "🎯 Personalized Financial Analysis"
    ] if getattr(settings, 'enable_ai_features', True) else []
    
    return {
        "message": "Welcome to WealthTrackr AI-Powered Financial API 🚀🤖",
        "version": getattr(settings, 'app_version', '2.0.0'),
        "environment": getattr(settings, 'environment', 'development'),
        "features": base_features + ai_features,
        "endpoints": {
            "authentication": "/auth",
            "financial_profile": "/profile/financial", 
            "market_insights": "/market/insights",
            "ai_advice": "/ai/advice"
        },
        "health_check": "/health",
        "database_status": "/health/database",
        "documentation": "/docs" if getattr(settings, 'debug', True) else None
    }

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Comprehensive health check"""
    db_healthy = check_database_health()
    pool_status = get_db_pool_status()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": getattr(settings, 'app_version', '2.0.0'),
        "environment": getattr(settings, 'environment', 'development'),
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "pool": pool_status
        },
        "features": {
            "ai_enabled": getattr(settings, 'enable_ai_features', True),
            "ai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "email_verification": getattr(settings, 'enable_email_verification', False),
            "two_factor_auth": getattr(settings, 'enable_two_factor_auth', False)
        }
    }

@app.get("/health/database", tags=["Health Check"])
async def database_health():
    """Detailed database health check"""
    db_healthy = check_database_health()
    pool_status = get_db_pool_status()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "connection": "active" if db_healthy else "failed",
        "pool_info": pool_status,
        "database_url": "***configured***" if DATABASE_URL else "Not configured"
    }

# ─── Development Routes ─────────────────────────────────────────────────────
if getattr(settings, 'debug', True):
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """Debug endpoint to view current configuration (development only)"""
        return {
            "environment": getattr(settings, 'environment', 'development'),
            "debug": getattr(settings, 'debug', True),
            "features": {
                "ai_enabled": getattr(settings, 'enable_ai_features', True),
                "ai_configured": bool(os.getenv("OPENAI_API_KEY")),
                "email_verification": getattr(settings, 'enable_email_verification', False),
                "two_factor_auth": getattr(settings, 'enable_two_factor_auth', False),
                "premium_features": getattr(settings, 'enable_premium_features', False)
            },
            "database": {
                "echo": getattr(settings, 'database_echo', False),
                "pool_size": getattr(settings, 'database_pool_size', 5)
            }
        }
    
    @app.get("/debug/pool", tags=["Debug"])
    async def debug_pool():
        """Debug endpoint to view database pool status (development only)"""
        return get_db_pool_status()

# ─── Run Configuration ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    
    host = "127.0.0.1"
    port = 8000
    reload = getattr(settings, 'debug', True)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=getattr(settings, 'log_level', 'info').lower()
    )

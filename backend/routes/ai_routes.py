# backend/routes/ai_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.database import get_db
from backend.auth import get_current_user
from backend.models.models_user import User
from backend.ai.services.spending_analyzer import SpendingAnalyzer
from backend.ai.services.budget_intelligence import BudgetIntelligence
from backend.ai.services.subscription_optimizer import SubscriptionOptimizer
from backend.ai.services.investment_advisor import InvestmentAdvisor
from backend.ai.models.ai_models import AIInsight, UserFinancialProfile
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Financial Advisor"])

# Pydantic models for requests/responses
class UpdatePreferencesRequest(BaseModel):
    risk_tolerance: Optional[str] = None
    investment_goals: Optional[List[str]] = None
    preferred_sectors: Optional[List[str]] = None
    max_single_investment_amount: Optional[float] = None
    emergency_fund_target: Optional[float] = None

class BudgetAnalysisRequest(BaseModel):
    monthly_budget: Optional[float] = None

# --------------------------------------------------------------------------------------
# SPENDING ANALYSIS ENDPOINTS
# --------------------------------------------------------------------------------------

@router.get("/spending-insights", response_model=Dict[str, Any])
async def get_spending_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered spending insights and recommendations"""
    try:
        analyzer = SpendingAnalyzer(db)
        
        # Generate fresh insights
        insights = analyzer.analyze_spending_trends(current_user.id)
        
        # Get spending summary
        summary = analyzer.get_spending_summary(current_user.id)
        
        # Get recent insights from database
        recent_insights = db.query(AIInsight).filter(
            AIInsight.user_id == current_user.id,
            AIInsight.insight_type == "spending",
            AIInsight.is_dismissed == False
        ).order_by(AIInsight.created_at.desc()).limit(10).all()
        
        insight_data = []
        for insight in recent_insights:
            insight_data.append({
                "id": insight.id,
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
                "potential_savings": insight.potential_savings,
                "confidence_score": insight.confidence_score,
                "created_at": insight.created_at.isoformat(),
                "metadata": insight.metadata
            })
        
        return {
            "summary": summary,
            "insights": insight_data,
            "insights_generated": len(insights),
            "total_insights": len(recent_insights)
        }
        
    except Exception as e:
        logger.error(f"Error getting spending insights for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate spending insights")

@router.get("/spending-summary", response_model=Dict[str, Any])
async def get_spending_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive spending summary"""
    try:
        analyzer = SpendingAnalyzer(db)
        summary = analyzer.get_spending_summary(current_user.id)
        return summary
        
    except Exception as e:
        logger.error(f"Error getting spending summary for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate spending summary")

# --------------------------------------------------------------------------------------
# BUDGET INTELLIGENCE ENDPOINTS
# --------------------------------------------------------------------------------------

@router.post("/budget-analysis", response_model=Dict[str, Any])
async def analyze_budget(
    request: BudgetAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze budget health and provide intelligent insights"""
    try:
        budget_ai = BudgetIntelligence(db)
        
        # Generate budget insights
        insights = budget_ai.analyze_budget_health(current_user.id, request.monthly_budget)
        
        # Get budget forecast
        forecast = budget_ai.get_budget_forecast(current_user.id, days_ahead=30)
        
        # Get recent budget insights from database
        recent_insights = db.query(AIInsight).filter(
            AIInsight.user_id == current_user.id,
            AIInsight.insight_type == "budget",
            AIInsight.is_dismissed == False
        ).order_by(AIInsight.created_at.desc()).limit(5).all()
        
        insight_data = []
        for insight in recent_insights:
            insight_data.append({
                "id": insight.id,
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
                "potential_savings": insight.potential_savings,
                "confidence_score": insight.confidence_score,
                "created_at": insight.created_at.isoformat(),
                "metadata": insight.metadata
            })
        
        return {
            "forecast": forecast,
            "insights": insight_data,
            "insights_generated": len(insights),
            "monthly_budget": request.monthly_budget
        }
        
    except Exception as e:
        logger.error(f"Error analyzing budget for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze budget")

@router.get("/budget-forecast", response_model=Dict[str, Any])
async def get_budget_forecast(
    days_ahead: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get budget forecast for specified period"""
    try:
        budget_ai = BudgetIntelligence(db)
        forecast = budget_ai.get_budget_forecast(current_user.id, days_ahead)
        return forecast
        
    except Exception as e:
        logger.error(f"Error getting budget forecast for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate budget forecast")

# --------------------------------------------------------------------------------------
# SUBSCRIPTION OPTIMIZATION ENDPOINTS
# --------------------------------------------------------------------------------------

@router.get("/subscription-analysis", response_model=Dict[str, Any])
async def analyze_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze subscriptions and find optimization opportunities"""
    try:
        optimizer = SubscriptionOptimizer(db)
        
        # Generate subscription insights
        insights = optimizer.analyze_subscription_opportunities(current_user.id)
        
        # Get subscription summary
        summary = optimizer.get_subscription_summary(current_user.id)
        
        # Get recent subscription insights from database
        recent_insights = db.query(AIInsight).filter(
            AIInsight.user_id == current_user.id,
            AIInsight.insight_type == "subscription",
            AIInsight.is_dismissed == False
        ).order_by(AIInsight.created_at.desc()).limit(10).all()
        
        insight_data = []
        for insight in recent_insights:
            insight_data.append({
                "id": insight.id,
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
                "potential_savings": insight.potential_savings,
                "confidence_score": insight.confidence_score,
                "created_at": insight.created_at.isoformat(),
                "metadata": insight.metadata
            })
        
        return {
            "summary": summary,
            "insights": insight_data,
            "insights_generated": len(insights),
            "total_potential_savings": sum(
                insight.potential_savings for insight in recent_insights 
                if insight.potential_savings
            )
        }
        
    except Exception as e:
        logger.error(f"Error analyzing subscriptions for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze subscriptions")

# --------------------------------------------------------------------------------------
# INVESTMENT ADVISOR ENDPOINTS
# --------------------------------------------------------------------------------------

@router.get("/investment-recommendations", response_model=Dict[str, Any])
async def get_investment_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered investment recommendations"""
    try:
        advisor = InvestmentAdvisor(db)
        
        # Generate investment recommendations
        insights = advisor.generate_investment_recommendations(current_user.id)
        
        # Get investment summary
        summary = advisor.get_investment_summary(current_user.id)
        
        # Get market insights
        market_insights = advisor.get_market_insights()
        
        # Get recent investment insights from database
        recent_insights = db.query(AIInsight).filter(
            AIInsight.user_id == current_user.id,
            AIInsight.insight_type == "investment",
            AIInsight.is_dismissed == False
        ).order_by(AIInsight.created_at.desc()).limit(10).all()
        
        insight_data = []
        for insight in recent_insights:
            insight_data.append({
                "id": insight.id,
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
                "potential_savings": insight.potential_savings,
                "confidence_score": insight.confidence_score,
                "created_at": insight.created_at.isoformat(),
                "metadata": insight.metadata
            })
        
        return {
            "summary": summary,
            "market_insights": market_insights,
            "insights": insight_data,
            "insights_generated": len(insights),
            "investment_readiness": summary.get("investment_readiness", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting investment recommendations for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate investment recommendations")

@router.get("/market-insights", response_model=Dict[str, Any])
async def get_market_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current market insights and opportunities"""
    try:
        advisor = InvestmentAdvisor(db)
        insights = advisor.get_market_insights()
        return insights
        
    except Exception as e:
        logger.error(f"Error getting market insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market insights")

# --------------------------------------------------------------------------------------
# USER PROFILE AND PREFERENCES ENDPOINTS
# --------------------------------------------------------------------------------------

@router.get("/financial-profile", response_model=Dict[str, Any])
async def get_financial_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's financial profile"""
    try:
        analyzer = SpendingAnalyzer(db)  # Any analyzer works for this
        profile = analyzer.get_or_create_financial_profile(current_user.id)
        
        return {
            "risk_tolerance": profile.risk_tolerance,
            "investment_experience": profile.investment_experience,
            "investment_goals": profile.investment_goals,
            "monthly_income_avg": profile.monthly_income_avg,
            "monthly_expenses_avg": profile.monthly_expenses_avg,
            "savings_rate": profile.savings_rate,
            "financial_health_score": profile.financial_health_score,
            "top_expense_categories": profile.top_expense_categories,
            "emergency_fund_target": profile.emergency_fund_target,
            "last_analysis_date": profile.last_analysis_date.isoformat() if profile.last_analysis_date else None
        }
        
    except Exception as e:
        logger.error(f"Error getting financial profile for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get financial profile")

@router.post("/update-preferences", response_model=Dict[str, Any])
async def update_preferences(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's financial preferences"""
    try:
        # Get or create profile
        profile = db.query(UserFinancialProfile).filter(
            UserFinancialProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            analyzer = SpendingAnalyzer(db)
            profile = analyzer.get_or_create_financial_profile(current_user.id)
        
        # Update preferences
        if request.risk_tolerance:
            profile.risk_tolerance = request.risk_tolerance
        if request.investment_goals:
            profile.investment_goals = request.investment_goals
        if request.preferred_sectors:
            profile.preferred_sectors = request.preferred_sectors
        if request.max_single_investment_amount:
            profile.max_single_investment_amount = request.max_single_investment_amount
        if request.emergency_fund_target:
            profile.emergency_fund_target = request.emergency_fund_target
        
        profile.updated_at = db.func.now()
        db.commit()
        db.refresh(profile)
        
        return {
            "message": "Preferences updated successfully",
            "risk_tolerance": profile.risk_tolerance,
            "investment_goals": profile.investment_goals,
            "preferred_sectors": profile.preferred_sectors
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

# --------------------------------------------------------------------------------------
# COMPREHENSIVE AI ANALYSIS ENDPOINT
# --------------------------------------------------------------------------------------

@router.post("/analyze-all", response_model=Dict[str, Any])
async def analyze_all_finances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run comprehensive AI analysis across all financial areas"""
    try:
        # Initialize all analyzers
        spending_analyzer = SpendingAnalyzer(db)
        budget_intelligence = BudgetIntelligence(db)
        subscription_optimizer = SubscriptionOptimizer(db)
        investment_advisor = InvestmentAdvisor(db)
        
        # Update financial profile first
        profile = spending_analyzer.update_financial_profile(current_user.id)
        
        # Run all analyses
        spending_insights = spending_analyzer.analyze_spending_trends(current_user.id)
        budget_insights = budget_intelligence.analyze_budget_health(current_user.id)
        subscription_insights = subscription_optimizer.analyze_subscription_opportunities(current_user.id)
        investment_insights = investment_advisor.generate_investment_recommendations(current_user.id)
        
        # Get summaries
        spending_summary = spending_analyzer.get_spending_summary(current_user.id)
        subscription_summary = subscription_optimizer.get_subscription_summary(current_user.id)
        investment_summary = investment_advisor.get_investment_summary(current_user.id)
        
        total_insights = len(spending_insights) + len(budget_insights) + len(subscription_insights) + len(investment_insights)
        
        return {
            "message": f"Comprehensive analysis complete! Generated {total_insights} insights.",
            "financial_health_score": profile.financial_health_score,
            "insights_generated": {
                "spending": len(spending_insights),
                "budget": len(budget_insights),
                "subscriptions": len(subscription_insights),
                "investments": len(investment_insights),
                "total": total_insights
            },
            "summaries": {
                "spending": spending_summary,
                "subscriptions": subscription_summary,
                "investments": investment_summary
            },
            "analysis_date": profile.last_analysis_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running comprehensive analysis for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run comprehensive analysis")

# --------------------------------------------------------------------------------------
# INSIGHT MANAGEMENT ENDPOINTS
# --------------------------------------------------------------------------------------

@router.get("/insights", response_model=Dict[str, Any])
async def get_all_insights(
    insight_type: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's AI insights with optional filtering"""
    try:
        query = db.query(AIInsight).filter(
            AIInsight.user_id == current_user.id,
            AIInsight.is_dismissed == False
        )
        
        if insight_type:
            query = query.filter(AIInsight.insight_type == insight_type)
        
        insights = query.order_by(AIInsight.created_at.desc()).limit(limit).all()
        
        insight_data = []
        for insight in insights:
            insight_data.append({
                "id": insight.id,
                "type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
                "potential_savings": insight.potential_savings,
                "confidence_score": insight.confidence_score,
                "is_read": insight.is_read,
                "created_at": insight.created_at.isoformat(),
                "metadata": insight.metadata
            })
        
        return {
            "insights": insight_data,
            "total_count": len(insight_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting insights for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get insights")

@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(
    insight_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dismiss a specific insight"""
    try:
        insight = db.query(AIInsight).filter(
            AIInsight.id == insight_id,
            AIInsight.user_id == current_user.id
        ).first()
        
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        insight.is_dismissed = True
        db.commit()
        
        return {"message": "Insight dismissed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing insight {insight_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to dismiss insight")

@router.post("/insights/{insight_id}/mark-read")
async def mark_insight_read(
    insight_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific insight as read"""
    try:
        insight = db.query(AIInsight).filter(
            AIInsight.id == insight_id,
            AIInsight.user_id == current_user.id
        ).first()
        
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        insight.is_read = True
        db.commit()
        
        return {"message": "Insight marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking insight {insight_id} as read for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark insight as read")

# backend/ai/services/base_analyzer.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.models_user import User
from backend.models.models_expense import Expense
from backend.models.models_income import Income
from backend.ai.models.ai_models import UserFinancialProfile, AIInsight
import logging

logger = logging.getLogger(__name__)

class BaseFinancialAnalyzer:
    """Base class for all AI financial analysis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_expenses(self, user_id: int, days: int = 90) -> pd.DataFrame:
        """Get user expenses as pandas DataFrame"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        expenses = self.db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date_spent >= cutoff_date
        ).all()
        
        if not expenses:
            return pd.DataFrame()
        
        data = []
        for expense in expenses:
            data.append({
                'id': expense.id,
                'amount': expense.amount,
                'category_id': expense.category_id,
                'description': expense.description,
                'date': expense.date_spent,
                'month': expense.date_spent.strftime('%Y-%m'),
                'week': expense.date_spent.strftime('%Y-W%U')
            })
        
        return pd.DataFrame(data)
    
    def get_user_incomes(self, user_id: int, days: int = 90) -> pd.DataFrame:
        """Get user incomes as pandas DataFrame"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        incomes = self.db.query(Income).filter(
            Income.user_id == user_id,
            Income.date_received >= cutoff_date
        ).all()
        
        if not incomes:
            return pd.DataFrame()
        
        data = []
        for income in incomes:
            data.append({
                'id': income.id,
                'amount': income.amount,
                'source': income.source,
                'date': income.date_received,
                'month': income.date_received.strftime('%Y-%m'),
                'week': income.date_received.strftime('%Y-W%U')
            })
        
        return pd.DataFrame(data)
    
    def calculate_financial_health_score(self, user_id: int) -> float:
        """Calculate overall financial health score (0-100)"""
        try:
            expenses_df = self.get_user_expenses(user_id, days=90)
            incomes_df = self.get_user_incomes(user_id, days=90)
            
            if expenses_df.empty or incomes_df.empty:
                return 50.0  # Default score for new users
            
            # Calculate metrics
            monthly_income = incomes_df['amount'].sum() / 3  # 3 months average
            monthly_expenses = expenses_df['amount'].sum() / 3
            savings_rate = max(0, (monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0
            
            # Spending volatility (lower is better)
            monthly_spending = expenses_df.groupby('month')['amount'].sum()
            spending_volatility = monthly_spending.std() / monthly_spending.mean() if len(monthly_spending) > 1 else 0
            
            # Calculate score components
            savings_score = min(30, savings_rate * 1.5)  # Max 30 points for 20% savings rate
            income_stability_score = 25  # Assume stable for now
            spending_consistency_score = max(0, 25 - spending_volatility * 50)  # Penalize volatility
            expense_management_score = 20 if monthly_expenses < monthly_income else 0
            
            total_score = savings_score + income_stability_score + spending_consistency_score + expense_management_score
            
            return min(100, max(0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating financial health score for user {user_id}: {e}")
            return 50.0
    
    def get_or_create_financial_profile(self, user_id: int) -> UserFinancialProfile:
        """Get existing profile or create new one"""
        profile = self.db.query(UserFinancialProfile).filter(
            UserFinancialProfile.user_id == user_id
        ).first()
        
        if not profile:
            profile = UserFinancialProfile(
                user_id=user_id,
                financial_health_score=self.calculate_financial_health_score(user_id)
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        
        return profile
    
    def update_financial_profile(self, user_id: int) -> UserFinancialProfile:
        """Update user's financial profile with latest data"""
        try:
            profile = self.get_or_create_financial_profile(user_id)
            
            # Get recent data
            expenses_df = self.get_user_expenses(user_id, days=90)
            incomes_df = self.get_user_incomes(user_id, days=90)
            
            if not expenses_df.empty:
                # Update expense metrics
                profile.monthly_expenses_avg = expenses_df['amount'].sum() / 3
                
                # Calculate top expense categories
                if 'category_id' in expenses_df.columns:
                    category_totals = expenses_df.groupby('category_id')['amount'].sum()
                    total_expenses = category_totals.sum()
                    top_categories = []
                    for cat_id, amount in category_totals.head(5).items():
                        percentage = (amount / total_expenses) * 100
                        top_categories.append({
                            'category_id': int(cat_id) if pd.notna(cat_id) else None,
                            'amount': float(amount),
                            'percentage': float(percentage)
                        })
                    profile.top_expense_categories = top_categories
                
                # Calculate spending volatility
                monthly_spending = expenses_df.groupby('month')['amount'].sum()
                if len(monthly_spending) > 1:
                    profile.spending_volatility = float(monthly_spending.std())
            
            if not incomes_df.empty:
                # Update income metrics
                profile.monthly_income_avg = incomes_df['amount'].sum() / 3
            
            # Calculate savings rate
            if profile.monthly_income_avg > 0:
                profile.savings_rate = max(0, 
                    (profile.monthly_income_avg - profile.monthly_expenses_avg) / profile.monthly_income_avg * 100
                )
            
            # Update financial health score
            profile.financial_health_score = self.calculate_financial_health_score(user_id)
            profile.last_analysis_date = datetime.utcnow()
            profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Updated financial profile for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error updating financial profile for user {user_id}: {e}")
            self.db.rollback()
            raise e
    
    def create_insight(
        self, 
        user_id: int, 
        insight_type: str, 
        title: str, 
        description: str,
        priority: str = "medium",
        potential_savings: Optional[float] = None,
        confidence_score: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None,
        expires_days: Optional[int] = None
    ) -> AIInsight:
        """Create a new AI insight for the user"""
        
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        insight = AIInsight(
            user_id=user_id,
            insight_type=insight_type,
            title=title,
            description=description,
            priority=priority,
            potential_savings=potential_savings,
            confidence_score=confidence_score,
            insight_metadata=metadata,
            expires_at=expires_at
        )
        
        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)
        
        logger.info(f"Created {insight_type} insight for user {user_id}: {title}")
        return insight

# backend/ai/services/budget_intelligence.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.ai.services.base_analyzer import BaseFinancialAnalyzer
import logging

logger = logging.getLogger(__name__)

class BudgetIntelligence(BaseFinancialAnalyzer):
    """AI-powered budget analysis and predictions"""
    
    def analyze_budget_health(self, user_id: int, monthly_budget: Optional[float] = None) -> List[Dict[str, Any]]:
        """Analyze budget performance and provide insights"""
        insights = []
        
        try:
            expenses_df = self.get_user_expenses(user_id, days=90)
            incomes_df = self.get_user_incomes(user_id, days=90)
            
            if expenses_df.empty:
                return insights
            
            # Calculate current month spending
            current_month = datetime.now().strftime('%Y-%m')
            current_month_expenses = expenses_df[expenses_df['month'] == current_month]['amount'].sum()
            
            # Estimate monthly budget if not provided
            if monthly_budget is None:
                monthly_budget = self._estimate_monthly_budget(user_id, expenses_df, incomes_df)
            
            if monthly_budget > 0:
                # Budget utilization insights
                budget_insights = self._analyze_budget_utilization(
                    user_id, current_month_expenses, monthly_budget, current_month
                )
                insights.extend(budget_insights)
                
                # Spending pace analysis
                pace_insights = self._analyze_spending_pace(
                    user_id, expenses_df, monthly_budget, current_month
                )
                insights.extend(pace_insights)
            
            # Cash flow analysis
            cashflow_insights = self._analyze_cash_flow(user_id, expenses_df, incomes_df)
            insights.extend(cashflow_insights)
            
            # Budget optimization suggestions
            optimization_insights = self._suggest_budget_optimizations(user_id, expenses_df)
            insights.extend(optimization_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing budget health for user {user_id}: {e}")
            return []
    
    def _estimate_monthly_budget(self, user_id: int, expenses_df: pd.DataFrame, incomes_df: pd.DataFrame) -> float:
        """Estimate reasonable monthly budget based on income and spending patterns"""
        try:
            # Use average income as baseline
            if not incomes_df.empty:
                avg_monthly_income = incomes_df.groupby('month')['amount'].sum().mean()
                # Suggest 80-90% of income as budget (10-20% for savings)
                return avg_monthly_income * 0.85
            
            # Fallback: use average spending + 10% buffer
            if not expenses_df.empty:
                avg_monthly_expenses = expenses_df.groupby('month')['amount'].sum().mean()
                return avg_monthly_expenses * 1.1
            
            return 0
            
        except Exception:
            return 0
    
    def _analyze_budget_utilization(
        self, 
        user_id: int, 
        current_spending: float, 
        monthly_budget: float, 
        current_month: str
    ) -> List[Dict[str, Any]]:
        """Analyze how much of the budget has been used"""
        insights = []
        
        utilization_rate = (current_spending / monthly_budget) * 100 if monthly_budget > 0 else 0
        remaining_budget = monthly_budget - current_spending
        
        # Get days into current month
        today = datetime.now()
        days_in_month = (datetime(today.year, today.month + 1, 1) - timedelta(days=1)).day
        current_day = today.day
        month_progress = (current_day / days_in_month) * 100
        
        if utilization_rate > 90:
            priority = "urgent" if utilization_rate > 100 else "high"
            title = "Budget nearly exhausted!" if utilization_rate <= 100 else "Budget exceeded!"
            
            insight = self.create_insight(
                user_id=user_id,
                insight_type="budget",
                title=title,
                description=f"You've used {utilization_rate:.1f}% of your monthly budget (${current_spending:.2f} of ${monthly_budget:.2f}). Consider reducing discretionary spending for the rest of the month.",
                priority=priority,
                confidence_score=0.95,
                insight_metadata={
                    "utilization_rate": utilization_rate,
                    "remaining_budget": remaining_budget,
                    "month_progress": month_progress,
                    "current_spending": current_spending,
                    "monthly_budget": monthly_budget
                }
            )
            insights.append(insight)
            
        elif utilization_rate > 75 and month_progress < 60:
            # Spending too fast
            insight = self.create_insight(
                user_id=user_id,
                insight_type="budget",
                title="Spending ahead of pace",
                description=f"You've used {utilization_rate:.1f}% of your budget but we're only {month_progress:.1f}% through the month. Consider slowing down spending to stay on track.",
                priority="medium",
                confidence_score=0.8,
                insight_metadata={
                    "utilization_rate": utilization_rate,
                    "month_progress": month_progress,
                    "pace_ratio": utilization_rate / month_progress
                }
            )
            insights.append(insight)
            
        elif utilization_rate < 50 and month_progress > 75:
            # Under-spending
            insight = self.create_insight(
                user_id=user_id,
                insight_type="budget",
                title="Great budget discipline!",
                description=f"You've only used {utilization_rate:.1f}% of your budget with {100-month_progress:.1f}% of the month remaining. You're on track for excellent savings this month!",
                priority="low",
                potential_savings=remaining_budget,
                confidence_score=0.8,
                insight_metadata={
                    "utilization_rate": utilization_rate,
                    "projected_savings": remaining_budget
                }
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_spending_pace(
        self, 
        user_id: int, 
        expenses_df: pd.DataFrame, 
        monthly_budget: float, 
        current_month: str
    ) -> List[Dict[str, Any]]:
        """Analyze daily spending pace and predict month-end spending"""
        insights = []
        
        try:
            current_month_df = expenses_df[expenses_df['month'] == current_month].copy()
            
            if current_month_df.empty:
                return insights
            
            # Calculate daily spending
            daily_spending = current_month_df.groupby(current_month_df['date'].dt.date)['amount'].sum()
            avg_daily_spending = daily_spending.mean()
            
            # Project month-end spending
            today = datetime.now()
            days_remaining = (datetime(today.year, today.month + 1, 1) - today).days
            projected_total = current_month_df['amount'].sum() + (avg_daily_spending * days_remaining)
            
            budget_variance = projected_total - monthly_budget
            
            if budget_variance > monthly_budget * 0.1:  # Projected to exceed budget by >10%
                daily_reduction_needed = budget_variance / days_remaining if days_remaining > 0 else 0
                
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="budget",
                    title=f"Projected to exceed budget by ${budget_variance:.2f}",
                    description=f"At your current spending pace (${avg_daily_spending:.2f}/day), you'll spend ${projected_total:.2f} this month. Reduce daily spending by ${daily_reduction_needed:.2f} to stay on budget.",
                    priority="high",
                    confidence_score=0.85,
                    insight_metadata={
                        "projected_total": projected_total,
                        "budget_variance": budget_variance,
                        "avg_daily_spending": avg_daily_spending,
                        "daily_reduction_needed": daily_reduction_needed,
                        "days_remaining": days_remaining
                    }
                )
                insights.append(insight)
                
            elif budget_variance < -monthly_budget * 0.1:  # Projected under-spending
                projected_savings = abs(budget_variance)
                
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="budget",
                    title=f"On track to save ${projected_savings:.2f} this month!",
                    description=f"Your current spending pace suggests you'll finish ${projected_savings:.2f} under budget. Great job staying disciplined!",
                    priority="low",
                    potential_savings=projected_savings,
                    confidence_score=0.8,
                    insight_metadata={
                        "projected_savings": projected_savings,
                        "projected_total": projected_total
                    }
                )
                insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing spending pace: {e}")
        
        return insights
    
    def _analyze_cash_flow(
        self, 
        user_id: int, 
        expenses_df: pd.DataFrame, 
        incomes_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Analyze cash flow patterns"""
        insights = []
        
        try:
            if incomes_df.empty or expenses_df.empty:
                return insights
            
            # Monthly cash flow analysis
            monthly_income = incomes_df.groupby('month')['amount'].sum()
            monthly_expenses = expenses_df.groupby('month')['amount'].sum()
            
            # Align months
            common_months = monthly_income.index.intersection(monthly_expenses.index)
            
            for month in common_months:
                income = monthly_income[month]
                expenses = monthly_expenses[month]
                net_cash_flow = income - expenses
                savings_rate = (net_cash_flow / income) * 100 if income > 0 else 0
                
                if net_cash_flow < 0:
                    # Negative cash flow
                    insight = self.create_insight(
                        user_id=user_id,
                        insight_type="budget",
                        title=f"Negative cash flow in {month}",
                        description=f"You spent ${abs(net_cash_flow):.2f} more than you earned in {month}. Review your expenses and consider increasing income or reducing spending.",
                        priority="high",
                        confidence_score=0.9,
                        insight_metadata={
                            "month": month,
                            "income": income,
                            "expenses": expenses,
                            "cash_flow": net_cash_flow
                        }
                    )
                    insights.append(insight)
                    
                elif savings_rate > 20:
                    # High savings rate
                    insight = self.create_insight(
                        user_id=user_id,
                        insight_type="budget",
                        title=f"Excellent savings rate: {savings_rate:.1f}% in {month}",
                        description=f"You saved ${net_cash_flow:.2f} ({savings_rate:.1f}% of income) in {month}. Consider investing this surplus for long-term growth.",
                        priority="low",
                        potential_savings=net_cash_flow,
                        confidence_score=0.8,
                        insight_metadata={
                            "month": month,
                            "savings_rate": savings_rate,
                            "savings_amount": net_cash_flow
                        }
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing cash flow: {e}")
        
        return insights
    
    def _suggest_budget_optimizations(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Suggest budget optimizations based on spending patterns"""
        insights = []
        
        try:
            if expenses_df.empty or 'category_id' not in expenses_df.columns:
                return insights
            
            # Analyze category spending for optimization opportunities
            category_spending = expenses_df.groupby('category_id')['amount'].agg(['sum', 'count', 'std']).reset_index()
            total_spending = category_spending['sum'].sum()
            
            for _, row in category_spending.iterrows():
                category_id = row['category_id']
                amount = row['sum']
                count = row['count']
                std_dev = row['std'] if pd.notna(row['std']) else 0
                percentage = (amount / total_spending) * 100
                
                # High variability in spending
                if std_dev > amount / count * 0.5 and count > 5:  # High variability
                    potential_savings = std_dev * 0.3  # Conservative estimate
                    
                    insight = self.create_insight(
                        user_id=user_id,
                        insight_type="budget",
                        title="Inconsistent spending detected",
                        description=f"Your spending in this category varies significantly. Setting a specific budget limit could help reduce overspending and save you approximately ${potential_savings:.2f} monthly.",
                        priority="medium",
                        potential_savings=potential_savings,
                        confidence_score=0.7,
                        insight_metadata={
                            "category_id": category_id,
                            "spending_variability": std_dev,
                            "average_amount": amount / count,
                            "transaction_count": count
                        }
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error suggesting budget optimizations: {e}")
        
        return insights
    
    def get_budget_forecast(self, user_id: int, days_ahead: int = 30) -> Dict[str, Any]:
        """Generate budget forecast for upcoming period"""
        try:
            expenses_df = self.get_user_expenses(user_id, days=90)
            
            if expenses_df.empty:
                return {"error": "Insufficient data for forecast"}
            
            # Calculate historical averages
            daily_avg = expenses_df['amount'].sum() / 90  # 90-day average
            weekly_avg = expenses_df.groupby('week')['amount'].sum().mean()
            monthly_avg = expenses_df.groupby('month')['amount'].sum().mean()
            
            # Seasonal adjustments (simple model)
            current_month = datetime.now().month
            seasonal_multiplier = 1.0
            
            # Holiday months tend to have higher spending
            if current_month in [11, 12]:  # November, December
                seasonal_multiplier = 1.15
            elif current_month in [6, 7, 8]:  # Summer months
                seasonal_multiplier = 1.05
            
            # Generate forecast
            forecasted_daily = daily_avg * seasonal_multiplier
            forecasted_total = forecasted_daily * days_ahead
            
            # Confidence interval (simple model)
            std_dev = expenses_df.groupby(expenses_df['date'].dt.date)['amount'].sum().std()
            confidence_margin = std_dev * np.sqrt(days_ahead) * 1.96  # 95% confidence
            
            return {
                "forecasted_total": round(forecasted_total, 2),
                "forecasted_daily_avg": round(forecasted_daily, 2),
                "confidence_lower": round(forecasted_total - confidence_margin, 2),
                "confidence_upper": round(forecasted_total + confidence_margin, 2),
                "historical_daily_avg": round(daily_avg, 2),
                "seasonal_multiplier": seasonal_multiplier,
                "forecast_period_days": days_ahead
            }
            
        except Exception as e:
            logger.error(f"Error generating budget forecast for user {user_id}: {e}")
            return {"error": "Unable to generate forecast"}

# backend/ai/services/spending_analyzer.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.ai.services.base_analyzer import BaseFinancialAnalyzer
import logging

logger = logging.getLogger(__name__)

class SpendingAnalyzer(BaseFinancialAnalyzer):
    """AI-powered spending analysis and insights"""
    
    def analyze_spending_trends(self, user_id: int) -> List[Dict[str, Any]]:
        """Analyze spending trends and generate insights"""
        insights = []
        
        try:
            # Get spending data
            expenses_df = self.get_user_expenses(user_id, days=90)
            if expenses_df.empty:
                return insights
            
            # Monthly trend analysis
            monthly_insights = self._analyze_monthly_trends(user_id, expenses_df)
            insights.extend(monthly_insights)
            
            # Category analysis
            category_insights = self._analyze_category_spending(user_id, expenses_df)
            insights.extend(category_insights)
            
            # Unusual spending detection
            anomaly_insights = self._detect_spending_anomalies(user_id, expenses_df)
            insights.extend(anomaly_insights)
            
            # Spending efficiency analysis
            efficiency_insights = self._analyze_spending_efficiency(user_id, expenses_df)
            insights.extend(efficiency_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing spending trends for user {user_id}: {e}")
            return []
    
    def _analyze_monthly_trends(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze month-over-month spending trends"""
        insights = []
        
        # Group by month
        monthly_spending = expenses_df.groupby('month')['amount'].sum().sort_index()
        
        if len(monthly_spending) < 2:
            return insights
        
        # Calculate trend
        current_month = monthly_spending.iloc[-1]
        previous_month = monthly_spending.iloc[-2]
        change_amount = current_month - previous_month
        change_percent = (change_amount / previous_month) * 100 if previous_month > 0 else 0
        
        if abs(change_percent) > 15:  # Significant change
            if change_percent > 0:
                priority = "high" if change_percent > 30 else "medium"
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="spending",
                    title=f"Spending increased by {change_percent:.1f}% this month",
                    description=f"You spent ${change_amount:.2f} more than last month (${current_month:.2f} vs ${previous_month:.2f}). Consider reviewing your recent purchases to identify areas for optimization.",
                    priority=priority,
                    confidence_score=0.9,
                    insight_metadata={
                        "change_amount": change_amount,
                        "change_percent": change_percent,
                        "current_month_spending": current_month,
                        "previous_month_spending": previous_month
                    }
                )
                insights.append(insight)
            else:
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="spending",
                    title=f"Great job! Spending decreased by {abs(change_percent):.1f}%",
                    description=f"You saved ${abs(change_amount):.2f} compared to last month. Keep up the excellent spending discipline!",
                    priority="low",
                    confidence_score=0.9,
                    insight_metadata={
                        "savings_amount": abs(change_amount),
                        "change_percent": change_percent
                    }
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_category_spending(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze spending by category"""
        insights = []
        
        if 'category_id' not in expenses_df.columns or expenses_df['category_id'].isna().all():
            return insights
        
        # Category spending analysis
        category_spending = expenses_df.groupby('category_id')['amount'].agg(['sum', 'count', 'mean']).reset_index()
        total_spending = category_spending['sum'].sum()
        
        for _, row in category_spending.iterrows():
            category_id = row['category_id']
            amount = row['sum']
            count = row['count']
            avg_amount = row['mean']
            percentage = (amount / total_spending) * 100
            
            # High spending category alert
            if percentage > 30:
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="spending",
                    title=f"High spending in category: {percentage:.1f}% of total",
                    description=f"You've spent ${amount:.2f} ({percentage:.1f}% of total spending) in this category over the last 3 months. Consider if this aligns with your financial goals.",
                    priority="medium",
                    confidence_score=0.8,
                    insight_metadata={
                        "category_id": category_id,
                        "amount": amount,
                        "percentage": percentage,
                        "transaction_count": count
                    }
                )
                insights.append(insight)
            
            # Frequent small purchases
            if count > 20 and avg_amount < 25:
                potential_savings = count * 5  # Assume $5 savings per transaction
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="spending",
                    title=f"Many small purchases detected ({count} transactions)",
                    description=f"You made {count} small purchases averaging ${avg_amount:.2f} each. Bundling purchases or planning ahead could save you money.",
                    priority="low",
                    potential_savings=potential_savings,
                    confidence_score=0.7,
                    insight_metadata={
                        "category_id": category_id,
                        "transaction_count": count,
                        "average_amount": avg_amount
                    }
                )
                insights.append(insight)
        
        return insights
    
    def _detect_spending_anomalies(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect unusual spending patterns"""
        insights = []
        
        # Weekly spending analysis
        weekly_spending = expenses_df.groupby('week')['amount'].sum()
        
        if len(weekly_spending) < 4:
            return insights
        
        # Calculate statistics
        mean_weekly = weekly_spending.mean()
        std_weekly = weekly_spending.std()
        
        # Find anomalous weeks (spending > 2 standard deviations from mean)
        threshold = mean_weekly + (2 * std_weekly)
        anomalous_weeks = weekly_spending[weekly_spending > threshold]
        
        for week, amount in anomalous_weeks.items():
            if amount > mean_weekly * 1.5:  # At least 50% above average
                excess_amount = amount - mean_weekly
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="spending",
                    title=f"Unusual spending spike detected",
                    description=f"You spent ${amount:.2f} in week {week}, which is ${excess_amount:.2f} above your typical weekly spending. Was this a planned expense?",
                    priority="medium",
                    confidence_score=0.8,
                    insight_metadata={
                        "week": week,
                        "amount": amount,
                        "excess_amount": excess_amount,
                        "average_weekly": mean_weekly
                    },
                    expires_days=14
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_spending_efficiency(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze spending efficiency and suggest optimizations"""
        insights = []
        
        # Weekend vs weekday spending
        expenses_df['day_of_week'] = expenses_df['date'].dt.dayofweek
        expenses_df['is_weekend'] = expenses_df['day_of_week'] >= 5
        
        weekend_spending = expenses_df[expenses_df['is_weekend']]['amount'].sum()
        weekday_spending = expenses_df[~expenses_df['is_weekend']]['amount'].sum()
        total_spending = weekend_spending + weekday_spending
        
        if total_spending > 0:
            weekend_percentage = (weekend_spending / total_spending) * 100
            
            if weekend_percentage > 40:  # High weekend spending
                potential_savings = weekend_spending * 0.15  # Assume 15% savings potential
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="spending",
                    title=f"High weekend spending: {weekend_percentage:.1f}% of total",
                    description=f"You spend significantly more on weekends (${weekend_spending:.2f} vs ${weekday_spending:.2f} on weekdays). Planning weekend activities in advance could help reduce impulse purchases.",
                    priority="low",
                    potential_savings=potential_savings,
                    confidence_score=0.7,
                    insight_metadata={
                        "weekend_spending": weekend_spending,
                        "weekday_spending": weekday_spending,
                        "weekend_percentage": weekend_percentage
                    }
                )
                insights.append(insight)
        
        return insights
    
    def get_spending_summary(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive spending summary"""
        try:
            expenses_df = self.get_user_expenses(user_id, days=90)
            
            if expenses_df.empty:
                return {
                    "total_spending_3m": 0,
                    "avg_monthly_spending": 0,
                    "avg_weekly_spending": 0,
                    "total_transactions": 0,
                    "avg_transaction_amount": 0,
                    "spending_trend": "no_data"
                }
            
            # Basic metrics
            total_spending = expenses_df['amount'].sum()
            total_transactions = len(expenses_df)
            avg_transaction = expenses_df['amount'].mean()
            
            # Time-based metrics
            monthly_spending = expenses_df.groupby('month')['amount'].sum()
            avg_monthly = monthly_spending.mean()
            
            weekly_spending = expenses_df.groupby('week')['amount'].sum()
            avg_weekly = weekly_spending.mean()
            
            # Trend calculation
            trend = "stable"
            if len(monthly_spending) >= 2:
                recent_change = (monthly_spending.iloc[-1] - monthly_spending.iloc[-2]) / monthly_spending.iloc[-2] * 100
                if recent_change > 10:
                    trend = "increasing"
                elif recent_change < -10:
                    trend = "decreasing"
            
            return {
                "total_spending_3m": round(total_spending, 2),
                "avg_monthly_spending": round(avg_monthly, 2),
                "avg_weekly_spending": round(avg_weekly, 2),
                "total_transactions": total_transactions,
                "avg_transaction_amount": round(avg_transaction, 2),
                "spending_trend": trend,
                "monthly_breakdown": monthly_spending.to_dict() if not monthly_spending.empty else {}
            }
            
        except Exception as e:
            logger.error(f"Error generating spending summary for user {user_id}: {e}")
            return {"error": "Unable to generate spending summary"}

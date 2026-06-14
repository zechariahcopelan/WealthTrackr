# backend/ai/services/investment_advisor.py

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.ai.services.base_analyzer import BaseFinancialAnalyzer
from backend.ai.models.ai_models import InvestmentRecommendation, UserFinancialProfile
import logging

logger = logging.getLogger(__name__)

class InvestmentAdvisor(BaseFinancialAnalyzer):
    """AI-powered investment recommendations based on spending patterns and financial profile"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.safe_etfs = ['SPY', 'VOO', 'VTI', 'VXUS', 'BND']  # Safe, diversified ETFs
        self.sector_etfs = {
            'technology': ['QQQ', 'VGT', 'ARKK'],
            'healthcare': ['VHT', 'XLV', 'IBB'],
            'finance': ['XLF', 'VFH', 'KBE'],
            'energy': ['XLE', 'VDE', 'ICLN'],
            'consumer': ['XLY', 'VCR', 'AMZN'],
            'real_estate': ['VNQ', 'IYR', 'REZ']
        }
    
    def generate_investment_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate personalized investment recommendations"""
        insights = []
        
        try:
            # Update user's financial profile
            profile = self.update_financial_profile(user_id)
            
            # Get spending patterns to infer interests
            expenses_df = self.get_user_expenses(user_id, days=180)
            incomes_df = self.get_user_incomes(user_id, days=90)
            
            # Calculate investable surplus
            investable_amount = self._calculate_investable_surplus(profile, incomes_df, expenses_df)
            
            if investable_amount <= 0:
                # Create insight about building emergency fund first
                emergency_insight = self._suggest_emergency_fund(user_id, profile)
                if emergency_insight:
                    insights.append(emergency_insight)
                return insights
            
            # Generate different types of recommendations
            
            # 1. Core portfolio recommendations (safe, diversified)
            core_recommendations = self._generate_core_portfolio_recommendations(user_id, profile, investable_amount)
            insights.extend(core_recommendations)
            
            # 2. Interest-based recommendations (based on spending patterns)
            interest_recommendations = self._generate_interest_based_recommendations(user_id, expenses_df, investable_amount)
            insights.extend(interest_recommendations)
            
            # 3. Risk-appropriate individual stock recommendations
            stock_recommendations = self._generate_stock_recommendations(user_id, profile, investable_amount)
            insights.extend(stock_recommendations)
            
            # 4. Dollar-cost averaging suggestions
            dca_recommendations = self._suggest_dollar_cost_averaging(user_id, profile, investable_amount)
            insights.extend(dca_recommendations)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating investment recommendations for user {user_id}: {e}")
            return []
    
    def _calculate_investable_surplus(
        self, 
        profile: UserFinancialProfile, 
        incomes_df: pd.DataFrame, 
        expenses_df: pd.DataFrame
    ) -> float:
        """Calculate how much the user can realistically invest"""
        try:
            if incomes_df.empty or expenses_df.empty:
                return 0
            
            monthly_income = profile.monthly_income_avg
            monthly_expenses = profile.monthly_expenses_avg
            monthly_surplus = monthly_income - monthly_expenses
            
            # Reserve for emergency fund (3-6 months expenses)
            emergency_fund_needed = monthly_expenses * 3
            current_emergency_fund = profile.emergency_fund_target  # Assume they tell us or we estimate
            
            # Only recommend investing if they have emergency fund covered
            if current_emergency_fund < emergency_fund_needed:
                return 0
            
            # Conservative approach: recommend investing 50-80% of surplus
            risk_multiplier = {
                'conservative': 0.5,
                'moderate': 0.65,
                'aggressive': 0.8
            }.get(profile.risk_tolerance, 0.6)
            
            investable_monthly = monthly_surplus * risk_multiplier
            return max(0, investable_monthly)
            
        except Exception as e:
            logger.error(f"Error calculating investable surplus: {e}")
            return 0
    
    def _suggest_emergency_fund(self, user_id: int, profile: UserFinancialProfile) -> Optional[Dict[str, Any]]:
        """Suggest building emergency fund before investing"""
        try:
            if profile.monthly_expenses_avg <= 0:
                return None
            
            emergency_fund_target = profile.monthly_expenses_avg * 6
            current_savings_rate = profile.savings_rate
            
            if current_savings_rate > 0:
                monthly_savings = (profile.monthly_income_avg * current_savings_rate) / 100
                months_to_emergency_fund = emergency_fund_target / monthly_savings if monthly_savings > 0 else 999
                
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="investment",
                    title="Build emergency fund before investing",
                    description=f"Focus on building a ${emergency_fund_target:.0f} emergency fund (6 months of expenses) before investing. At your current savings rate, you'll reach this goal in {months_to_emergency_fund:.1f} months.",
                    priority="high",
                    confidence_score=0.9,
                    insight_metadata={
                        "emergency_fund_target": emergency_fund_target,
                        "current_savings_rate": current_savings_rate,
                        "months_to_goal": months_to_emergency_fund,
                        "recommended_action": "emergency_fund"
                    }
                )
                return insight
            
        except Exception as e:
            logger.error(f"Error suggesting emergency fund: {e}")
        
        return None
    
    def _generate_core_portfolio_recommendations(
        self, 
        user_id: int, 
        profile: UserFinancialProfile, 
        investable_amount: float
    ) -> List[Dict[str, Any]]:
        """Generate core portfolio recommendations (safe, diversified ETFs)"""
        insights = []
        
        try:
            # Recommend based on risk tolerance
            if profile.risk_tolerance == 'conservative':
                allocation = {'SPY': 0.4, 'BND': 0.4, 'VXUS': 0.2}  # 40% US stocks, 40% bonds, 20% international
            elif profile.risk_tolerance == 'aggressive':
                allocation = {'VTI': 0.6, 'VXUS': 0.3, 'QQQ': 0.1}  # 60% US total market, 30% international, 10% tech
            else:  # moderate
                allocation = {'SPY': 0.5, 'VXUS': 0.25, 'BND': 0.25}  # 50% US stocks, 25% international, 25% bonds
            
            for symbol, percentage in allocation.items():
                try:
                    # Get current stock data
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                    
                    if current_price > 0:
                        suggested_amount = investable_amount * percentage
                        
                        # Create investment recommendation in database
                        recommendation = InvestmentRecommendation(
                            user_id=user_id,
                            symbol=symbol,
                            name=info.get('longName', symbol),
                            investment_type='etf',
                            sector=info.get('category', 'Diversified'),
                            recommendation_type='buy',
                            confidence_score=0.85,
                            risk_level=profile.risk_tolerance,
                            current_price=current_price,
                            expected_return_1y=8.0 if 'SPY' in symbol or 'VTI' in symbol else 6.0,
                            reason_summary=f"Core portfolio allocation for {profile.risk_tolerance} investor",
                            key_factors=[
                                "Diversified exposure",
                                "Low expense ratio",
                                "Long-term track record",
                                f"Suitable for {profile.risk_tolerance} risk tolerance"
                            ],
                            suggested_allocation=percentage * 100,
                            min_investment_amount=suggested_amount,
                            time_horizon="long_term"
                        )
                        
                        self.db.add(recommendation)
                        
                        # Create insight
                        insight = self.create_insight(
                            user_id=user_id,
                            insight_type="investment",
                            title=f"Core holding: {info.get('longName', symbol)}",
                            description=f"Allocate {percentage*100:.0f}% (${suggested_amount:.0f}) of your portfolio to {symbol}. This provides diversified exposure with low risk and steady long-term growth potential.",
                            priority="medium",
                            confidence_score=0.85,
                            insight_metadata={
                                "symbol": symbol,
                                "allocation_percentage": percentage * 100,
                                "suggested_amount": suggested_amount,
                                "current_price": current_price,
                                "investment_type": "core_holding",
                                "risk_level": profile.risk_tolerance
                            }
                        )
                        insights.append(insight)
                
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error generating core portfolio recommendations: {e}")
            self.db.rollback()
        
        return insights
    
    def _generate_interest_based_recommendations(
        self, 
        user_id: int, 
        expenses_df: pd.DataFrame, 
        investable_amount: float
    ) -> List[Dict[str, Any]]:
        """Generate investment recommendations based on user's spending patterns"""
        insights = []
        
        try:
            if expenses_df.empty or 'description' not in expenses_df.columns:
                return insights
            
            # Analyze spending to infer interests
            spending_interests = self._analyze_spending_for_interests(expenses_df)
            
            for interest, spending_amount in spending_interests.items():
                if interest in self.sector_etfs:
                    # Recommend sector ETFs based on spending patterns
                    recommended_etfs = self.sector_etfs[interest][:2]  # Top 2 ETFs in sector
                    
                    for symbol in recommended_etfs:
                        try:
                            stock = yf.Ticker(symbol)
                            info = stock.info
                            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                            
                            if current_price > 0:
                                # Suggest smaller allocation for sector-specific investments (5-15%)
                                suggested_allocation = min(15, max(5, (spending_amount / expenses_df['amount'].sum()) * 50))
                                suggested_amount = investable_amount * (suggested_allocation / 100)
                                
                                # Create investment recommendation
                                recommendation = InvestmentRecommendation(
                                    user_id=user_id,
                                    symbol=symbol,
                                    name=info.get('longName', symbol),
                                    investment_type='etf',
                                    sector=interest.title(),
                                    recommendation_type='buy',
                                    confidence_score=0.75,
                                    risk_level='moderate',
                                    current_price=current_price,
                                    expected_return_1y=10.0,  # Higher expected return for sector-specific
                                    reason_summary=f"Based on your ${spending_amount:.0f} spending in {interest}",
                                    key_factors=[
                                        f"You spend significantly on {interest}",
                                        "Sector-specific exposure",
                                        "Growth potential",
                                        "Aligns with your interests"
                                    ],
                                    suggested_allocation=suggested_allocation,
                                    min_investment_amount=max(100, suggested_amount),
                                    time_horizon="medium_term"
                                )
                                
                                self.db.add(recommendation)
                                
                                insight = self.create_insight(
                                    user_id=user_id,
                                    insight_type="investment",
                                    title=f"Invest in {interest} sector: {symbol}",
                                    description=f"You spend ${spending_amount:.0f} on {interest}. Consider investing ${suggested_amount:.0f} ({suggested_allocation:.1f}%) in {symbol} to benefit from growth in sectors you already support.",
                                    priority="low",
                                    confidence_score=0.75,
                                    insight_metadata={
                                        "symbol": symbol,
                                        "sector": interest,
                                        "spending_amount": spending_amount,
                                        "suggested_amount": suggested_amount,
                                        "allocation_percentage": suggested_allocation,
                                        "rationale": "spending_pattern_alignment"
                                    }
                                )
                                insights.append(insight)
                                break  # Only recommend one ETF per sector
                        
                        except Exception as e:
                            logger.error(f"Error processing {symbol} for {interest}: {e}")
                            continue
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error generating interest-based recommendations: {e}")
            self.db.rollback()
        
        return insights
    
    def _analyze_spending_for_interests(self, expenses_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze spending patterns to infer user interests/sectors"""
        interests = {}
        
        try:
            # Define spending categories and their corresponding investment sectors
            sector_keywords = {
                'technology': ['apple', 'microsoft', 'google', 'amazon', 'tech', 'software', 'computer', 'phone', 'electronics'],
                'healthcare': ['pharmacy', 'doctor', 'medical', 'health', 'hospital', 'medicine', 'cvs', 'walgreens'],
                'consumer': ['amazon', 'target', 'walmart', 'retail', 'shopping', 'clothing', 'restaurant', 'food'],
                'energy': ['gas', 'electric', 'utility', 'shell', 'exxon', 'energy', 'fuel'],
                'finance': ['bank', 'credit', 'loan', 'insurance', 'financial'],
                'real_estate': ['rent', 'mortgage', 'property', 'real estate', 'home depot', 'lowes']
            }
            
            for sector, keywords in sector_keywords.items():
                sector_spending = 0
                
                for _, expense in expenses_df.iterrows():
                    description = str(expense.get('description', '')).lower()
                    
                    if any(keyword in description for keyword in keywords):
                        sector_spending += expense['amount']
                
                if sector_spending > 0:
                    interests[sector] = sector_spending
            
            return interests
            
        except Exception as e:
            logger.error(f"Error analyzing spending for interests: {e}")
            return {}
    
    def _generate_stock_recommendations(
        self, 
        user_id: int, 
        profile: UserFinancialProfile, 
        investable_amount: float
    ) -> List[Dict[str, Any]]:
        """Generate individual stock recommendations based on risk tolerance"""
        insights = []
        
        try:
            # Only recommend individual stocks for moderate/aggressive investors
            if profile.risk_tolerance == 'conservative':
                return insights
            
            # Conservative list of large-cap, dividend-paying stocks
            quality_stocks = ['AAPL', 'MSFT', 'GOOGL', 'JNJ', 'PG', 'KO', 'DIS', 'V']
            
            # Recommend 2-3 stocks maximum
            recommended_count = 2 if profile.risk_tolerance == 'moderate' else 3
            
            for i, symbol in enumerate(quality_stocks[:recommended_count]):
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                    
                    if current_price > 0:
                        # Conservative allocation for individual stocks (5-10%)
                        suggested_allocation = 5 + (i * 2)  # 5%, 7%, 9%
                        suggested_amount = investable_amount * (suggested_allocation / 100)
                        
                        # Get some basic metrics
                        pe_ratio = info.get('trailingPE', 0)
                        dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                        
                        recommendation = InvestmentRecommendation(
                            user_id=user_id,
                            symbol=symbol,
                            name=info.get('longName', symbol),
                            investment_type='stock',
                            sector=info.get('sector', 'Technology'),
                            recommendation_type='buy',
                            confidence_score=0.7,
                            risk_level='medium',
                            current_price=current_price,
                            expected_return_1y=12.0,
                            dividend_yield=dividend_yield,
                            reason_summary=f"Quality large-cap stock suitable for {profile.risk_tolerance} investor",
                            key_factors=[
                                "Large-cap stability",
                                "Strong fundamentals",
                                "Dividend income" if dividend_yield > 1 else "Growth potential",
                                "Blue-chip quality"
                            ],
                            risks=[
                                "Individual stock volatility",
                                "Market risk",
                                "Sector concentration"
                            ],
                            suggested_allocation=suggested_allocation,
                            min_investment_amount=max(500, suggested_amount),
                            time_horizon="long_term"
                        )
                        
                        self.db.add(recommendation)
                        
                        insight = self.create_insight(
                            user_id=user_id,
                            insight_type="investment",
                            title=f"Quality stock pick: {symbol}",
                            description=f"Consider ${suggested_amount:.0f} ({suggested_allocation}%) in {info.get('longName', symbol)}. Strong fundamentals, established company, suitable for building long-term wealth.",
                            priority="low",
                            confidence_score=0.7,
                            insight_metadata={
                                "symbol": symbol,
                                "company_name": info.get('longName', symbol),
                                "current_price": current_price,
                                "pe_ratio": pe_ratio,
                                "dividend_yield": dividend_yield,
                                "suggested_amount": suggested_amount,
                                "allocation_percentage": suggested_allocation,
                                "investment_rationale": "quality_large_cap"
                            }
                        )
                        insights.append(insight)
                
                except Exception as e:
                    logger.error(f"Error processing stock {symbol}: {e}")
                    continue
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error generating stock recommendations: {e}")
            self.db.rollback()
        
        return insights
    
    def _suggest_dollar_cost_averaging(
        self, 
        user_id: int, 
        profile: UserFinancialProfile, 
        investable_amount: float
    ) -> List[Dict[str, Any]]:
        """Suggest dollar-cost averaging strategy"""
        insights = []
        
        try:
            if investable_amount < 100:
                return insights
            
            # Suggest monthly investment amount
            monthly_investment = min(investable_amount, profile.monthly_income_avg * 0.1)  # Max 10% of income
            
            insight = self.create_insight(
                user_id=user_id,
                insight_type="investment",
                title=f"Start dollar-cost averaging with ${monthly_investment:.0f}/month",
                description=f"Instead of investing a lump sum, consider investing ${monthly_investment:.0f} monthly into your chosen investments. This reduces timing risk and builds discipline.",
                priority="medium",
                confidence_score=0.9,
                insight_metadata={
                    "monthly_investment_amount": monthly_investment,
                    "strategy": "dollar_cost_averaging",
                    "benefits": [
                        "Reduces timing risk",
                        "Builds investing discipline",
                        "Smooths market volatility",
                        "Automates wealth building"
                    ],
                    "recommended_duration": "indefinite"
                }
            )
            insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error suggesting dollar-cost averaging: {e}")
        
        return insights
    
    def get_market_insights(self) -> Dict[str, Any]:
        """Get current market insights and opportunities"""
        try:
            # Get market data for major indices
            spy = yf.Ticker("SPY")
            qqq = yf.Ticker("QQQ")
            
            spy_info = spy.info
            qqq_info = qqq.info
            
            # Simple market sentiment analysis
            spy_52w_high = spy_info.get('fiftyTwoWeekHigh', 0)
            spy_current = spy_info.get('currentPrice', spy_info.get('regularMarketPrice', 0))
            
            market_position = (spy_current / spy_52w_high) if spy_52w_high > 0 else 0
            
            if market_position > 0.95:
                market_sentiment = "Near highs - consider gradual entry"
            elif market_position < 0.85:
                market_sentiment = "Potential buying opportunity"
            else:
                market_sentiment = "Neutral market conditions"
            
            return {
                "spy_price": spy_current,
                "spy_52w_high": spy_52w_high,
                "market_position_percent": market_position * 100,
                "market_sentiment": market_sentiment,
                "recommended_strategy": "dollar_cost_averaging" if market_position > 0.9 else "gradual_investment",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market insights: {e}")
            return {"error": "Unable to fetch market data"}
    
    def get_investment_summary(self, user_id: int) -> Dict[str, Any]:
        """Get investment summary and recommendations"""
        try:
            profile = self.get_or_create_financial_profile(user_id)
            
            # Get recent recommendations
            recent_recommendations = self.db.query(InvestmentRecommendation).filter(
                InvestmentRecommendation.user_id == user_id,
                InvestmentRecommendation.is_active == True,
                InvestmentRecommendation.created_at >= datetime.now() - timedelta(days=30)
            ).all()
            
            total_recommended_allocation = sum(
                rec.suggested_allocation for rec in recent_recommendations if rec.suggested_allocation
            )
            
            return {
                "risk_tolerance": profile.risk_tolerance,
                "monthly_investable_amount": self._calculate_investable_surplus(
                    profile,
                    self.get_user_incomes(user_id, 90),
                    self.get_user_expenses(user_id, 90)
                ),
                "financial_health_score": profile.financial_health_score,
                "active_recommendations_count": len(recent_recommendations),
                "total_recommended_allocation": total_recommended_allocation,
                "emergency_fund_status": "adequate" if profile.monthly_expenses_avg * 6 <= profile.emergency_fund_target else "needs_attention",
                "investment_readiness": "ready" if self._calculate_investable_surplus(profile, self.get_user_incomes(user_id, 90), self.get_user_expenses(user_id, 90)) > 0 else "build_emergency_fund_first"
            }
            
        except Exception as e:
            logger.error(f"Error generating investment summary for user {user_id}: {e}")
            return {"error": "Unable to generate investment summary"}

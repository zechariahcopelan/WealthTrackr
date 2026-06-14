# backend/ai/services/subscription_optimizer.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.ai.services.base_analyzer import BaseFinancialAnalyzer
from backend.ai.models.ai_models import SubscriptionAlternative
import re
import logging

logger = logging.getLogger(__name__)

class SubscriptionOptimizer(BaseFinancialAnalyzer):
    """AI-powered subscription analysis and optimization"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self._initialize_subscription_database()
    
    def _initialize_subscription_database(self):
        """Initialize subscription alternatives database with common services"""
        try:
            # Check if data already exists
            existing_count = self.db.query(SubscriptionAlternative).count()
            if existing_count > 0:
                return
            
            # Streaming services
            streaming_alternatives = [
                {
                    "service_name": "Hulu (Basic)",
                    "category": "streaming",
                    "price_monthly": 7.99,
                    "alternative_to": "Netflix",
                    "savings_amount": 7.00,
                    "features": ["Ad-supported streaming", "TV shows", "Limited movies"],
                    "pros": ["Cheaper than Netflix", "Next-day TV episodes", "Good original content"],
                    "cons": ["Has advertisements", "Smaller movie library"],
                    "website_url": "https://hulu.com",
                    "free_trial_days": 30
                },
                {
                    "service_name": "Apple TV+",
                    "category": "streaming",
                    "price_monthly": 6.99,
                    "alternative_to": "Netflix",
                    "savings_amount": 8.00,
                    "features": ["Ad-free streaming", "Original content", "4K quality"],
                    "pros": ["High-quality originals", "Cheapest premium streaming", "No ads"],
                    "cons": ["Limited content library", "Newer service"],
                    "website_url": "https://tv.apple.com",
                    "free_trial_days": 7
                },
                {
                    "service_name": "Tubi",
                    "category": "streaming",
                    "price_monthly": 0.00,
                    "alternative_to": "Netflix",
                    "savings_amount": 15.49,
                    "features": ["Free streaming", "Movies and TV", "Ad-supported"],
                    "pros": ["Completely free", "Large content library", "No subscription needed"],
                    "cons": ["Has advertisements", "Older content", "Limited originals"],
                    "website_url": "https://tubitv.com"
                }
            ]
            
            # Fitness services
            fitness_alternatives = [
                {
                    "service_name": "Planet Fitness",
                    "category": "fitness",
                    "price_monthly": 10.00,
                    "alternative_to": "Traditional Gym",
                    "savings_amount": 40.00,
                    "features": ["Basic gym access", "Cardio equipment", "Weight machines"],
                    "pros": ["Very affordable", "No commitment", "Clean facilities"],
                    "cons": ["Limited equipment", "Crowded peak hours", "No personal training"],
                    "website_url": "https://planetfitness.com"
                },
                {
                    "service_name": "Nike Training Club",
                    "category": "fitness",
                    "price_monthly": 0.00,
                    "alternative_to": "Personal Trainer",
                    "savings_amount": 150.00,
                    "features": ["Free workout videos", "Training programs", "No equipment needed"],
                    "pros": ["Completely free", "Professional workouts", "At-home convenience"],
                    "cons": ["No personal feedback", "Requires self-motivation", "Limited equipment workouts"],
                    "website_url": "https://nike.com/ntc"
                },
                {
                    "service_name": "YouTube Fitness Channels",
                    "category": "fitness",
                    "price_monthly": 0.00,
                    "alternative_to": "Gym Membership",
                    "savings_amount": 50.00,
                    "features": ["Free workout videos", "Variety of trainers", "All fitness levels"],
                    "pros": ["Completely free", "Huge variety", "Can workout anywhere"],
                    "cons": ["Quality varies", "No structured programs", "Requires self-discipline"],
                    "website_url": "https://youtube.com"
                }
            ]
            
            # Music services
            music_alternatives = [
                {
                    "service_name": "Spotify (Free)",
                    "category": "music",
                    "price_monthly": 0.00,
                    "alternative_to": "Apple Music",
                    "savings_amount": 10.99,
                    "features": ["Free music streaming", "Playlists", "Podcast access"],
                    "pros": ["Completely free", "Large music library", "Good discovery"],
                    "cons": ["Has advertisements", "Limited skips", "No offline listening"],
                    "website_url": "https://spotify.com"
                },
                {
                    "service_name": "YouTube Music (Free)",
                    "category": "music",
                    "price_monthly": 0.00,
                    "alternative_to": "Spotify Premium",
                    "savings_amount": 9.99,
                    "features": ["Free music streaming", "Music videos", "Ad-supported"],
                    "pros": ["Free option available", "Music videos included", "Good recommendations"],
                    "cons": ["Has advertisements", "Limited features", "No background play on mobile"],
                    "website_url": "https://music.youtube.com"
                }
            ]
            
            # Phone/Internet services
            telecom_alternatives = [
                {
                    "service_name": "Mint Mobile",
                    "category": "phone",
                    "price_monthly": 15.00,
                    "alternative_to": "Verizon",
                    "savings_amount": 65.00,
                    "features": ["Unlimited talk/text", "4GB data", "T-Mobile network"],
                    "pros": ["Very affordable", "Uses major network", "No contracts"],
                    "cons": ["Prepaid only", "Customer service limited", "Data deprioritization"],
                    "website_url": "https://mintmobile.com"
                },
                {
                    "service_name": "Visible",
                    "category": "phone",
                    "price_monthly": 25.00,
                    "alternative_to": "AT&T",
                    "savings_amount": 55.00,
                    "features": ["Unlimited everything", "Verizon network", "Mobile hotspot"],
                    "pros": ["Truly unlimited", "Verizon network", "Simple pricing"],
                    "cons": ["May be slower during peak times", "Limited customer service"],
                    "website_url": "https://visible.com"
                }
            ]
            
            # Software/Productivity
            software_alternatives = [
                {
                    "service_name": "Google Workspace (Personal)",
                    "category": "productivity",
                    "price_monthly": 6.00,
                    "alternative_to": "Microsoft 365",
                    "savings_amount": 4.00,
                    "features": ["Gmail", "Google Drive", "Docs/Sheets", "100GB storage"],
                    "pros": ["Cheaper than Office 365", "Cloud-based", "Easy collaboration"],
                    "cons": ["Different interface", "Less advanced features", "Requires internet"],
                    "website_url": "https://workspace.google.com"
                },
                {
                    "service_name": "LibreOffice",
                    "category": "productivity",
                    "price_monthly": 0.00,
                    "alternative_to": "Microsoft Office",
                    "savings_amount": 10.00,
                    "features": ["Word processing", "Spreadsheets", "Presentations", "Open source"],
                    "pros": ["Completely free", "No subscription", "Compatible with Office files"],
                    "cons": ["Different interface", "No cloud features", "Less polished"],
                    "website_url": "https://libreoffice.org"
                }
            ]
            
            # Add all alternatives to database
            all_alternatives = streaming_alternatives + fitness_alternatives + music_alternatives + telecom_alternatives + software_alternatives
            
            for alt_data in all_alternatives:
                alternative = SubscriptionAlternative(**alt_data)
                self.db.add(alternative)
            
            self.db.commit()
            logger.info(f"Initialized subscription database with {len(all_alternatives)} alternatives")
            
        except Exception as e:
            logger.error(f"Error initializing subscription database: {e}")
            self.db.rollback()
    
    def analyze_subscription_opportunities(self, user_id: int) -> List[Dict[str, Any]]:
        """Analyze user expenses for subscription optimization opportunities"""
        insights = []
        
        try:
            expenses_df = self.get_user_expenses(user_id, days=180)  # 6 months for better pattern detection
            
            if expenses_df.empty:
                return insights
            
            # Detect recurring subscriptions
            subscription_insights = self._detect_subscriptions(user_id, expenses_df)
            insights.extend(subscription_insights)
            
            # Find bundling opportunities
            bundling_insights = self._find_bundling_opportunities(user_id, expenses_df)
            insights.extend(bundling_insights)
            
            # Detect unused subscriptions
            unused_insights = self._detect_unused_subscriptions(user_id, expenses_df)
            insights.extend(unused_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing subscription opportunities for user {user_id}: {e}")
            return []
    
    def _detect_subscriptions(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect recurring subscription-like expenses"""
        insights = []
        
        try:
            # Common subscription keywords
            subscription_keywords = [
                'netflix', 'spotify', 'hulu', 'disney', 'apple', 'amazon prime',
                'gym', 'fitness', 'planet fitness', 'subscription', 'monthly',
                'adobe', 'microsoft', 'office', 'google', 'dropbox', 'icloud',
                'verizon', 'att', 'tmobile', 'phone', 'internet', 'cable'
            ]
            
            # Group by description to find recurring patterns
            if 'description' in expenses_df.columns:
                description_groups = expenses_df.groupby('description').agg({
                    'amount': ['count', 'mean', 'std', 'sum'],
                    'date': ['min', 'max']
                }).reset_index()
                
                description_groups.columns = ['description', 'count', 'avg_amount', 'std_amount', 'total_amount', 'first_date', 'last_date']
                
                # Filter for potential subscriptions (recurring payments)
                potential_subscriptions = description_groups[
                    (description_groups['count'] >= 3) &  # At least 3 occurrences
                    (description_groups['std_amount'] < description_groups['avg_amount'] * 0.1)  # Low variance
                ]
                
                for _, sub in potential_subscriptions.iterrows():
                    description = sub['description'].lower()
                    monthly_cost = sub['avg_amount']
                    annual_cost = monthly_cost * 12
                    
                    # Check if it matches known subscription patterns
                    is_likely_subscription = any(keyword in description for keyword in subscription_keywords)
                    
                    if is_likely_subscription or monthly_cost > 5:  # Likely subscription or significant recurring cost
                        # Find alternatives
                        alternatives = self._find_alternatives_for_service(description, monthly_cost)
                        
                        if alternatives:
                            best_alternative = min(alternatives, key=lambda x: x.price_monthly)
                            potential_savings = (monthly_cost - best_alternative.price_monthly) * 12
                            
                            if potential_savings > 0:
                                insight = self.create_insight(
                                    user_id=user_id,
                                    insight_type="subscription",
                                    title=f"Save ${potential_savings:.2f}/year on {sub['description']}",
                                    description=f"You're paying ${monthly_cost:.2f}/month for {sub['description']}. Switch to {best_alternative.service_name} (${best_alternative.price_monthly:.2f}/month) and save ${potential_savings:.2f} annually.",
                                    priority="medium" if potential_savings > 50 else "low",
                                    potential_savings=potential_savings,
                                    confidence_score=0.8 if is_likely_subscription else 0.6,
                                    insight_metadata={
                                        "current_service": sub['description'],
                                        "current_monthly_cost": monthly_cost,
                                        "alternative_service": best_alternative.service_name,
                                        "alternative_monthly_cost": best_alternative.price_monthly,
                                        "annual_savings": potential_savings,
                                        "alternative_pros": best_alternative.pros,
                                        "alternative_cons": best_alternative.cons,
                                        "alternative_url": best_alternative.website_url
                                    }
                                )
                                insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error detecting subscriptions: {e}")
        
        return insights
    
    def _find_alternatives_for_service(self, description: str, current_price: float) -> List[SubscriptionAlternative]:
        """Find alternatives for a given service"""
        try:
            # Determine service category based on description
            category = self._categorize_service(description)
            
            if not category:
                return []
            
            # Get alternatives from database
            alternatives = self.db.query(SubscriptionAlternative).filter(
                SubscriptionAlternative.category == category,
                SubscriptionAlternative.price_monthly < current_price
            ).all()
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Error finding alternatives for {description}: {e}")
            return []
    
    def _categorize_service(self, description: str) -> Optional[str]:
        """Categorize a service based on its description"""
        description_lower = description.lower()
        
        streaming_keywords = ['netflix', 'hulu', 'disney', 'amazon prime', 'apple tv', 'streaming', 'video']
        fitness_keywords = ['gym', 'fitness', 'planet', 'workout', 'training']
        music_keywords = ['spotify', 'apple music', 'music', 'pandora']
        phone_keywords = ['verizon', 'att', 'tmobile', 'phone', 'mobile', 'cellular']
        productivity_keywords = ['microsoft', 'office', 'adobe', 'google', 'software', 'subscription']
        
        if any(keyword in description_lower for keyword in streaming_keywords):
            return "streaming"
        elif any(keyword in description_lower for keyword in fitness_keywords):
            return "fitness"
        elif any(keyword in description_lower for keyword in music_keywords):
            return "music"
        elif any(keyword in description_lower for keyword in phone_keywords):
            return "phone"
        elif any(keyword in description_lower for keyword in productivity_keywords):
            return "productivity"
        
        return None
    
    def _find_bundling_opportunities(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find opportunities to bundle services for savings"""
        insights = []
        
        try:
            # Look for multiple services in the same category
            if 'description' not in expenses_df.columns:
                return insights
            
            # Group recent expenses by category
            recent_df = expenses_df[expenses_df['date'] >= datetime.now() - timedelta(days=90)]
            
            streaming_services = []
            phone_services = []
            
            for _, expense in recent_df.iterrows():
                description = expense['description'].lower()
                
                if any(keyword in description for keyword in ['netflix', 'hulu', 'disney', 'streaming']):
                    streaming_services.append(expense)
                elif any(keyword in description for keyword in ['verizon', 'att', 'phone', 'mobile']):
                    phone_services.append(expense)
            
            # Suggest streaming bundle if multiple streaming services
            if len(streaming_services) >= 2:
                total_streaming_cost = sum(service['amount'] for service in streaming_services)
                
                if total_streaming_cost > 25:  # If spending more than $25/month on streaming
                    bundle_savings = total_streaming_cost * 0.2  # Assume 20% bundle savings
                    
                    insight = self.create_insight(
                        user_id=user_id,
                        insight_type="subscription",
                        title="Bundle streaming services for savings",
                        description=f"You're paying ${total_streaming_cost:.2f}/month across multiple streaming services. Consider bundling (like Disney+/Hulu bundle) to save approximately ${bundle_savings:.2f}/month.",
                        priority="medium",
                        potential_savings=bundle_savings * 12,
                        confidence_score=0.7,
                        insight_metadata={
                            "current_total_cost": total_streaming_cost,
                            "service_count": len(streaming_services),
                            "estimated_bundle_savings": bundle_savings
                        }
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error finding bundling opportunities: {e}")
        
        return insights
    
    def _detect_unused_subscriptions(self, user_id: int, expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potentially unused subscriptions based on spending patterns"""
        insights = []
        
        try:
            # Look for subscriptions that haven't had related spending
            # This is a simplified heuristic - in a real app, you'd track usage data
            
            if 'description' not in expenses_df.columns:
                return insights
            
            # Find gym memberships without other fitness-related expenses
            gym_expenses = expenses_df[
                expenses_df['description'].str.contains('gym|fitness', case=False, na=False)
            ]
            
            fitness_expenses = expenses_df[
                expenses_df['description'].str.contains('athletic|sports|workout|protein|supplement', case=False, na=False)
            ]
            
            if not gym_expenses.empty and fitness_expenses.empty:
                avg_gym_cost = gym_expenses['amount'].mean()
                annual_cost = avg_gym_cost * 12
                
                insight = self.create_insight(
                    user_id=user_id,
                    insight_type="subscription",
                    title="Potential unused gym membership detected",
                    description=f"You're paying ${avg_gym_cost:.2f}/month for gym membership but have no other fitness-related expenses. If you're not using it regularly, consider canceling to save ${annual_cost:.2f}/year.",
                    priority="medium",
                    potential_savings=annual_cost,
                    confidence_score=0.6,
                    insight_metadata={
                        "monthly_gym_cost": avg_gym_cost,
                        "annual_cost": annual_cost,
                        "suggestion": "Track gym visits or consider home workout alternatives"
                    }
                )
                insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error detecting unused subscriptions: {e}")
        
        return insights
    
    def get_subscription_summary(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive subscription analysis summary"""
        try:
            expenses_df = self.get_user_expenses(user_id, days=90)
            
            if expenses_df.empty:
                return {"total_subscription_cost": 0, "subscription_count": 0}
            
            # Estimate subscription expenses
            subscription_keywords = [
                'netflix', 'spotify', 'hulu', 'disney', 'subscription', 'monthly',
                'gym', 'fitness', 'adobe', 'microsoft', 'google', 'apple'
            ]
            
            if 'description' in expenses_df.columns:
                subscription_expenses = expenses_df[
                    expenses_df['description'].str.contains('|'.join(subscription_keywords), case=False, na=False)
                ]
                
                monthly_subscription_cost = subscription_expenses['amount'].sum() / 3  # 3-month average
                subscription_count = subscription_expenses['description'].nunique()
                
                return {
                    "monthly_subscription_cost": round(monthly_subscription_cost, 2),
                    "annual_subscription_cost": round(monthly_subscription_cost * 12, 2),
                    "subscription_count": subscription_count,
                    "largest_subscription": subscription_expenses.groupby('description')['amount'].mean().max() if not subscription_expenses.empty else 0
                }
            
            return {"total_subscription_cost": 0, "subscription_count": 0}
            
        except Exception as e:
            logger.error(f"Error generating subscription summary for user {user_id}: {e}")
            return {"error": "Unable to generate subscription summary"}

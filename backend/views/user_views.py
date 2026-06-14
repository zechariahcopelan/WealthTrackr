# /home/kenneth-copeland/Documents/WealthTrackr/backend/views/user_views.py

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction, IntegrityError
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, UpdateView

from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsOwner
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from backend.models.models import User
from backend.serializers.user_serializers import (
    UserSerializer, UpdateUserSerializer, UserProfileSerializer,
    UserPreferencesSerializer, SecuritySettingsSerializer,
    FinancialProfileSerializer, UserCompletionSerializer,
    BioUpdateSerializer, ProfilePictureSerializer
)
from backend.permissions import IsOwnerOrReadOnly, IsProfileOwner
from backend.utils.validators import validate_image_upload, validate_bio_content
from backend.utils.image_processing import process_profile_image
from backend.utils.analytics import track_user_event
from backend.utils.cache import cache_user_data, invalidate_user_cache
from backend.utils.notifications import send_profile_update_notification
from backend.tasks.celery_tasks import sync_user_data_across_services

logger = logging.getLogger(__name__)

# =====================================================
# USER PROFILE MANAGEMENT VIEWS
# =====================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    Comprehensive User ViewSet with all profile management endpoints
    Supports CRUD operations with enhanced security and validation
    """
    
    queryset = User.objects.select_related().prefetch_related(
        'financial_goals', 'notifications', 'user_sessions'
    )
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'updated_at', 'level', 'experience_points']
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.action in ['list', 'retrieve']:
            # Only return public profiles or own profile
            if self.request.user.is_staff:
                return self.queryset
            return self.queryset.filter(
                models.Q(id=self.request.user.id) | 
                models.Q(privacy_settings__profile_visibility='public')
            )
        return self.queryset.filter(id=self.request.user.id)

    def get_serializer_class(self):
        """Dynamic serializer selection based on action"""
        if self.action == 'update_profile':
            return UpdateUserSerializer
        elif self.action == 'preferences':
            return UserPreferencesSerializer
        elif self.action == 'security':
            return SecuritySettingsSerializer
        elif self.action == 'financial_profile':
            return FinancialProfileSerializer
        elif self.action == 'completion':
            return UserCompletionSerializer
        elif self.action == 'bio':
            return BioUpdateSerializer
        elif self.action == 'profile_picture':
            return ProfilePictureSerializer
        return super().get_serializer_class()

    @extend_schema(
        summary="Update existing user profile",
        description="Update user profile information with comprehensive validation",
        request=UpdateUserSerializer,
        responses={200: UserSerializer}
    )
    def update(self, request, *args, **kwargs):
        """
        PUT /api/users/:id
        Update existing user endpoint with full profile data
        """
        try:
            instance = self.get_object()
            
            # Ensure user can only update their own profile
            if instance.id != request.user.id and not request.user.is_staff:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate incoming data
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save with audit trail
            with transaction.atomic():
                updated_user = serializer.save(updated_at=datetime.now(timezone.utc))
                
                # Track analytics
                track_user_event(
                    user_id=updated_user.id,
                    event_type='profile_updated',
                    data={'fields_updated': list(request.data.keys())}
                )
                
                # Invalidate cache
                invalidate_user_cache(updated_user.id)
                
                # Send notification if email changed
                if 'email' in request.data and request.data['email'] != instance.email:
                    send_profile_update_notification(updated_user, 'email_changed')
                
                # Async task for cross-service sync
                sync_user_data_across_services.delay(updated_user.id)

            response_serializer = UserSerializer(updated_user, context={'request': request})
            
            logger.info(f"User profile updated: {updated_user.id}")
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            logger.warning(f"Validation error in user update: {e}")
            return Response(
                {'error': 'Validation failed', 'details': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in user update: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Update user bio",
        description="Update only the user's bio field with content validation",
        request=BioUpdateSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['patch'], url_path='bio')
    def bio(self, request, pk=None):
        """
        PATCH /api/users/:id/bio
        Update bio-specific endpoint with content validation
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            bio = request.data.get('bio', '')
            
            # Validate bio content
            if not validate_bio_content(bio):
                return Response(
                    {'error': 'Invalid bio content'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                user.bio = bio
                user.updated_at = datetime.now(timezone.utc)
                user.save(update_fields=['bio', 'updated_at'])
                
                track_user_event(
                    user_id=user.id,
                    event_type='bio_updated',
                    data={'bio_length': len(bio)}
                )

            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating bio: {e}")
            return Response(
                {'error': 'Failed to update bio'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Update profile picture",
        description="Upload and update user profile picture with image processing",
        request=ProfilePictureSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['patch'], url_path='profile-picture')
    def profile_picture(self, request, pk=None):
        """
        PATCH /api/users/:id/profile-picture
        Update profile picture with image processing and validation
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Handle both URL and file upload
            profile_pic_url = request.data.get('profile_pic_url')
            profile_pic_file = request.FILES.get('profile_picture')

            if profile_pic_file:
                # Validate uploaded file
                if not validate_image_upload(profile_pic_file):
                    return Response(
                        {'error': 'Invalid image file'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Process and save image
                processed_url = process_profile_image(profile_pic_file, user.id)
                profile_pic_url = processed_url

            elif not profile_pic_url:
                return Response(
                    {'error': 'Profile picture URL or file required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                user.profile_picture_url = profile_pic_url
                user.updated_at = datetime.now(timezone.utc)
                user.save(update_fields=['profile_picture_url', 'updated_at'])
                
                track_user_event(
                    user_id=user.id,
                    event_type='profile_picture_updated',
                    data={'upload_type': 'file' if profile_pic_file else 'url'}
                )

            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating profile picture: {e}")
            return Response(
                {'error': 'Failed to update profile picture'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Comprehensive profile update",
        description="Update complete user profile with all fields",
        request=UpdateUserSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['put'], url_path='profile')
    def update_profile(self, request, pk=None):
        """
        PUT /api/users/:id/profile
        Comprehensive profile update endpoint
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = UpdateUserSerializer(user, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                updated_user = serializer.save(updated_at=datetime.now(timezone.utc))
                
                # Calculate profile completion
                completion_data = calculate_profile_completion(updated_user)
                
                track_user_event(
                    user_id=updated_user.id,
                    event_type='comprehensive_profile_update',
                    data={
                        'completion_percentage': completion_data['completion_percentage'],
                        'fields_updated': list(request.data.keys())
                    }
                )
                
                # Award XP for profile completion milestones
                if completion_data['completion_percentage'] >= 100:
                    updated_user.add_experience_points(100, "Profile completed")
                elif completion_data['completion_percentage'] >= 75:
                    updated_user.add_experience_points(50, "Profile 75% complete")

            response_serializer = UserSerializer(updated_user, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in comprehensive profile update: {e}")
            return Response(
                {'error': 'Failed to update profile'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get profile completion status",
        description="Get user profile completion percentage and missing fields",
        responses={200: UserCompletionSerializer}
    )
    @action(detail=True, methods=['get'], url_path='completion')
    def completion(self, request, pk=None):
        """
        GET /api/users/:id/completion
        Get profile completion status with detailed breakdown
        """
        try:
            user = self.get_object()
            
            # Only allow users to see their own completion or staff
            if user.id != request.user.id and not request.user.is_staff:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            completion_data = calculate_profile_completion(user)
            
            # Add recommendations based on missing fields
            recommendations = generate_completion_recommendations(
                completion_data['missing_fields']
            )
            completion_data['recommendations'] = recommendations
            
            # Track analytics
            track_user_event(
                user_id=user.id,
                event_type='profile_completion_checked',
                data={'completion_percentage': completion_data['completion_percentage']}
            )

            return Response(completion_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting profile completion: {e}")
            return Response(
                {'error': 'Failed to get completion status'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =====================================================
# SECURITY & PREFERENCES VIEWS
# =====================================================

    @extend_schema(
        summary="Update security settings",
        description="Update user security preferences and authentication settings",
        request=SecuritySettingsSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['patch'], url_path='security')
    def security(self, request, pk=None):
        """
        PATCH /api/users/:id/security
        Update security settings with validation
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = SecuritySettingsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            security_data = serializer.validated_data

            with transaction.atomic():
                # Update security settings
                if 'two_factor_enabled' in security_data:
                    user.two_factor_enabled = security_data['two_factor_enabled']
                
                if 'biometric_enabled' in security_data:
                    user.biometric_enabled = security_data['biometric_enabled']
                
                if 'biometric_types' in security_data:
                    user.biometric_types = security_data['biometric_types']
                
                if 'login_notifications' in security_data:
                    user.notification_preferences['login_alerts'] = security_data['login_notifications']
                
                if 'session_timeout' in security_data:
                    user.app_preferences['session_timeout'] = security_data['session_timeout']

                user.updated_at = datetime.now(timezone.utc)
                user.save()
                
                track_user_event(
                    user_id=user.id,
                    event_type='security_settings_updated',
                    data=security_data
                )
                
                # Send security notification
                send_profile_update_notification(user, 'security_changed')

            response_serializer = UserSerializer(user, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating security settings: {e}")
            return Response(
                {'error': 'Failed to update security settings'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Update user preferences",
        description="Update notification, privacy, and app preferences",
        request=UserPreferencesSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['patch'], url_path='preferences')
    def preferences(self, request, pk=None):
        """
        PATCH /api/users/:id/preferences
        Update user preferences endpoint
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = UserPreferencesSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            preferences_data = serializer.validated_data

            with transaction.atomic():
                # Update notification preferences
                if 'notification_preferences' in preferences_data:
                    user.notification_preferences.update(
                        preferences_data['notification_preferences']
                    )
                
                # Update privacy settings
                if 'privacy_settings' in preferences_data:
                    user.privacy_settings.update(
                        preferences_data['privacy_settings']
                    )
                
                # Update app preferences
                if 'app_preferences' in preferences_data:
                    user.app_preferences.update(
                        preferences_data['app_preferences']
                    )
                
                # Update basic preferences
                for field in ['language', 'timezone', 'currency']:
                    if field in preferences_data:
                        setattr(user, field, preferences_data[field])

                user.updated_at = datetime.now(timezone.utc)
                user.save()
                
                track_user_event(
                    user_id=user.id,
                    event_type='preferences_updated',
                    data={'categories': list(preferences_data.keys())}
                )

            response_serializer = UserSerializer(user, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return Response(
                {'error': 'Failed to update preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =====================================================
# FINANCIAL PROFILE VIEWS
# =====================================================

    @extend_schema(
        summary="Update financial profile",
        description="Update user's financial information and investment preferences",
        request=FinancialProfileSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['patch'], url_path='financial-profile')
    def financial_profile(self, request, pk=None):
        """
        PATCH /api/users/:id/financial-profile
        Update financial profile information
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = FinancialProfileSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            financial_data = serializer.validated_data

            with transaction.atomic():
                # Update financial profile fields
                for field in ['monthly_income', 'risk_tolerance', 'investment_experience']:
                    if field in financial_data:
                        setattr(user, field, financial_data[field])
                
                # Update financial goals
                if 'financial_goals' in financial_data:
                    # Handle financial goals updates
                    goals_data = financial_data['financial_goals']
                    # You might want to create separate FinancialGoal objects
                    # For now, storing in JSON field
                    user.financial_goals = goals_data
                
                # Update subscription preferences if included
                if 'subscription_preferences' in financial_data:
                    user.subscription_preferences = financial_data['subscription_preferences']

                user.updated_at = datetime.now(timezone.utc)
                user.save()
                
                # Award XP for completing financial profile
                if all(field in financial_data for field in ['monthly_income', 'risk_tolerance', 'investment_experience']):
                    user.add_experience_points(75, "Financial profile completed")
                
                track_user_event(
                    user_id=user.id,
                    event_type='financial_profile_updated',
                    data={
                        'risk_tolerance': financial_data.get('risk_tolerance'),
                        'investment_experience': financial_data.get('investment_experience')
                    }
                )

            response_serializer = UserSerializer(user, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating financial profile: {e}")
            return Response(
                {'error': 'Failed to update financial profile'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =====================================================
# ADDITIONAL ENHANCED ENDPOINTS
# =====================================================

    @extend_schema(
        summary="Get user analytics",
        description="Get comprehensive user activity and engagement analytics",
        responses={200: 'User analytics data'}
    )
    @action(detail=True, methods=['get'], url_path='analytics')
    def analytics(self, request, pk=None):
        """
        GET /api/users/:id/analytics
        Get user analytics and engagement metrics
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id and not request.user.is_staff:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            analytics_data = {
                'profile_completion': calculate_profile_completion(user)['completion_percentage'],
                'engagement_score': calculate_engagement_score(user),
                'activity_streak': user.streak_days,
                'level': user.level,
                'experience_points': user.experience_points,
                'badges_earned': len(user.badges),
                'last_login': user.last_login,
                'account_age_days': (datetime.now(timezone.utc) - user.created_at).days,
                'feature_usage': get_feature_usage_stats(user.id),
                'goals_progress': get_goals_progress(user.id)
            }

            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return Response(
                {'error': 'Failed to get analytics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Export user data",
        description="Export all user data in requested format (GDPR compliance)",
        parameters=[
            OpenApiParameter('format', OpenApiTypes.STR, description='Export format (json, csv)')
        ],
        responses={200: 'Exported user data'}
    )
    @action(detail=True, methods=['post'], url_path='export')
    def export_data(self, request, pk=None):
        """
        POST /api/users/:id/export
        Export user data for GDPR compliance
        """
        try:
            user = self.get_object()
            
            if user.id != request.user.id:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            export_format = request.data.get('format', 'json')
            
            # Generate export data
            export_data = generate_user_export(user, export_format)
            
            track_user_event(
                user_id=user.id,
                event_type='data_exported',
                data={'format': export_format}
            )

            if export_format == 'json':
                return Response(export_data, status=status.HTTP_200_OK)
            else:
                # For CSV or other formats, return download URL
                return Response(
                    {'download_url': export_data['download_url']}, 
                    status=status.HTTP_200_OK
                )
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return Response(
                {'error': 'Failed to export data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def calculate_profile_completion(user: User) -> Dict[str, Any]:
    """Calculate profile completion percentage and missing fields"""
    
    required_fields = [
        'first_name', 'last_name', 'email', 'bio', 'profile_picture_url',
        'date_of_birth', 'location', 'occupation', 'phone_number'
    ]
    
    completed_fields = []
    missing_fields = []
    
    for field in required_fields:
        value = getattr(user, field, None)
        if value and str(value).strip():
            completed_fields.append(field)
        else:
            missing_fields.append(field)
    
    # Check financial profile completion
    financial_fields = ['monthly_income', 'risk_tolerance', 'investment_experience']
    financial_completed = sum(1 for field in financial_fields if getattr(user, field, None))
    
    # Check preferences completion
    prefs_completed = 1 if user.notification_preferences else 0
    
    total_fields = len(required_fields) + len(financial_fields) + 1
    completed_count = len(completed_fields) + financial_completed + prefs_completed
    
    completion_percentage = int((completed_count / total_fields) * 100)
    
    return {
        'completion_percentage': completion_percentage,
        'completed_fields': completed_fields,
        'missing_fields': missing_fields,
        'financial_profile_completion': int((financial_completed / len(financial_fields)) * 100),
        'total_fields': total_fields,
        'completed_count': completed_count
    }

def generate_completion_recommendations(missing_fields: List[str]) -> List[Dict[str, str]]:
    """Generate personalized recommendations based on missing fields"""
    
    recommendations = []
    field_recommendations = {
        'bio': {
            'title': 'Add a personal bio',
            'description': 'Tell others about yourself and your financial goals',
            'priority': 'medium'
        },
        'profile_picture_url': {
            'title': 'Upload a profile picture',
            'description': 'Add a profile picture to personalize your account',
            'priority': 'low'
        },
        'date_of_birth': {
            'title': 'Add your date of birth',
            'description': 'Help us provide age-appropriate financial advice',
            'priority': 'high'
        },
        'occupation': {
            'title': 'Add your occupation',
            'description': 'Get industry-specific financial insights',
            'priority': 'medium'
        },
        'location': {
            'title': 'Add your location',
            'description': 'Get location-based financial opportunities',
            'priority': 'medium'
        }
    }
    
    for field in missing_fields:
        if field in field_recommendations:
            recommendations.append(field_recommendations[field])
    
    return sorted(recommendations, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)

def calculate_engagement_score(user: User) -> int:
    """Calculate user engagement score based on various factors"""
    
    score = 0
    
    # Profile completion bonus
    completion = calculate_profile_completion(user)['completion_percentage']
    score += completion
    
    # Activity streak bonus
    score += min(user.streak_days * 2, 50)  # Max 50 points from streaks
    
    # Level progression bonus
    score += user.level * 5
    
    # Recent activity bonus
    if user.last_login and (datetime.now(timezone.utc) - user.last_login).days < 7:
        score += 20
    
    return min(score, 100)  # Cap at 100

def get_feature_usage_stats(user_id: str) -> Dict[str, int]:
    """Get user's feature usage statistics"""
    # This would typically query your analytics database
    # For now, returning mock data
    return {
        'transactions_created': 0,
        'budgets_created': 0,
        'goals_created': 0,
        'ai_insights_viewed': 0,
        'reports_generated': 0
    }

def get_goals_progress(user_id: str) -> Dict[str, Any]:
    """Get user's financial goals progress"""
    # This would query your financial goals system
    return {
        'total_goals': 0,
        'completed_goals': 0,
        'in_progress_goals': 0,
        'total_target_amount': 0,
        'total_saved_amount': 0
    }

def generate_user_export(user: User, format_type: str) -> Dict[str, Any]:
    """Generate comprehensive user data export"""
    
    user_data = {
        'personal_info': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': user.bio,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'location': user.location,
            'occupation': user.occupation,
            'company': user.company,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
        },
        'financial_profile': {
            'monthly_income': float(user.monthly_income) if user.monthly_income else None,
            'risk_tolerance': user.risk_tolerance,
            'investment_experience': user.investment_experience
        },
        'gamification': {
            'level': user.level,
            'experience_points': user.experience_points,
            'badges': user.badges,
            'streak_days': user.streak_days,
            'achievement_count': user.achievement_count
        },
        'preferences': {
            'notification_preferences': user.notification_preferences,
            'privacy_settings': user.privacy_settings,
            'app_preferences': user.app_preferences
        },
        'security': {
            'two_factor_enabled': user.two_factor_enabled,
            'biometric_enabled': user.biometric_enabled,
            'account_status': user.account_status
        }
    }
    
    if format_type == 'json':
        return user_data
    else:
        # For other formats, you'd generate a file and return download URL
        # This is a simplified example
        return {'download_url': f'/exports/{user.id}/data.{format_type}'}

# =====================================================
# ADDITIONAL API VIEWS
# =====================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_data(request, user_id):
    """
    GET /api/users/:id/dashboard
    Get comprehensive dashboard data for user
    """
    try:
        if request.user.id != user_id and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = User.objects.get(id=user_id)
        
        dashboard_data = {
            'user_profile': UserSerializer(user).data,
            'completion_status': calculate_profile_completion(user),
            'engagement_score': calculate_engagement_score(user),
            'recent_activity': get_recent_activity(user_id),
            'recommendations': generate_dashboard_recommendations(user),
            'quick_stats': {
                'level': user.level,
                'xp': user.experience_points,
                'streak': user.streak_days,
                'badges': len(user.badges)
            }
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return Response(
            {'error': 'Failed to get dashboard data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_recent_activity(user_id: str) -> List[Dict[str, Any]]:
    """Get user's recent activity"""
    # This would query your activity/audit log
    return []

def generate_dashboard_recommendations(user: User) -> List[Dict[str, Any]]:
    """Generate personalized dashboard recommendations"""
    recommendations = []
    
    # Profile completion recommendations
    completion_data = calculate_profile_completion(user)
    if completion_data['completion_percentage'] < 100:
        recommendations.append({
            'type': 'profile_completion',
            'title': 'Complete your profile',
            'description': f"You're {completion_data['completion_percentage']}% done!",
            'action_url': f'/profile/{user.id}/edit',
            'priority': 'medium'
        })
    
    # Engagement recommendations
    if user.streak_days == 0:
        recommendations.append({
            'type': 'engagement',
            'title': 'Start your daily streak',
            'description': 'Log in daily to build your streak and earn XP',
            'action_url': '/dashboard',
            'priority': 'high'
        })
    
    return recommendations

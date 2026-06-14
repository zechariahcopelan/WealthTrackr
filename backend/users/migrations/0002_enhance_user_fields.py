# /home/kenneth-copeland/Documents/WealthTrackr/backend/users/migrations/0002_enhance_user_fields.py

from django.db import migrations, models
import django.contrib.postgres.fields
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # Replace with your actual previous migration
    ]

    operations = [
        # =====================================================
        # PERSONAL INFORMATION FIELDS
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='display_name',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(max_length=20, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_picture_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='age',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(
                max_length=50, 
                choices=[
                    ('male', 'Male'),
                    ('female', 'Female'),
                    ('non_binary', 'Non-binary'),
                    ('prefer_not_to_say', 'Prefer not to say'),
                    ('other', 'Other'),
                ],
                blank=True, 
                null=True
            ),
        ),

        # =====================================================
        # LOCATION & LOCALIZATION
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='location',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(max_length=50, default='UTC'),
        ),
        migrations.AddField(
            model_name='user',
            name='language',
            field=models.CharField(max_length=10, default='en'),
        ),
        migrations.AddField(
            model_name='user',
            name='country',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='currency',
            field=models.CharField(max_length=10, default='USD'),
        ),

        # =====================================================
        # PROFESSIONAL INFORMATION
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='occupation',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='company',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),

        # =====================================================
        # ACCOUNT STATUS & ROLES
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='account_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('active', 'Active'),
                    ('inactive', 'Inactive'),
                    ('suspended', 'Suspended'),
                    ('pending_verification', 'Pending Verification'),
                    ('locked', 'Locked'),
                    ('deactivated', 'Deactivated'),
                ],
                default='active'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='user_role',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('user', 'Regular User'),
                    ('premium', 'Premium User'),
                    ('admin', 'Administrator'),
                    ('moderator', 'Moderator'),
                    ('support', 'Support Staff'),
                ],
                default='user'
            ),
        ),

        # =====================================================
        # EMAIL & PHONE VERIFICATION
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='email_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # =====================================================
        # SECURITY & AUTHENTICATION
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='two_factor_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='two_factor_methods',
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='biometric_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='biometric_types',
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='pin_enabled',
            field=models.BooleanField(default=False),
        ),

        # =====================================================
        # LOGIN TRACKING
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='last_login_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='last_login_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='last_login_device',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='login_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='failed_login_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='account_locked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # =====================================================
        # PASSWORD MANAGEMENT
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='password_changed_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='user',
            name='security_questions_set',
            field=models.BooleanField(default=False),
        ),

        # =====================================================
        # GAMIFICATION SYSTEM
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='level',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='user',
            name='experience_points',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='achievement_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='badges',
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='streak_days',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='last_activity_date',
            field=models.DateField(blank=True, null=True),
        ),

        # =====================================================
        # SOFT DELETE SUPPORT
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # =====================================================
        # FINANCIAL PROFILE FIELDS (Additional)
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='monthly_income',
            field=models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='risk_tolerance',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('conservative', 'Conservative'),
                    ('moderate', 'Moderate'),
                    ('aggressive', 'Aggressive'),
                ],
                blank=True,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='investment_experience',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('beginner', 'Beginner'),
                    ('intermediate', 'Intermediate'),
                    ('advanced', 'Advanced'),
                    ('expert', 'Expert'),
                ],
                blank=True,
                null=True
            ),
        ),

        # =====================================================
        # SUBSCRIPTION & PREMIUM FEATURES
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='subscription_plan',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('free', 'Free'),
                    ('basic', 'Basic'),
                    ('premium', 'Premium'),
                    ('enterprise', 'Enterprise'),
                ],
                default='free'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('active', 'Active'),
                    ('expired', 'Expired'),
                    ('cancelled', 'Cancelled'),
                    ('trial', 'Trial'),
                ],
                default='active'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # =====================================================
        # PREFERENCES (JSON FIELDS)
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='notification_preferences',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='privacy_settings',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='app_preferences',
            field=models.JSONField(default=dict, blank=True),
        ),

        # =====================================================
        # SYNC & METADATA
        # =====================================================
        migrations.AddField(
            model_name='user',
            name='last_sync_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='external_id',
            field=models.CharField(max_length=100, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='referred_by',
            field=models.ForeignKey(
                'self',
                on_delete=models.SET_NULL,
                blank=True,
                null=True,
                related_name='referrals'
            ),
        ),

        # =====================================================
        # DATABASE INDEXES FOR PERFORMANCE
        # =====================================================
        migrations.RunSQL([
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_verified ON users_user(is_verified);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_account_status ON users_user(account_status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login ON users_user(last_login_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users_user(created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_level ON users_user(level);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_experience_points ON users_user(experience_points);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_subscription_plan ON users_user(subscription_plan);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_subscription_expires ON users_user(subscription_expires_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_phone_number ON users_user(phone_number);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_external_id ON users_user(external_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_deleted_at ON users_user(deleted_at) WHERE deleted_at IS NOT NULL;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_streak_days ON users_user(streak_days);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_activity ON users_user(last_activity_date);",
        ], reverse_sql=[
            "DROP INDEX IF EXISTS idx_users_email_verified;",
            "DROP INDEX IF EXISTS idx_users_account_status;", 
            "DROP INDEX IF EXISTS idx_users_last_login;",
            "DROP INDEX IF EXISTS idx_users_created_at;",
            "DROP INDEX IF EXISTS idx_users_level;",
            "DROP INDEX IF EXISTS idx_users_experience_points;",
            "DROP INDEX IF EXISTS idx_users_subscription_plan;",
            "DROP INDEX IF EXISTS idx_users_subscription_expires;",
            "DROP INDEX IF EXISTS idx_users_phone_number;",
            "DROP INDEX IF EXISTS idx_users_external_id;",
            "DROP INDEX IF EXISTS idx_users_deleted_at;",
            "DROP INDEX IF EXISTS idx_users_streak_days;",
            "DROP INDEX IF EXISTS idx_users_last_activity;",
        ]),

        # =====================================================
        # CONSTRAINTS AND VALIDATIONS
        # =====================================================
        migrations.RunSQL([
            # Check constraint for valid age range
            "ALTER TABLE users_user ADD CONSTRAINT check_valid_age CHECK (age IS NULL OR (age >= 13 AND age <= 150));",
            
            # Check constraint for positive experience points
            "ALTER TABLE users_user ADD CONSTRAINT check_positive_xp CHECK (experience_points >= 0);",
            
            # Check constraint for positive level
            "ALTER TABLE users_user ADD CONSTRAINT check_positive_level CHECK (level >= 1);",
            
            # Check constraint for positive streak
            "ALTER TABLE users_user ADD CONSTRAINT check_positive_streak CHECK (streak_days >= 0);",
            
            # Check constraint for valid failed login attempts
            "ALTER TABLE users_user ADD CONSTRAINT check_failed_login_attempts CHECK (failed_login_attempts >= 0 AND failed_login_attempts <= 10);",
            
            # Check constraint for valid login count
            "ALTER TABLE users_user ADD CONSTRAINT check_login_count CHECK (login_count >= 0);",
            
        ], reverse_sql=[
            "ALTER TABLE users_user DROP CONSTRAINT IF EXISTS check_valid_age;",
            "ALTER TABLE users_user DROP CONSTRAINT IF EXISTS check_positive_xp;",
            "ALTER TABLE users_user DROP CONSTRAINT IF EXISTS check_positive_level;",
            "ALTER TABLE users_user DROP CONSTRAINT IF EXISTS check_positive_streak;",
            "ALTER TABLE users_user DROP CONSTRAINT IF EXISTS check_failed_login_attempts;",
            "ALTER TABLE users_user DROP CONSTRAINT IF EXISTS check_login_count;",
        ]),

        # =====================================================
        # INITIAL DATA POPULATION
        # =====================================================
        migrations.RunSQL([
            # Set initial notification preferences for existing users
            """
            UPDATE users_user 
            SET notification_preferences = '{
                "email_notifications": true,
                "push_notifications": true,
                "budget_alerts": true,
                "goal_reminders": true,
                "ai_insights": true,
                "security_alerts": true
            }'::jsonb
            WHERE notification_preferences = '{}';
            """,
            
            # Set initial privacy settings
            """
            UPDATE users_user 
            SET privacy_settings = '{
                "profile_visibility": "private",
                "data_sharing": false,
                "analytics_tracking": true,
                "personalized_ads": false
            }'::jsonb
            WHERE privacy_settings = '{}';
            """,
            
            # Set initial app preferences
            """
            UPDATE users_user 
            SET app_preferences = '{
                "theme": "system",
                "date_format": "MM/DD/YYYY",
                "time_format": "12",
                "currency_display": "symbol",
                "haptic_feedback": true
            }'::jsonb
            WHERE app_preferences = '{}';
            """,
            
            # Update password_changed_at for existing users
            """
            UPDATE users_user 
            SET password_changed_at = COALESCE(updated_at, created_at, NOW())
            WHERE password_changed_at IS NULL;
            """,
            
        ], reverse_sql=[
            # No reverse operations needed for data population
        ]),
    ]

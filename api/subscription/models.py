"""
Subscription Management Models
Carnatic Music Learning Platform
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
import json

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from config.database import Base

class SubscriptionTier(str, Enum):
    """Subscription tier enumeration"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    LIFETIME = "lifetime"

class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class SubscriptionStatus(str, Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    PENDING = "pending"

@dataclass
class FeatureAccess:
    """Feature access configuration for subscription tiers"""

    # Core features
    basic_exercises: bool = True
    advanced_exercises: bool = False
    real_time_feedback: bool = True

    # Recording features
    recording_limit: int = 10  # per month
    recording_duration: int = 300  # seconds
    audio_quality: str = "standard"  # standard, high, premium

    # Analysis features
    basic_analysis: bool = True
    advanced_analytics: bool = False
    progress_tracking: bool = True
    detailed_feedback: bool = False

    # Content access
    sarali_varisai: bool = True
    janta_varisai: bool = False
    alankaram_access: bool = False
    composition_library: int = 5  # number of compositions

    # Social features
    community_access: bool = False
    group_sessions: bool = False
    expert_feedback: bool = False

    # Technical features
    offline_mode: bool = False
    multi_device_sync: bool = False
    priority_support: bool = False

    # Limits and quotas
    daily_practice_time: int = 60  # minutes
    monthly_practice_time: int = 1800  # minutes (30 hours)
    concurrent_sessions: int = 1

class SubscriptionPlan(Base):
    """Subscription plan configuration"""

    __tablename__ = 'subscription_plans'

    id = Column(Integer, primary_key=True)

    # Plan identification
    name = Column(String(100), nullable=False)
    tier = Column(SQLEnum(SubscriptionTier), nullable=False, index=True)
    description = Column(Text)

    # Pricing
    price_monthly = Column(Float)  # USD
    price_yearly = Column(Float)   # USD with discount
    price_currency = Column(String(3), default='USD')

    # Regional pricing (JSON structure for different countries)
    regional_pricing = Column(JSON, default=dict)

    # Feature access
    features = Column(JSON, nullable=False)  # FeatureAccess as JSON

    # Plan settings
    trial_days = Column(Integer, default=0)
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Display settings
    display_order = Column(Integer, default=0)
    color_theme = Column(String(20), default='primary')

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_subscriptions = relationship("UserSubscription", back_populates="plan")

class UserSubscription(Base):
    """User subscription tracking"""

    __tablename__ = 'user_subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey('subscription_plans.id'), nullable=False)

    # Subscription period
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    # Trial information
    is_trial = Column(Boolean, default=False)
    trial_expires_at = Column(DateTime(timezone=True))

    # Payment tracking
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))

    # Subscription metadata
    subscription_data = Column(JSON, default=dict)  # Payment provider data, etc.
    cancellation_reason = Column(String(200))
    auto_renewal = Column(Boolean, default=True)

    # Usage tracking
    last_activity = Column(DateTime(timezone=True))
    usage_stats = Column(JSON, default=dict)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="user_subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")

class Payment(Base):
    """Payment transaction tracking"""

    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey('user_subscriptions.id'), nullable=False)

    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)

    # Payment method
    payment_method = Column(String(50))  # stripe, paypal, razorpay, etc.
    payment_method_id = Column(String(100))  # External payment method ID

    # External transaction tracking
    external_transaction_id = Column(String(200), index=True)
    provider_response = Column(JSON, default=dict)

    # Invoice information
    invoice_id = Column(String(100))
    invoice_url = Column(String(500))
    receipt_url = Column(String(500))

    # Billing period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))

    # Transaction metadata
    transaction_fee = Column(Float, default=0.0)
    net_amount = Column(Float)  # amount - transaction_fee

    # Refund information
    refund_amount = Column(Float, default=0.0)
    refund_reason = Column(String(200))
    refunded_at = Column(DateTime(timezone=True))

    # Timestamps
    attempted_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscription = relationship("UserSubscription", back_populates="payments")

class UsageRecord(Base):
    """Usage tracking for quota management"""

    __tablename__ = 'usage_records'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey('user_subscriptions.id'), nullable=False)

    # Usage tracking
    record_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    usage_type = Column(String(50), nullable=False, index=True)  # practice_time, recording, exercise, etc.

    # Usage metrics
    quantity = Column(Float, default=1.0)  # Amount used
    duration = Column(Integer, default=0)  # Duration in seconds

    # Additional context
    resource_id = Column(Integer)  # Exercise ID, Recording ID, etc.
    metadata = Column(JSON, default=dict)

    # Aggregation helpers
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    day = Column(Integer, index=True)

    # Relationships
    subscription = relationship("UserSubscription", back_populates="usage_records")

class Coupon(Base):
    """Discount coupon system"""

    __tablename__ = 'coupons'

    id = Column(Integer, primary_key=True)

    # Coupon identification
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200))
    description = Column(Text)

    # Discount settings
    discount_type = Column(String(20), default='percentage')  # percentage, fixed
    discount_value = Column(Float, nullable=False)  # 20 for 20% or 20 for $20
    max_discount_amount = Column(Float)  # Maximum discount for percentage coupons

    # Usage limits
    usage_limit = Column(Integer)  # Total usage limit
    usage_limit_per_user = Column(Integer, default=1)
    current_usage = Column(Integer, default=0)

    # Validity
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))

    # Applicable plans
    applicable_plans = Column(JSON, default=list)  # List of plan IDs
    min_amount = Column(Float)  # Minimum order amount

    # First-time user only
    new_users_only = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class CouponUsage(Base):
    """Coupon usage tracking"""

    __tablename__ = 'coupon_usage'

    id = Column(Integer, primary_key=True)

    # Usage tracking
    coupon_id = Column(Integer, ForeignKey('coupons.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey('payments.id'))

    # Discount applied
    discount_amount = Column(Float, nullable=False)
    original_amount = Column(Float, nullable=False)
    final_amount = Column(Float, nullable=False)

    # Timestamps
    used_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    coupon = relationship("Coupon")

# Predefined subscription plans
SUBSCRIPTION_PLANS = {
    SubscriptionTier.FREE: {
        'name': 'Free Tier',
        'description': 'Perfect for beginners exploring Carnatic music',
        'price_monthly': 0,
        'price_yearly': 0,
        'features': FeatureAccess(
            basic_exercises=True,
            advanced_exercises=False,
            recording_limit=5,
            recording_duration=60,
            composition_library=2,
            daily_practice_time=30,
            monthly_practice_time=900
        ).__dict__,
        'trial_days': 0,
        'color_theme': 'gray'
    },
    SubscriptionTier.BASIC: {
        'name': 'Basic Plan',
        'description': 'Essential features for regular practice',
        'price_monthly': 9.99,
        'price_yearly': 99.99,  # 2 months free
        'features': FeatureAccess(
            basic_exercises=True,
            advanced_exercises=True,
            recording_limit=50,
            recording_duration=300,
            composition_library=20,
            detailed_feedback=True,
            sarali_varisai=True,
            janta_varisai=True,
            daily_practice_time=120,
            monthly_practice_time=3600,
            multi_device_sync=True
        ).__dict__,
        'trial_days': 14,
        'color_theme': 'blue'
    },
    SubscriptionTier.PREMIUM: {
        'name': 'Premium Plan',
        'description': 'Advanced features for serious learners',
        'price_monthly': 19.99,
        'price_yearly': 199.99,  # 2 months free
        'features': FeatureAccess(
            basic_exercises=True,
            advanced_exercises=True,
            recording_limit=200,
            recording_duration=600,
            audio_quality="high",
            advanced_analytics=True,
            detailed_feedback=True,
            sarali_varisai=True,
            janta_varisai=True,
            alankaram_access=True,
            composition_library=100,
            community_access=True,
            group_sessions=True,
            offline_mode=True,
            multi_device_sync=True,
            concurrent_sessions=3,
            daily_practice_time=240,
            monthly_practice_time=7200
        ).__dict__,
        'trial_days': 14,
        'is_popular': True,
        'color_theme': 'orange'
    },
    SubscriptionTier.PROFESSIONAL: {
        'name': 'Professional Plan',
        'description': 'Complete access for teachers and professionals',
        'price_monthly': 39.99,
        'price_yearly': 399.99,  # 2 months free
        'features': FeatureAccess(
            basic_exercises=True,
            advanced_exercises=True,
            recording_limit=-1,  # Unlimited
            recording_duration=1800,
            audio_quality="premium",
            advanced_analytics=True,
            detailed_feedback=True,
            sarali_varisai=True,
            janta_varisai=True,
            alankaram_access=True,
            composition_library=-1,  # Unlimited
            community_access=True,
            group_sessions=True,
            expert_feedback=True,
            offline_mode=True,
            multi_device_sync=True,
            priority_support=True,
            concurrent_sessions=10,
            daily_practice_time=-1,  # Unlimited
            monthly_practice_time=-1  # Unlimited
        ).__dict__,
        'trial_days': 30,
        'color_theme': 'purple'
    },
    SubscriptionTier.LIFETIME: {
        'name': 'Lifetime Access',
        'description': 'One-time payment for lifetime access',
        'price_monthly': None,
        'price_yearly': 999.99,
        'features': FeatureAccess(
            basic_exercises=True,
            advanced_exercises=True,
            recording_limit=-1,
            recording_duration=1800,
            audio_quality="premium",
            advanced_analytics=True,
            detailed_feedback=True,
            sarali_varisai=True,
            janta_varisai=True,
            alankaram_access=True,
            composition_library=-1,
            community_access=True,
            group_sessions=True,
            expert_feedback=True,
            offline_mode=True,
            multi_device_sync=True,
            priority_support=True,
            concurrent_sessions=10,
            daily_practice_time=-1,
            monthly_practice_time=-1
        ).__dict__,
        'trial_days': 0,
        'color_theme': 'gold'
    }
}
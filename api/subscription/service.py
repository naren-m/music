"""
Subscription Management Service
Carnatic Music Learning Platform
"""

import os
import stripe
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import asdict

from flask import current_app
from config.database import get_db_session, User
from .models import (
    SubscriptionPlan, UserSubscription, Payment, UsageRecord,
    Coupon, CouponUsage, SubscriptionTier, PaymentStatus,
    SubscriptionStatus, FeatureAccess, SUBSCRIPTION_PLANS
)

class SubscriptionService:
    """Comprehensive subscription management service"""

    def __init__(self):
        # Initialize payment providers
        self.stripe_api_key = os.getenv('STRIPE_SECRET_KEY')
        if self.stripe_api_key:
            stripe.api_key = self.stripe_api_key

        # Regional pricing (example for India)
        self.regional_pricing = {
            'USD': {'multiplier': 1.0, 'currency': 'USD'},
            'INR': {'multiplier': 82.0, 'currency': 'INR'},  # Approximate rate
            'EUR': {'multiplier': 0.85, 'currency': 'EUR'},
            'GBP': {'multiplier': 0.73, 'currency': 'GBP'}
        }

    def initialize_plans(self) -> None:
        """Initialize subscription plans in database"""
        with get_db_session() as session:
            for tier, plan_data in SUBSCRIPTION_PLANS.items():
                existing_plan = session.query(SubscriptionPlan).filter_by(
                    tier=tier, name=plan_data['name']
                ).first()

                if not existing_plan:
                    plan = SubscriptionPlan(
                        tier=tier,
                        **plan_data,
                        regional_pricing=self._calculate_regional_pricing(
                            plan_data.get('price_monthly'),
                            plan_data.get('price_yearly')
                        )
                    )
                    session.add(plan)

            session.commit()

    def _calculate_regional_pricing(self, monthly_price: Optional[float],
                                  yearly_price: Optional[float]) -> Dict[str, Any]:
        """Calculate regional pricing for different currencies"""
        regional_pricing = {}

        for region, config in self.regional_pricing.items():
            regional_pricing[region] = {
                'currency': config['currency'],
                'monthly_price': round(monthly_price * config['multiplier'], 2) if monthly_price else None,
                'yearly_price': round(yearly_price * config['multiplier'], 2) if yearly_price else None
            }

        return regional_pricing

    def get_available_plans(self, region: str = 'USD') -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        with get_db_session() as session:
            plans = session.query(SubscriptionPlan).filter_by(
                is_active=True
            ).order_by(SubscriptionPlan.display_order).all()

            result = []
            for plan in plans:
                plan_data = {
                    'id': plan.id,
                    'name': plan.name,
                    'tier': plan.tier,
                    'description': plan.description,
                    'features': plan.features,
                    'trial_days': plan.trial_days,
                    'is_popular': plan.is_popular,
                    'color_theme': plan.color_theme
                }

                # Add regional pricing
                if region in plan.regional_pricing:
                    regional = plan.regional_pricing[region]
                    plan_data.update({
                        'currency': regional['currency'],
                        'price_monthly': regional['monthly_price'],
                        'price_yearly': regional['yearly_price']
                    })
                else:
                    # Fallback to USD
                    plan_data.update({
                        'currency': 'USD',
                        'price_monthly': plan.price_monthly,
                        'price_yearly': plan.price_yearly
                    })

                result.append(plan_data)

            return result

    def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get current user subscription"""
        with get_db_session() as session:
            subscription = session.query(UserSubscription).filter_by(
                user_id=user_id,
                status=SubscriptionStatus.ACTIVE
            ).first()

            if not subscription:
                # Return free tier as default
                return self._get_free_tier_subscription(user_id)

            return {
                'id': subscription.id,
                'plan': {
                    'id': subscription.plan.id,
                    'name': subscription.plan.name,
                    'tier': subscription.plan.tier,
                    'features': subscription.plan.features
                },
                'status': subscription.status,
                'started_at': subscription.started_at.isoformat(),
                'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                'is_trial': subscription.is_trial,
                'trial_expires_at': subscription.trial_expires_at.isoformat() if subscription.trial_expires_at else None,
                'auto_renewal': subscription.auto_renewal,
                'usage_stats': subscription.usage_stats
            }

    def _get_free_tier_subscription(self, user_id: int) -> Dict[str, Any]:
        """Get free tier subscription data"""
        return {
            'id': None,
            'plan': {
                'id': None,
                'name': 'Free Tier',
                'tier': SubscriptionTier.FREE,
                'features': SUBSCRIPTION_PLANS[SubscriptionTier.FREE]['features']
            },
            'status': SubscriptionStatus.ACTIVE,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': None,
            'is_trial': False,
            'trial_expires_at': None,
            'auto_renewal': False,
            'usage_stats': {}
        }

    def create_subscription(self, user_id: int, plan_id: int,
                          payment_method: str = 'stripe',
                          billing_cycle: str = 'monthly') -> Dict[str, Any]:
        """Create new subscription"""
        try:
            with get_db_session() as session:
                # Get user and plan
                user = session.query(User).filter_by(id=user_id).first()
                plan = session.query(SubscriptionPlan).filter_by(id=plan_id).first()

                if not user or not plan:
                    return {'success': False, 'error': 'User or plan not found'}

                # Check for existing active subscription
                existing = session.query(UserSubscription).filter_by(
                    user_id=user_id,
                    status=SubscriptionStatus.ACTIVE
                ).first()

                if existing and existing.plan.tier != SubscriptionTier.FREE:
                    return {'success': False, 'error': 'User already has an active subscription'}

                # Calculate dates
                start_date = datetime.now(timezone.utc)
                trial_end = None
                subscription_end = None

                if plan.trial_days > 0:
                    trial_end = start_date + timedelta(days=plan.trial_days)

                # Calculate subscription end date
                if billing_cycle == 'yearly':
                    subscription_end = start_date + timedelta(days=365)
                elif billing_cycle == 'monthly':
                    subscription_end = start_date + timedelta(days=30)

                # Create subscription
                subscription = UserSubscription(
                    user_id=user_id,
                    plan_id=plan_id,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=start_date,
                    expires_at=subscription_end,
                    is_trial=plan.trial_days > 0,
                    trial_expires_at=trial_end,
                    current_period_start=start_date,
                    current_period_end=trial_end if trial_end else subscription_end,
                    auto_renewal=True
                )

                session.add(subscription)

                # Cancel existing subscription if it's free
                if existing:
                    existing.status = SubscriptionStatus.CANCELLED
                    existing.cancelled_at = start_date

                session.flush()

                # Create payment if not trial
                payment_result = None
                if plan.trial_days == 0 or not trial_end:
                    amount = plan.price_yearly if billing_cycle == 'yearly' else plan.price_monthly

                    if amount and amount > 0:
                        payment_result = self._create_payment(
                            user_id, subscription.id, amount,
                            payment_method, billing_cycle
                        )

                        if not payment_result['success']:
                            session.rollback()
                            return payment_result

                session.commit()

                return {
                    'success': True,
                    'subscription': {
                        'id': subscription.id,
                        'plan_name': plan.name,
                        'status': subscription.status,
                        'is_trial': subscription.is_trial,
                        'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None
                    },
                    'payment': payment_result
                }

        except Exception as e:
            current_app.logger.error(f"Create subscription error: {e}")
            return {'success': False, 'error': str(e)}

    def _create_payment(self, user_id: int, subscription_id: int,
                       amount: float, payment_method: str,
                       billing_cycle: str) -> Dict[str, Any]:
        """Create payment record and process payment"""
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(id=user_id).first()

                # Calculate period
                period_start = datetime.now(timezone.utc)
                period_end = period_start + (
                    timedelta(days=365) if billing_cycle == 'yearly'
                    else timedelta(days=30)
                )

                # Create payment record
                payment = Payment(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    amount=amount,
                    currency='USD',  # TODO: Support multiple currencies
                    status=PaymentStatus.PENDING,
                    payment_method=payment_method,
                    period_start=period_start,
                    period_end=period_end,
                    net_amount=amount  # TODO: Calculate fees
                )

                session.add(payment)
                session.flush()

                # Process payment based on method
                if payment_method == 'stripe' and self.stripe_api_key:
                    stripe_result = self._process_stripe_payment(user, payment, amount)

                    if stripe_result['success']:
                        payment.status = PaymentStatus.COMPLETED
                        payment.external_transaction_id = stripe_result['transaction_id']
                        payment.provider_response = stripe_result['response']
                        payment.completed_at = datetime.now(timezone.utc)
                    else:
                        payment.status = PaymentStatus.FAILED
                        payment.failed_at = datetime.now(timezone.utc)
                        payment.provider_response = stripe_result

                else:
                    # Mock payment for development
                    payment.status = PaymentStatus.COMPLETED
                    payment.completed_at = datetime.now(timezone.utc)
                    stripe_result = {'success': True, 'transaction_id': 'mock_payment'}

                session.commit()

                return {
                    'success': stripe_result['success'],
                    'payment_id': payment.id,
                    'transaction_id': payment.external_transaction_id,
                    'amount': payment.amount,
                    'currency': payment.currency
                }

        except Exception as e:
            current_app.logger.error(f"Payment creation error: {e}")
            return {'success': False, 'error': str(e)}

    def _process_stripe_payment(self, user: User, payment: Payment,
                               amount: float) -> Dict[str, Any]:
        """Process payment via Stripe"""
        try:
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe uses cents
                currency='usd',
                automatic_payment_methods={'enabled': True},
                metadata={
                    'user_id': str(user.id),
                    'payment_id': str(payment.id),
                    'email': user.email
                }
            )

            return {
                'success': True,
                'transaction_id': intent.id,
                'client_secret': intent.client_secret,
                'response': {
                    'intent_id': intent.id,
                    'status': intent.status
                }
            }

        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }

    def cancel_subscription(self, user_id: int, reason: str = None) -> Dict[str, Any]:
        """Cancel user subscription"""
        try:
            with get_db_session() as session:
                subscription = session.query(UserSubscription).filter_by(
                    user_id=user_id,
                    status=SubscriptionStatus.ACTIVE
                ).first()

                if not subscription:
                    return {'success': False, 'error': 'No active subscription found'}

                # Update subscription
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.now(timezone.utc)
                subscription.auto_renewal = False
                subscription.cancellation_reason = reason

                session.commit()

                return {
                    'success': True,
                    'message': 'Subscription cancelled successfully',
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None
                }

        except Exception as e:
            current_app.logger.error(f"Cancel subscription error: {e}")
            return {'success': False, 'error': str(e)}

    def check_feature_access(self, user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        subscription = self.get_user_subscription(user_id)
        features = subscription['plan']['features']

        return features.get(feature, False)

    def get_usage_limits(self, user_id: int) -> Dict[str, Any]:
        """Get current usage limits for user"""
        subscription = self.get_user_subscription(user_id)
        features = subscription['plan']['features']

        return {
            'recording_limit': features.get('recording_limit', 0),
            'recording_duration': features.get('recording_duration', 0),
            'daily_practice_time': features.get('daily_practice_time', 0),
            'monthly_practice_time': features.get('monthly_practice_time', 0),
            'composition_library': features.get('composition_library', 0),
            'concurrent_sessions': features.get('concurrent_sessions', 1)
        }

    def track_usage(self, user_id: int, usage_type: str,
                   quantity: float = 1.0, duration: int = 0,
                   resource_id: int = None) -> None:
        """Track user usage for quota management"""
        try:
            with get_db_session() as session:
                subscription = session.query(UserSubscription).filter_by(
                    user_id=user_id,
                    status=SubscriptionStatus.ACTIVE
                ).first()

                if subscription:
                    now = datetime.now(timezone.utc)

                    usage_record = UsageRecord(
                        user_id=user_id,
                        subscription_id=subscription.id,
                        record_date=now,
                        usage_type=usage_type,
                        quantity=quantity,
                        duration=duration,
                        resource_id=resource_id,
                        year=now.year,
                        month=now.month,
                        day=now.day
                    )

                    session.add(usage_record)

                    # Update subscription usage stats
                    stats = subscription.usage_stats or {}
                    current_month = f"{now.year}-{now.month:02d}"

                    if current_month not in stats:
                        stats[current_month] = {}

                    if usage_type not in stats[current_month]:
                        stats[current_month][usage_type] = 0

                    stats[current_month][usage_type] += quantity
                    subscription.usage_stats = stats
                    subscription.last_activity = now

                    session.commit()

        except Exception as e:
            current_app.logger.error(f"Track usage error: {e}")

    def get_usage_statistics(self, user_id: int, period: str = 'current_month') -> Dict[str, Any]:
        """Get usage statistics for user"""
        try:
            with get_db_session() as session:
                now = datetime.now(timezone.utc)

                # Define date range based on period
                if period == 'current_month':
                    start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_date = now
                elif period == 'last_30_days':
                    start_date = now - timedelta(days=30)
                    end_date = now
                else:
                    start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_date = now

                # Query usage records
                usage_records = session.query(UsageRecord).filter(
                    UsageRecord.user_id == user_id,
                    UsageRecord.record_date >= start_date,
                    UsageRecord.record_date <= end_date
                ).all()

                # Aggregate usage by type
                usage_stats = {}
                for record in usage_records:
                    usage_type = record.usage_type

                    if usage_type not in usage_stats:
                        usage_stats[usage_type] = {
                            'count': 0,
                            'total_quantity': 0.0,
                            'total_duration': 0
                        }

                    usage_stats[usage_type]['count'] += 1
                    usage_stats[usage_type]['total_quantity'] += record.quantity
                    usage_stats[usage_type]['total_duration'] += record.duration

                return {
                    'period': period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'usage_stats': usage_stats,
                    'limits': self.get_usage_limits(user_id)
                }

        except Exception as e:
            current_app.logger.error(f"Get usage statistics error: {e}")
            return {}

    def validate_coupon(self, coupon_code: str, user_id: int,
                       plan_id: int) -> Dict[str, Any]:
        """Validate and apply coupon"""
        try:
            with get_db_session() as session:
                coupon = session.query(Coupon).filter_by(
                    code=coupon_code.upper(),
                    is_active=True
                ).first()

                if not coupon:
                    return {'valid': False, 'error': 'Invalid coupon code'}

                now = datetime.now(timezone.utc)

                # Check expiry
                if coupon.expires_at and now > coupon.expires_at:
                    return {'valid': False, 'error': 'Coupon has expired'}

                # Check start date
                if coupon.starts_at and now < coupon.starts_at:
                    return {'valid': False, 'error': 'Coupon is not yet active'}

                # Check usage limit
                if coupon.usage_limit and coupon.current_usage >= coupon.usage_limit:
                    return {'valid': False, 'error': 'Coupon usage limit reached'}

                # Check user usage limit
                if coupon.usage_limit_per_user:
                    user_usage = session.query(CouponUsage).filter_by(
                        coupon_id=coupon.id,
                        user_id=user_id
                    ).count()

                    if user_usage >= coupon.usage_limit_per_user:
                        return {'valid': False, 'error': 'Coupon usage limit per user reached'}

                # Check applicable plans
                if coupon.applicable_plans and plan_id not in coupon.applicable_plans:
                    return {'valid': False, 'error': 'Coupon not applicable to this plan'}

                # Check new users only
                if coupon.new_users_only:
                    existing_subscription = session.query(UserSubscription).filter_by(
                        user_id=user_id
                    ).first()

                    if existing_subscription:
                        return {'valid': False, 'error': 'Coupon is only for new users'}

                return {
                    'valid': True,
                    'coupon': {
                        'id': coupon.id,
                        'code': coupon.code,
                        'name': coupon.name,
                        'discount_type': coupon.discount_type,
                        'discount_value': coupon.discount_value,
                        'max_discount_amount': coupon.max_discount_amount
                    }
                }

        except Exception as e:
            current_app.logger.error(f"Validate coupon error: {e}")
            return {'valid': False, 'error': 'Error validating coupon'}

    def calculate_discount(self, amount: float, coupon_data: Dict[str, Any]) -> float:
        """Calculate discount amount"""
        discount_type = coupon_data['discount_type']
        discount_value = coupon_data['discount_value']
        max_discount = coupon_data.get('max_discount_amount')

        if discount_type == 'percentage':
            discount = amount * (discount_value / 100)
            if max_discount:
                discount = min(discount, max_discount)
        else:  # fixed
            discount = min(discount_value, amount)

        return round(discount, 2)

# Initialize service
subscription_service = SubscriptionService()
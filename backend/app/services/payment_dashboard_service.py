"""
Payment Dashboard Service

Service layer for payment system analytics and reporting.
Provides comprehensive metrics, trends, alerts, and recommendations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from ..models.billing.bank_accounts import BankAccount, BankAccountOwnerType
from ..models.billing.payments import Payment, PaymentMethodConstants
from ..models.billing.enums import PaymentStatus
from ..models.billing.gateways import Gateway


logger = logging.getLogger(__name__)


class PaymentDashboardService:
    """Service for payment system analytics and reporting."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_payment_overview(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive payment system overview.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            tenant_id: Tenant ID for scoping
            
        Returns:
            Payment system overview data
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        overview = {
            "bank_accounts": self.get_bank_account_metrics(),
            "payments": self.get_payment_metrics(start_date, end_date, tenant_id),
            "gateways": self.get_gateway_metrics(start_date, end_date, tenant_id),
            "trends": self.get_payment_trends(start_date, end_date, tenant_id),
            "alerts": self.get_payment_alerts(),
            "summary": {}
        }
        
        # Generate summary
        overview["summary"] = {
            "total_accounts": overview["bank_accounts"]["total_accounts"],
            "verified_accounts": overview["bank_accounts"]["verified_accounts"],
            "total_payments": overview["payments"]["total_payments"],
            "success_rate": overview["payments"]["success_rate"],
            "total_amount": overview["payments"]["total_amount"],
            "active_gateways": overview["gateways"]["active_gateways"],
            "alert_count": len(overview["alerts"])
        }
        
        return overview
    
    def get_bank_account_metrics(self) -> Dict[str, Any]:
        """Get bank account metrics."""
        total_accounts = self.db.query(BankAccount).count()
        active_accounts = self.db.query(BankAccount).filter(BankAccount.active == True).count()
        verified_accounts = self.db.query(BankAccount).filter(BankAccount.verified == True).count()
        platform_accounts = self.db.query(BankAccount).filter(
            BankAccount.owner_type == BankAccountOwnerType.PLATFORM
        ).count()
        reseller_accounts = self.db.query(BankAccount).filter(
            BankAccount.owner_type == BankAccountOwnerType.RESELLER
        ).count()
        
        verification_rate = (verified_accounts / total_accounts * 100) if total_accounts > 0 else 0
        
        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "verified_accounts": verified_accounts,
            "unverified_accounts": total_accounts - verified_accounts,
            "platform_accounts": platform_accounts,
            "reseller_accounts": reseller_accounts,
            "verification_rate": round(verification_rate, 2)
        }
    
    def get_payment_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get payment transaction metrics."""
        query = self.db.query(Payment).filter(
            Payment.created_at >= start_date,
            Payment.created_at <= end_date
        )
        
        if tenant_id:
            query = query.filter(Payment.tenant_id == tenant_id)
        
        total_payments = query.count()
        successful_payments = query.filter(Payment.status == PaymentStatus.COMPLETED).count()
        failed_payments = query.filter(Payment.status == PaymentStatus.FAILED).count()
        pending_payments = query.filter(Payment.status == PaymentStatus.PENDING).count()
        
        # Payment amounts
        total_amount_result = query.filter(Payment.status == PaymentStatus.COMPLETED).with_entities(
            func.coalesce(func.sum(Payment.amount), 0)
        ).scalar()
        total_amount = float(total_amount_result or 0)
        
        # Payment methods
        gateway_payments = query.filter(Payment.method == PaymentMethodConstants.GATEWAY).count()
        bank_transfer_payments = query.filter(Payment.method == PaymentMethodConstants.BANK_TRANSFER).count()
        cash_payments = query.filter(Payment.method == PaymentMethodConstants.CASH).count()
        
        # Success rate
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        # Average payment amount
        avg_amount = total_amount / successful_payments if successful_payments > 0 else 0
        
        return {
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "success_rate": round(success_rate, 2),
            "failure_rate": round((failed_payments / total_payments * 100) if total_payments > 0 else 0, 2),
            "total_amount": total_amount,
            "average_amount": round(avg_amount, 2),
            "payment_methods": {
                "gateway": gateway_payments,
                "bank_transfer": bank_transfer_payments,
                "cash": cash_payments
            }
        }
    
    def get_gateway_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get payment gateway metrics."""
        total_gateways = self.db.query(Gateway).count()
        active_gateways = self.db.query(Gateway).filter(Gateway.active == True).count()
        
        # Gateway usage
        gateway_usage_query = self.db.query(
            Gateway.name,
            func.count(Payment.id).label('payment_count'),
            func.coalesce(func.sum(Payment.amount), 0).label('total_amount')
        ).join(
            Payment, Payment.gateway_id == Gateway.id
        ).filter(
            Payment.created_at >= start_date,
            Payment.created_at <= end_date,
            Payment.status == PaymentStatus.COMPLETED
        )
        
        if tenant_id:
            gateway_usage_query = gateway_usage_query.filter(Payment.tenant_id == tenant_id)
        
        gateway_usage = gateway_usage_query.group_by(Gateway.name).all()
        
        return {
            "total_gateways": total_gateways,
            "active_gateways": active_gateways,
            "gateway_usage": [
                {
                    "name": usage.name,
                    "payment_count": usage.payment_count,
                    "total_amount": float(usage.total_amount)
                }
                for usage in gateway_usage
            ]
        }
    
    def get_payment_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get payment trends over time."""
        # Daily payment trends
        daily_trends_query = self.db.query(
            func.date(Payment.created_at).label('date'),
            func.count(Payment.id).label('payment_count'),
            func.coalesce(func.sum(Payment.amount), 0).label('total_amount'),
            func.count(Payment.id).filter(Payment.status == PaymentStatus.COMPLETED).label('successful_count'),
            func.count(Payment.id).filter(Payment.status == PaymentStatus.FAILED).label('failed_count')
        ).filter(
            Payment.created_at >= start_date,
            Payment.created_at <= end_date
        )
        
        if tenant_id:
            daily_trends_query = daily_trends_query.filter(Payment.tenant_id == tenant_id)
        
        daily_trends = daily_trends_query.group_by(func.date(Payment.created_at)).order_by(
            func.date(Payment.created_at)
        ).all()
        
        # Payment method trends
        method_trends_query = self.db.query(
            func.date(Payment.created_at).label('date'),
            Payment.method,
            func.count(Payment.id).label('count')
        ).filter(
            Payment.created_at >= start_date,
            Payment.created_at <= end_date
        )
        
        if tenant_id:
            method_trends_query = method_trends_query.filter(Payment.tenant_id == tenant_id)
        
        method_trends = method_trends_query.group_by(
            func.date(Payment.created_at), Payment.method
        ).order_by(func.date(Payment.created_at)).all()
        
        return {
            "daily_trends": [
                {
                    "date": trend.date.isoformat(),
                    "payment_count": trend.payment_count,
                    "total_amount": float(trend.total_amount),
                    "successful_count": trend.successful_count,
                    "failed_count": trend.failed_count,
                    "success_rate": round(
                        (trend.successful_count / trend.payment_count * 100) 
                        if trend.payment_count > 0 else 0, 2
                    )
                }
                for trend in daily_trends
            ],
            "method_trends": [
                {
                    "date": trend.date.isoformat(),
                    "method": trend.method.value,
                    "count": trend.count
                }
                for trend in method_trends
            ]
        }
    
    def get_payment_alerts(self) -> List[Dict[str, Any]]:
        """Get payment system alerts."""
        alerts = []
        
        # Check payment success rate
        total_payments = self.db.query(Payment).count()
        if total_payments > 0:
            successful_payments = self.db.query(Payment).filter(
                Payment.status == PaymentStatus.COMPLETED
            ).count()
            success_rate = successful_payments / total_payments * 100
            
            if success_rate < 80:
                alerts.append({
                    "type": "payment_success_rate_low",
                    "severity": "critical" if success_rate < 70 else "warning",
                    "message": f"Payment success rate is {success_rate:.1f}%",
                    "value": success_rate,
                    "threshold": 80,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
        
        # Check pending payments
        pending_payments = self.db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING
        ).count()
        
        if pending_payments > 50:
            alerts.append({
                "type": "pending_payments_high",
                "severity": "critical" if pending_payments > 100 else "warning",
                "message": f"{pending_payments} payments are pending",
                "value": pending_payments,
                "threshold": 50,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Check unverified bank accounts
        total_accounts = self.db.query(BankAccount).count()
        if total_accounts > 0:
            unverified_accounts = self.db.query(BankAccount).filter(
                BankAccount.verified == False
            ).count()
            unverified_rate = unverified_accounts / total_accounts * 100
            
            if unverified_rate > 40:
                alerts.append({
                    "type": "unverified_accounts_high",
                    "severity": "warning",
                    "message": f"{unverified_rate:.1f}% of bank accounts are unverified",
                    "value": unverified_rate,
                    "threshold": 40,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
        
        return alerts
    
    def get_analytics_report(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report."""
        overview = self.get_payment_overview(start_date, end_date, tenant_id)
        
        # Calculate period comparison
        period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date
        
        previous_metrics = self.get_payment_metrics(previous_start, previous_end, tenant_id)
        
        # Calculate growth rates
        current_payments = overview["payments"]["total_payments"]
        previous_payments = previous_metrics["total_payments"]
        payment_growth = ((current_payments - previous_payments) / previous_payments * 100) if previous_payments > 0 else 0
        
        current_amount = overview["payments"]["total_amount"]
        previous_amount = previous_metrics["total_amount"]
        amount_growth = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "overview": overview,
            "growth": {
                "payment_count_growth": round(payment_growth, 2),
                "amount_growth": round(amount_growth, 2),
                "success_rate_change": round(
                    overview["payments"]["success_rate"] - previous_metrics["success_rate"], 2
                )
            },
            "previous_period": {
                "start_date": previous_start.isoformat(),
                "end_date": previous_end.isoformat(),
                "metrics": previous_metrics
            },
            "recommendations": self.get_recommendations(overview),
            "key_insights": self.generate_key_insights(overview)
        }
    
    def get_recommendations(self, overview: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on payment data."""
        recommendations = []
        
        # Success rate recommendations
        success_rate = overview["payments"]["success_rate"]
        if success_rate < 90:
            recommendations.append({
                "type": "success_rate_improvement",
                "priority": "high" if success_rate < 80 else "medium",
                "title": "Improve Payment Success Rate",
                "description": f"Current success rate is {success_rate}%. Consider reviewing gateway configurations and retry logic.",
                "actions": [
                    "Review failed payment error codes",
                    "Optimize gateway retry policies",
                    "Implement payment method fallbacks"
                ]
            })
        
        # Bank account verification recommendations
        verification_rate = overview["bank_accounts"]["verification_rate"]
        if verification_rate < 80:
            recommendations.append({
                "type": "account_verification",
                "priority": "medium",
                "title": "Increase Bank Account Verification",
                "description": f"Only {verification_rate}% of bank accounts are verified. This may impact payout efficiency.",
                "actions": [
                    "Implement automated verification workflows",
                    "Send verification reminders to account holders",
                    "Streamline verification process"
                ]
            })
        
        # Payment method diversification
        payment_methods = overview["payments"]["payment_methods"]
        total_payments = sum(payment_methods.values())
        if total_payments > 0:
            gateway_percentage = payment_methods["gateway"] / total_payments * 100
            if gateway_percentage > 80:
                recommendations.append({
                    "type": "payment_diversification",
                    "priority": "low",
                    "title": "Diversify Payment Methods",
                    "description": f"{gateway_percentage:.1f}% of payments use gateways. Consider promoting alternative methods.",
                    "actions": [
                        "Promote bank transfer options",
                        "Implement cash collection points",
                        "Offer payment method incentives"
                    ]
                })
        
        return recommendations
    
    def generate_key_insights(self, overview: Dict[str, Any]) -> List[str]:
        """Generate key insights from payment data."""
        insights = []
        
        # Payment volume insights
        total_payments = overview["payments"]["total_payments"]
        if total_payments > 1000:
            insights.append(f"High payment volume: {total_payments:,} transactions processed")
        elif total_payments < 100:
            insights.append(f"Low payment volume: Only {total_payments} transactions processed")
        
        # Success rate insights
        success_rate = overview["payments"]["success_rate"]
        if success_rate > 95:
            insights.append(f"Excellent payment success rate: {success_rate}%")
        elif success_rate < 80:
            insights.append(f"Payment success rate needs attention: {success_rate}%")
        
        # Bank account insights
        verification_rate = overview["bank_accounts"]["verification_rate"]
        if verification_rate > 90:
            insights.append(f"High bank account verification rate: {verification_rate}%")
        elif verification_rate < 60:
            insights.append(f"Many bank accounts remain unverified: {100-verification_rate:.1f}%")
        
        # Alert insights
        alert_count = len(overview["alerts"])
        if alert_count == 0:
            insights.append("No active payment system alerts")
        elif alert_count > 3:
            insights.append(f"Multiple payment system alerts require attention: {alert_count}")
        
        return insights

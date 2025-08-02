"""
Payment Dashboard Metrics Seed Data

Seed script to add payment system dashboard metrics, segments, widgets, and alert thresholds.
"""

from sqlalchemy.orm import Session
from ..models.dashboard.metrics import MetricDefinition, SegmentDefinition, DashboardWidget, ThresholdDefinition
from ..core.database import SessionLocal


def seed_payment_dashboard_metrics():
    """Seed payment dashboard metrics, segments, widgets, and thresholds."""
    db = SessionLocal()
    
    try:
        # Payment System Metrics
        payment_metrics = [
            {
                "key": "total_bank_accounts",
                "name": "Total Bank Accounts",
                "description": "Total number of bank accounts in the system",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM bank_accounts",
                "unit": "accounts",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "active_bank_accounts",
                "name": "Active Bank Accounts",
                "description": "Number of active bank accounts",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM bank_accounts WHERE active = true",
                "unit": "accounts",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "verified_bank_accounts",
                "name": "Verified Bank Accounts",
                "description": "Number of verified bank accounts",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM bank_accounts WHERE verified = true",
                "unit": "accounts",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "platform_collection_accounts",
                "name": "Platform Collection Accounts",
                "description": "Number of platform collection accounts",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM bank_accounts WHERE owner_type = 'PLATFORM'",
                "unit": "accounts",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "reseller_payout_accounts",
                "name": "Reseller Payout Accounts",
                "description": "Number of reseller payout accounts",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM bank_accounts WHERE owner_type = 'RESELLER'",
                "unit": "accounts",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "reseller",
                "cache_ttl": 300
            },
            {
                "key": "total_payments",
                "name": "Total Payments",
                "description": "Total number of payment transactions",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "successful_payments",
                "name": "Successful Payments",
                "description": "Number of successful payment transactions",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE status = 'completed'",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "failed_payments",
                "name": "Failed Payments",
                "description": "Number of failed payment transactions",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE status = 'failed'",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "pending_payments",
                "name": "Pending Payments",
                "description": "Number of pending payment transactions",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE status = 'pending'",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 60
            },
            {
                "key": "payment_success_rate",
                "name": "Payment Success Rate",
                "description": "Percentage of successful payments",
                "category": "payment",
                "metric_type": "ratio",
                "sql_query": """
                    SELECT 
                        CASE 
                            WHEN COUNT(*) = 0 THEN 0 
                            ELSE (COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*))
                        END
                    FROM payments
                """,
                "unit": "percentage",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "total_payment_amount",
                "name": "Total Payment Amount",
                "description": "Total amount of all payments",
                "category": "payment",
                "metric_type": "sum",
                "sql_query": "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed'",
                "unit": "currency",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "gateway_payments",
                "name": "Gateway Payments",
                "description": "Number of payments via payment gateways",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE method = 'gateway'",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "bank_transfer_payments",
                "name": "Bank Transfer Payments",
                "description": "Number of bank transfer payments",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE method = 'bank_transfer'",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "cash_payments",
                "name": "Cash Payments",
                "description": "Number of cash payments",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE method = 'cash'",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "bank_account_verification_rate",
                "name": "Bank Account Verification Rate",
                "description": "Percentage of verified bank accounts",
                "category": "payment",
                "metric_type": "ratio",
                "sql_query": """
                    SELECT 
                        CASE 
                            WHEN COUNT(*) = 0 THEN 0 
                            ELSE (COUNT(*) FILTER (WHERE verified = true) * 100.0 / COUNT(*))
                        END
                    FROM bank_accounts
                """,
                "unit": "percentage",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global",
                "cache_ttl": 300
            },
            {
                "key": "daily_payment_volume",
                "name": "Daily Payment Volume",
                "description": "Number of payments processed today",
                "category": "payment",
                "metric_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE DATE(created_at) = CURRENT_DATE",
                "unit": "payments",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 60
            },
            {
                "key": "daily_payment_amount",
                "name": "Daily Payment Amount",
                "description": "Total amount of payments processed today",
                "category": "payment",
                "metric_type": "sum",
                "sql_query": "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE DATE(created_at) = CURRENT_DATE AND status = 'completed'",
                "unit": "currency",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global",
                "cache_ttl": 60
            }
        ]
        
        # Payment System Segments
        payment_segments = [
            {
                "key": "high_value_payments",
                "name": "High Value Payments",
                "description": "Payments above $1000",
                "category": "payment",
                "filter_criteria": {"amount": {"gte": 1000}},
                "sql_filter": "amount >= 1000",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            },
            {
                "key": "gateway_customers",
                "name": "Gateway Payment Customers",
                "description": "Customers who use gateway payments",
                "category": "payment",
                "filter_criteria": {"payment_method": "gateway"},
                "sql_filter": "customer_id IN (SELECT DISTINCT customer_id FROM payments WHERE method = 'gateway')",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global"
            },
            {
                "key": "verified_accounts",
                "name": "Verified Bank Accounts",
                "description": "Bank accounts that are verified",
                "category": "payment",
                "filter_criteria": {"verified": True},
                "sql_filter": "verified = true",
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global"
            },
            {
                "key": "recent_payments",
                "name": "Recent Payments",
                "description": "Payments from the last 7 days",
                "category": "payment",
                "filter_criteria": {"created_at": {"gte": "7_days_ago"}},
                "sql_filter": "created_at >= NOW() - INTERVAL '7 days'",
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            }
        ]
        
        # Payment Dashboard Widgets
        payment_widgets = [
            {
                "key": "payment_overview",
                "name": "Payment Overview",
                "description": "Overview of payment system metrics",
                "widget_type": "metric_grid",
                "category": "payment",
                "config": {
                    "metrics": [
                        "total_payments",
                        "successful_payments",
                        "payment_success_rate",
                        "total_payment_amount"
                    ],
                    "layout": "2x2"
                },
                "position": {"x": 0, "y": 0, "width": 6, "height": 4},
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            },
            {
                "key": "payment_methods_chart",
                "name": "Payment Methods Distribution",
                "description": "Distribution of payment methods",
                "widget_type": "pie_chart",
                "category": "payment",
                "config": {
                    "metrics": [
                        "gateway_payments",
                        "bank_transfer_payments",
                        "cash_payments"
                    ],
                    "chart_type": "donut"
                },
                "position": {"x": 6, "y": 0, "width": 6, "height": 4},
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            },
            {
                "key": "daily_payment_trends",
                "name": "Daily Payment Trends",
                "description": "Daily payment volume and amount trends",
                "widget_type": "line_chart",
                "category": "payment",
                "config": {
                    "metrics": [
                        "daily_payment_volume",
                        "daily_payment_amount"
                    ],
                    "time_range": "30_days",
                    "dual_axis": True
                },
                "position": {"x": 0, "y": 4, "width": 12, "height": 4},
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            },
            {
                "key": "bank_account_status",
                "name": "Bank Account Status",
                "description": "Bank account verification and status overview",
                "widget_type": "status_grid",
                "category": "payment",
                "config": {
                    "metrics": [
                        "total_bank_accounts",
                        "verified_bank_accounts",
                        "platform_collection_accounts",
                        "reseller_payout_accounts"
                    ],
                    "layout": "2x2"
                },
                "position": {"x": 0, "y": 8, "width": 6, "height": 4},
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global"
            },
            {
                "key": "payment_alerts",
                "name": "Payment System Alerts",
                "description": "Critical payment system alerts and warnings",
                "widget_type": "alert_list",
                "category": "payment",
                "config": {
                    "alert_types": [
                        "high_failure_rate",
                        "pending_payments_high",
                        "unverified_accounts_high"
                    ],
                    "max_items": 10
                },
                "position": {"x": 6, "y": 8, "width": 6, "height": 4},
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            }
        ]
        
        # Payment Alert Thresholds
        payment_thresholds = [
            {
                "key": "payment_success_rate_critical",
                "name": "Payment Success Rate Critical",
                "description": "Critical threshold for payment success rate",
                "metric_key": "payment_success_rate",
                "threshold_type": "min",
                "critical_value": 80.0,
                "warning_value": 90.0,
                "operator": "lt",
                "alert_message": "Payment success rate is critically low",
                "severity": "critical",
                "notification_channels": ["email", "slack"],
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            },
            {
                "key": "failed_payments_high",
                "name": "High Failed Payments",
                "description": "Alert when failed payments are high",
                "metric_key": "failed_payments",
                "threshold_type": "max",
                "critical_value": 100,
                "warning_value": 50,
                "operator": "gt",
                "alert_message": "High number of failed payments detected",
                "severity": "warning",
                "notification_channels": ["email"],
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            },
            {
                "key": "pending_payments_high",
                "name": "High Pending Payments",
                "description": "Alert when pending payments are high",
                "metric_key": "pending_payments",
                "threshold_type": "max",
                "critical_value": 50,
                "warning_value": 20,
                "operator": "gt",
                "alert_message": "High number of pending payments requiring attention",
                "severity": "warning",
                "notification_channels": ["email"],
                "visibility_roles": ["admin", "manager", "finance"],
                "tenant_scope": "global"
            },
            {
                "key": "unverified_accounts_high",
                "name": "High Unverified Accounts",
                "description": "Alert when unverified bank accounts percentage is high",
                "metric_key": "bank_account_verification_rate",
                "threshold_type": "min",
                "critical_value": 60.0,
                "warning_value": 80.0,
                "operator": "lt",
                "alert_message": "High percentage of unverified bank accounts",
                "severity": "warning",
                "notification_channels": ["email"],
                "visibility_roles": ["admin", "manager"],
                "tenant_scope": "global"
            }
        ]
        
        # Insert metrics
        for metric_data in payment_metrics:
            existing = db.query(MetricDefinition).filter(
                MetricDefinition.key == metric_data["key"]
            ).first()
            
            if not existing:
                metric = MetricDefinition(**metric_data)
                db.add(metric)
                print(f"Added payment metric: {metric_data['key']}")
        
        # Insert segments
        for segment_data in payment_segments:
            existing = db.query(SegmentDefinition).filter(
                SegmentDefinition.key == segment_data["key"]
            ).first()
            
            if not existing:
                segment = SegmentDefinition(**segment_data)
                db.add(segment)
                print(f"Added payment segment: {segment_data['key']}")
        
        # Insert widgets
        for widget_data in payment_widgets:
            existing = db.query(DashboardWidget).filter(
                DashboardWidget.key == widget_data["key"]
            ).first()
            
            if not existing:
                widget = DashboardWidget(**widget_data)
                db.add(widget)
                print(f"Added payment widget: {widget_data['key']}")
        
        # Insert thresholds
        for threshold_data in payment_thresholds:
            existing = db.query(ThresholdDefinition).filter(
                ThresholdDefinition.key == threshold_data["key"]
            ).first()
            
            if not existing:
                threshold = ThresholdDefinition(**threshold_data)
                db.add(threshold)
                print(f"Added payment threshold: {threshold_data['key']}")
        
        db.commit()
        print("✅ Payment dashboard metrics seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding payment dashboard metrics: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_payment_dashboard_metrics()

#!/usr/bin/env python3
"""
Dashboard Data Seeding Script

Seeds the database with metric definitions, widgets, segments, and thresholds
for the Payment Dashboard Analytics system.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from app.core.database import get_db_session
from app.models.dashboard import (
    MetricDefinition, DataSourceConfig, SegmentDefinition,
    DashboardWidget, ThresholdDefinition
)
from app.models.payment import BankAccount, Payment, Gateway
from app.models.customer import Customer
from app.models.foundation.base import CustomerStatus


def seed_dashboard_data():
    """Seed dashboard data for payment analytics."""
    print("🚀 Starting Dashboard Data Seeding...")
    
    # Get database session
    db = next(get_db_session())
    
    try:
        # Clear existing data
        print("🧹 Clearing existing dashboard data...")
        db.query(ThresholdDefinition).delete()
        db.query(DashboardWidget).delete()
        db.query(SegmentDefinition).delete()
        db.query(MetricDefinition).delete()
        db.query(DataSourceConfig).delete()
        db.commit()
        
        # 1. Create Data Source Configurations
        print("📊 Creating data source configurations...")
        
        data_sources = [
            {
                "name": "primary_database",
                "source_type": "database",
                "connection_string": "postgresql://localhost/isp_framework",
                "is_active": True,
                "refresh_interval": 300,  # 5 minutes
                "configuration": {
                    "schema": "public",
                    "timeout": 30
                }
            },
            {
                "name": "payment_api",
                "source_type": "api",
                "connection_string": "http://localhost:8000/api/v1",
                "is_active": True,
                "refresh_interval": 60,  # 1 minute
                "configuration": {
                    "auth_type": "bearer",
                    "timeout": 10
                }
            }
        ]
        
        for ds_data in data_sources:
            data_source = DataSourceConfig(**ds_data)
            db.add(data_source)
        
        db.commit()
        
        # 2. Create Metric Definitions
        print("📈 Creating metric definitions...")
        
        metrics = [
            # Financial Metrics
            {
                "key": "total_revenue",
                "name": "Total Revenue",
                "description": "Total revenue from all payments",
                "category": "financial",
                "calculation_type": "sum",
                "sql_query": "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed'",
                "unit": "NGN",
                "format_type": "currency",
                "is_active": True,
                "cache_ttl": 300,
                "visibility_roles": ["admin", "billing_manager", "analyst"],
                "tenant_scope": "global"
            },
            {
                "key": "payment_success_rate",
                "name": "Payment Success Rate",
                "description": "Percentage of successful payments",
                "category": "financial",
                "calculation_type": "ratio",
                "sql_query": """
                    SELECT 
                        CASE 
                            WHEN COUNT(*) = 0 THEN 0 
                            ELSE (COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*))
                        END 
                    FROM payments
                """,
                "unit": "%",
                "format_type": "percentage",
                "is_active": True,
                "cache_ttl": 300,
                "visibility_roles": ["admin", "billing_manager", "analyst"],
                "tenant_scope": "global"
            },
            {
                "key": "monthly_recurring_revenue",
                "name": "Monthly Recurring Revenue (MRR)",
                "description": "Monthly recurring revenue from subscriptions",
                "category": "financial",
                "calculation_type": "sum",
                "sql_query": """
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM payments 
                    WHERE status = 'completed' 
                    AND created_at >= date_trunc('month', CURRENT_DATE)
                """,
                "unit": "NGN",
                "format_type": "currency",
                "is_active": True,
                "cache_ttl": 3600,
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            },
            {
                "key": "outstanding_receivables",
                "name": "Outstanding Receivables",
                "description": "Total amount of pending payments",
                "category": "financial",
                "calculation_type": "sum",
                "sql_query": "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'pending'",
                "unit": "NGN",
                "format_type": "currency",
                "is_active": True,
                "cache_ttl": 300,
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            },
            
            # Customer Metrics
            {
                "key": "total_customers",
                "name": "Total Customers",
                "description": "Total number of customers",
                "category": "customer",
                "calculation_type": "count",
                "sql_query": "SELECT COUNT(*) FROM customers WHERE is_active = true",
                "unit": "customers",
                "format_type": "number",
                "is_active": True,
                "cache_ttl": 600,
                "visibility_roles": ["admin", "customer_support", "analyst"],
                "tenant_scope": "global"
            },
            {
                "key": "active_customers",
                "name": "Active Customers",
                "description": "Number of customers with recent activity",
                "category": "customer",
                "calculation_type": "count",
                "sql_query": """
                    SELECT COUNT(DISTINCT customer_id) 
                    FROM payments 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                """,
                "unit": "customers",
                "format_type": "number",
                "is_active": True,
                "cache_ttl": 600,
                "visibility_roles": ["admin", "customer_support", "analyst"],
                "tenant_scope": "global"
            },
            
            # Operational Metrics
            {
                "key": "total_payments",
                "name": "Total Payments",
                "description": "Total number of payment transactions",
                "category": "operational",
                "calculation_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments",
                "unit": "transactions",
                "format_type": "number",
                "is_active": True,
                "cache_ttl": 300,
                "visibility_roles": ["admin", "billing_manager", "analyst"],
                "tenant_scope": "global"
            },
            {
                "key": "failed_payments",
                "name": "Failed Payments",
                "description": "Number of failed payment transactions",
                "category": "operational",
                "calculation_type": "count",
                "sql_query": "SELECT COUNT(*) FROM payments WHERE status = 'failed'",
                "unit": "transactions",
                "format_type": "number",
                "is_active": True,
                "cache_ttl": 300,
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            },
            
            # Network Metrics (placeholder for ISP-specific metrics)
            {
                "key": "active_bank_accounts",
                "name": "Active Bank Accounts",
                "description": "Number of active bank accounts",
                "category": "network",
                "calculation_type": "count",
                "sql_query": "SELECT COUNT(*) FROM bank_accounts WHERE is_active = true",
                "unit": "accounts",
                "format_type": "number",
                "is_active": True,
                "cache_ttl": 600,
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            }
        ]
        
        for metric_data in metrics:
            metric = MetricDefinition(**metric_data)
            db.add(metric)
        
        db.commit()
        
        # 3. Create Segment Definitions
        print("🎯 Creating segment definitions...")
        
        segments = [
            {
                "key": "high_value_customers",
                "name": "High Value Customers",
                "description": "Customers with payments > 50,000 NGN",
                "filter_criteria": {
                    "payment_amount": {"min": 50000},
                    "status": "active"
                },
                "sql_filter": "customer_id IN (SELECT customer_id FROM payments WHERE amount > 50000)",
                "is_active": True,
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            },
            {
                "key": "recent_customers",
                "name": "Recent Customers",
                "description": "Customers who made payments in the last 30 days",
                "filter_criteria": {
                    "payment_date": {"days_ago": 30}
                },
                "sql_filter": "customer_id IN (SELECT customer_id FROM payments WHERE created_at >= CURRENT_DATE - INTERVAL '30 days')",
                "is_active": True,
                "visibility_roles": ["admin", "customer_support", "analyst"],
                "tenant_scope": "global"
            },
            {
                "key": "failed_payment_customers",
                "name": "Failed Payment Customers",
                "description": "Customers with recent failed payments",
                "filter_criteria": {
                    "payment_status": "failed"
                },
                "sql_filter": "customer_id IN (SELECT customer_id FROM payments WHERE status = 'failed')",
                "is_active": True,
                "visibility_roles": ["admin", "billing_manager", "customer_support"],
                "tenant_scope": "global"
            }
        ]
        
        for segment_data in segments:
            segment = SegmentDefinition(**segment_data)
            db.add(segment)
        
        db.commit()
        
        # 4. Create Dashboard Widgets
        print("🎨 Creating dashboard widgets...")
        
        widgets = [
            {
                "key": "financial_overview",
                "name": "Financial Overview",
                "description": "Key financial metrics overview",
                "widget_type": "card_grid",
                "position": {"row": 0, "col": 0, "width": 12, "height": 4},
                "configuration": {
                    "metrics": ["total_revenue", "monthly_recurring_revenue", "payment_success_rate", "outstanding_receivables"],
                    "layout": "grid",
                    "refresh_interval": 300
                },
                "is_active": True,
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            },
            {
                "key": "payment_trends",
                "name": "Payment Trends",
                "description": "Payment volume and success rate trends",
                "widget_type": "line_chart",
                "position": {"row": 1, "col": 0, "width": 8, "height": 6},
                "configuration": {
                    "metrics": ["total_payments", "payment_success_rate"],
                    "time_period": "30d",
                    "chart_type": "line"
                },
                "is_active": True,
                "visibility_roles": ["admin", "billing_manager", "analyst"],
                "tenant_scope": "global"
            },
            {
                "key": "customer_metrics",
                "name": "Customer Metrics",
                "description": "Customer acquisition and activity metrics",
                "widget_type": "gauge_chart",
                "position": {"row": 1, "col": 8, "width": 4, "height": 6},
                "configuration": {
                    "metrics": ["total_customers", "active_customers"],
                    "chart_type": "gauge",
                    "thresholds": {"good": 1000, "warning": 500, "critical": 100}
                },
                "is_active": True,
                "visibility_roles": ["admin", "customer_support", "analyst"],
                "tenant_scope": "global"
            },
            {
                "key": "alerts_summary",
                "name": "Alerts Summary",
                "description": "Critical alerts and notifications",
                "widget_type": "alert_list",
                "position": {"row": 2, "col": 0, "width": 12, "height": 4},
                "configuration": {
                    "alert_types": ["payment_failures", "high_receivables", "low_success_rate"],
                    "max_items": 10
                },
                "is_active": True,
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            }
        ]
        
        for widget_data in widgets:
            widget = DashboardWidget(**widget_data)
            db.add(widget)
        
        db.commit()
        
        # 5. Create Threshold Definitions
        print("🚨 Creating threshold definitions...")
        
        thresholds = [
            {
                "metric_key": "payment_success_rate",
                "name": "Low Payment Success Rate",
                "threshold_type": "min",
                "warning_value": Decimal("85.0"),
                "critical_value": Decimal("75.0"),
                "comparison_operator": "lt",
                "is_active": True,
                "notification_channels": ["email", "webhook"],
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            },
            {
                "metric_key": "outstanding_receivables",
                "name": "High Outstanding Receivables",
                "threshold_type": "max",
                "warning_value": Decimal("1000000.0"),  # 1M NGN
                "critical_value": Decimal("5000000.0"),  # 5M NGN
                "comparison_operator": "gt",
                "is_active": True,
                "notification_channels": ["email", "sms"],
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            },
            {
                "metric_key": "failed_payments",
                "name": "High Failed Payment Count",
                "threshold_type": "max",
                "warning_value": Decimal("50.0"),
                "critical_value": Decimal("100.0"),
                "comparison_operator": "gt",
                "is_active": True,
                "notification_channels": ["email", "webhook"],
                "visibility_roles": ["admin", "billing_manager"],
                "tenant_scope": "global"
            }
        ]
        
        for threshold_data in thresholds:
            threshold = ThresholdDefinition(**threshold_data)
            db.add(threshold)
        
        db.commit()
        
        # 6. Create Sample Data for Testing
        print("🧪 Creating sample test data...")
        
        # Create sample customers if they don't exist
        customer_count = db.query(Customer).count()
        if customer_count < 5:
            print("Creating sample customers...")
            for i in range(1, 6):
                customer = Customer(
                    name=f"Test Customer {i}",
                    email=f"customer{i}@test.com",
                    phone=f"080123456{i:02d}",
                    is_active=True,
                    status_id=1,  # Assuming active status
                    reseller_id=1
                )
                db.add(customer)
            db.commit()
        
        # Create sample bank accounts if they don't exist
        bank_account_count = db.query(BankAccount).count()
        if bank_account_count < 2:
            print("Creating sample bank accounts...")
            
            platform_account = BankAccount(
                account_name="ISP Platform Collections",
                account_number="1234567890",
                bank_name="First Bank",
                bank_code="011",
                owner_type="PLATFORM",
                is_verified=True,
                is_active=True
            )
            db.add(platform_account)
            
            reseller_account = BankAccount(
                account_name="Lagos Reseller Payouts",
                account_number="0987654321",
                bank_name="GTBank",
                bank_code="058",
                owner_type="RESELLER",
                owner_id=1,
                is_verified=True,
                is_active=True
            )
            db.add(reseller_account)
            db.commit()
        
        # Create sample payments if they don't exist
        payment_count = db.query(Payment).count()
        if payment_count < 10:
            print("Creating sample payments...")
            
            # Get customer IDs
            customers = db.query(Customer).limit(5).all()
            
            for i in range(1, 11):
                customer = customers[i % len(customers)]
                amount = 1000 + (i * 500)
                status = "completed" if i % 4 != 0 else ("failed" if i % 8 == 0 else "pending")
                method = "gateway" if i % 3 != 0 else "cash"
                
                payment = Payment(
                    amount=Decimal(str(amount)),
                    currency="NGN",
                    method=method,
                    status=status,
                    customer_id=customer.id,
                    description=f"Test payment {i}",
                    reference=f"TEST{i}{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    created_at=datetime.now() - timedelta(days=i)
                )
                db.add(payment)
            
            db.commit()
        
        print("✅ Dashboard data seeding completed successfully!")
        print(f"📊 Created:")
        print(f"   - {len(data_sources)} data sources")
        print(f"   - {len(metrics)} metric definitions")
        print(f"   - {len(segments)} segment definitions")
        print(f"   - {len(widgets)} dashboard widgets")
        print(f"   - {len(thresholds)} threshold definitions")
        print(f"   - Sample customers, bank accounts, and payments")
        
    except Exception as e:
        print(f"❌ Error seeding dashboard data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_dashboard_data()

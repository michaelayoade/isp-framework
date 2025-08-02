"""Seed script for initial dashboard metrics and configurations."""

from sqlalchemy.orm import Session
from app.models.dashboard import (
    MetricDefinition,
    DataSourceConfig,
    SegmentDefinition,
    DashboardWidget,
    ThresholdDefinition
)


def seed_financial_metrics(db: Session):
    """Seed financial KPI metrics."""
    financial_metrics = [
        {
            "metric_key": "total_revenue",
            "metric_name": "Total Revenue",
            "description": "Sum of all invoice amounts",
            "category": "financial",
            "calculation_method": "sum",
            "source_table": "invoices",
            "source_column": "total_amount",
            "filters": {"status": "paid"},
            "display_format": "currency",
            "unit": "USD",
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "arpu",
            "metric_name": "Average Revenue Per User",
            "description": "Total revenue divided by active customers",
            "category": "financial",
            "calculation_method": "custom_sql",
            "custom_sql": """
                SELECT 
                    COALESCE(SUM(i.total_amount) / NULLIF(COUNT(DISTINCT c.id), 0), 0) as value
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.status = 'paid' 
                AND c.status_id IN (SELECT id FROM customer_statuses WHERE status = 'active')
                AND i.created_at >= %s AND i.created_at <= %s
            """,
            "display_format": "currency",
            "unit": "USD",
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "mrr",
            "metric_name": "Monthly Recurring Revenue",
            "description": "Predictable monthly revenue from active subscriptions",
            "category": "financial",
            "calculation_method": "custom_sql",
            "custom_sql": """
                SELECT 
                    COALESCE(SUM(
                        CASE 
                            WHEN sp.billing_cycle = 'monthly' THEN sp.price
                            WHEN sp.billing_cycle = 'quarterly' THEN sp.price / 3
                            WHEN sp.billing_cycle = 'yearly' THEN sp.price / 12
                            ELSE 0
                        END
                    ), 0) as value
                FROM customer_services cs
                JOIN service_plans sp ON cs.service_plan_id = sp.id
                WHERE cs.status = 'active'
            """,
            "display_format": "currency",
            "unit": "USD",
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "payment_success_rate",
            "metric_name": "Payment Success Rate",
            "description": "Percentage of successful payments",
            "category": "financial",
            "calculation_method": "custom_sql",
            "custom_sql": """
                SELECT 
                    COALESCE(
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(*), 0), 0
                    ) as value
                FROM payments
                WHERE created_at >= %s AND created_at <= %s
            """,
            "display_format": "percentage",
            "unit": "%",
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "outstanding_receivables",
            "metric_name": "Outstanding Receivables",
            "description": "Total unpaid invoice amounts",
            "category": "financial",
            "calculation_method": "sum",
            "source_table": "invoices",
            "source_column": "total_amount",
            "filters": {"status": ["pending", "overdue"]},
            "display_format": "currency",
            "unit": "USD",
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        }
    ]
    
    for metric_data in financial_metrics:
        existing = db.query(MetricDefinition).filter_by(metric_key=metric_data["metric_key"]).first()
        if not existing:
            metric = MetricDefinition(**metric_data)
            db.add(metric)
    
    db.commit()


def seed_network_metrics(db: Session):
    """Seed network performance metrics."""
    network_metrics = [
        {
            "metric_key": "device_uptime_avg",
            "metric_name": "Average Device Uptime",
            "description": "Average uptime across all network devices",
            "category": "network",
            "calculation_method": "avg",
            "source_table": "network_devices",
            "source_column": "uptime_seconds",
            "filters": {"operational_status": "up"},
            "display_format": "number",
            "unit": "hours",
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        },
        {
            "metric_key": "bandwidth_utilization_avg",
            "metric_name": "Average Bandwidth Utilization",
            "description": "Average bandwidth utilization across all interfaces",
            "category": "network",
            "calculation_method": "avg",
            "source_table": "device_metrics",
            "source_column": "metric_value",
            "filters": {"metric_type": "bandwidth_utilization"},
            "display_format": "percentage",
            "unit": "%",
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        },
        {
            "metric_key": "active_alerts_count",
            "metric_name": "Active Network Alerts",
            "description": "Number of active network alerts",
            "category": "network",
            "calculation_method": "count",
            "source_table": "network_alerts",
            "source_column": "id",
            "filters": {"is_active": True},
            "display_format": "number",
            "unit": "count",
            "is_real_time": True,
            "cache_ttl_seconds": 60,
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        },
        {
            "metric_key": "critical_alerts_count",
            "metric_name": "Critical Network Alerts",
            "description": "Number of critical severity alerts",
            "category": "network",
            "calculation_method": "count",
            "source_table": "network_alerts",
            "source_column": "id",
            "filters": {"is_active": True, "severity": "critical"},
            "display_format": "number",
            "unit": "count",
            "is_real_time": True,
            "cache_ttl_seconds": 60,
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        },
        {
            "metric_key": "packet_loss_avg",
            "metric_name": "Average Packet Loss",
            "description": "Average packet loss percentage across monitored links",
            "category": "network",
            "calculation_method": "avg",
            "source_table": "device_metrics",
            "source_column": "metric_value",
            "filters": {"metric_type": "packet_loss"},
            "display_format": "percentage",
            "unit": "%",
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        }
    ]
    
    for metric_data in network_metrics:
        existing = db.query(MetricDefinition).filter_by(metric_key=metric_data["metric_key"]).first()
        if not existing:
            metric = MetricDefinition(**metric_data)
            db.add(metric)
    
    db.commit()


def seed_customer_metrics(db: Session):
    """Seed customer-related metrics."""
    customer_metrics = [
        {
            "metric_key": "total_customers",
            "metric_name": "Total Customers",
            "description": "Total number of customers",
            "category": "customer",
            "calculation_method": "count",
            "source_table": "customers",
            "source_column": "id",
            "filters": {},
            "display_format": "number",
            "unit": "count",
            "visibility_roles": ["admin", "manager", "sales"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "active_customers",
            "metric_name": "Active Customers",
            "description": "Number of active customers",
            "category": "customer",
            "calculation_method": "count",
            "source_table": "customers",
            "source_column": "id",
            "joins": [{"table": "customer_statuses", "on": "customers.status_id = customer_statuses.id"}],
            "filters": {"customer_statuses.status": "active"},
            "display_format": "number",
            "unit": "count",
            "visibility_roles": ["admin", "manager", "sales"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "new_customers_monthly",
            "metric_name": "New Customers This Month",
            "description": "Number of customers acquired this month",
            "category": "customer",
            "calculation_method": "custom_sql",
            "custom_sql": """
                SELECT COUNT(*) as value
                FROM customers
                WHERE created_at >= date_trunc('month', CURRENT_DATE)
                AND created_at < date_trunc('month', CURRENT_DATE) + interval '1 month'
            """,
            "display_format": "number",
            "unit": "count",
            "visibility_roles": ["admin", "manager", "sales"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "churn_rate",
            "metric_name": "Customer Churn Rate",
            "description": "Percentage of customers who cancelled this month",
            "category": "customer",
            "calculation_method": "custom_sql",
            "custom_sql": """
                WITH monthly_stats AS (
                    SELECT 
                        COUNT(CASE WHEN created_at >= date_trunc('month', CURRENT_DATE) THEN 1 END) as new_customers,
                        COUNT(CASE WHEN status_id IN (SELECT id FROM customer_statuses WHERE status = 'cancelled') 
                                   AND updated_at >= date_trunc('month', CURRENT_DATE) THEN 1 END) as churned_customers,
                        COUNT(CASE WHEN status_id IN (SELECT id FROM customer_statuses WHERE status = 'active') THEN 1 END) as active_customers
                    FROM customers
                )
                SELECT 
                    CASE 
                        WHEN active_customers > 0 THEN (churned_customers * 100.0 / active_customers)
                        ELSE 0
                    END as value
                FROM monthly_stats
            """,
            "display_format": "percentage",
            "unit": "%",
            "visibility_roles": ["admin", "manager", "sales"],
            "tenant_scope": "reseller"
        }
    ]
    
    for metric_data in customer_metrics:
        existing = db.query(MetricDefinition).filter_by(metric_key=metric_data["metric_key"]).first()
        if not existing:
            metric = MetricDefinition(**metric_data)
            db.add(metric)
    
    db.commit()


def seed_operational_metrics(db: Session):
    """Seed operational metrics."""
    operational_metrics = [
        {
            "metric_key": "active_services",
            "metric_name": "Active Services",
            "description": "Number of active customer services",
            "category": "operational",
            "calculation_method": "count",
            "source_table": "customer_services",
            "source_column": "id",
            "filters": {"status": "active"},
            "display_format": "number",
            "unit": "count",
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "avg_service_activation_time",
            "metric_name": "Average Service Activation Time",
            "description": "Average time to activate new services",
            "category": "operational",
            "calculation_method": "custom_sql",
            "custom_sql": """
                SELECT 
                    COALESCE(AVG(EXTRACT(EPOCH FROM (activated_at - created_at)) / 3600), 0) as value
                FROM customer_services
                WHERE activated_at IS NOT NULL
                AND created_at >= %s AND created_at <= %s
            """,
            "display_format": "number",
            "unit": "hours",
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "open_tickets",
            "metric_name": "Open Support Tickets",
            "description": "Number of open support tickets",
            "category": "operational",
            "calculation_method": "count",
            "source_table": "tickets",
            "source_column": "id",
            "joins": [{"table": "ticket_statuses", "on": "tickets.status_id = ticket_statuses.id"}],
            "filters": {"ticket_statuses.status": ["open", "in_progress"]},
            "display_format": "number",
            "unit": "count",
            "is_real_time": True,
            "cache_ttl_seconds": 300,
            "visibility_roles": ["admin", "manager", "support"],
            "tenant_scope": "reseller"
        },
        {
            "metric_key": "avg_ticket_resolution_time",
            "metric_name": "Average Ticket Resolution Time",
            "description": "Average time to resolve support tickets",
            "category": "operational",
            "calculation_method": "custom_sql",
            "custom_sql": """
                SELECT 
                    COALESCE(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600), 0) as value
                FROM tickets
                WHERE resolved_at IS NOT NULL
                AND created_at >= %s AND created_at <= %s
            """,
            "display_format": "number",
            "unit": "hours",
            "visibility_roles": ["admin", "manager", "support"],
            "tenant_scope": "reseller"
        }
    ]
    
    for metric_data in operational_metrics:
        existing = db.query(MetricDefinition).filter_by(metric_key=metric_data["metric_key"]).first()
        if not existing:
            metric = MetricDefinition(**metric_data)
            db.add(metric)
    
    db.commit()


def seed_dashboard_segments(db: Session):
    """Seed common dashboard segments."""
    segments = [
        {
            "segment_key": "high_value_customers",
            "segment_name": "High Value Customers",
            "description": "Customers with ARPU above $100",
            "segment_type": "customer",
            "criteria": {"arpu": {"operator": ">", "value": 100}},
            "base_table": "customers",
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        },
        {
            "segment_key": "fiber_customers",
            "segment_name": "Fiber Internet Customers",
            "description": "Customers with fiber internet services",
            "segment_type": "service",
            "criteria": {"service_type": {"operator": "=", "value": "fiber"}},
            "base_table": "customer_services",
            "join_tables": [{"table": "service_types", "on": "customer_services.service_type_id = service_types.id"}],
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "reseller"
        },
        {
            "segment_key": "lagos_customers",
            "segment_name": "Lagos Customers",
            "description": "Customers located in Lagos",
            "segment_type": "geographic",
            "criteria": {"city": {"operator": "=", "value": "Lagos"}},
            "base_table": "customers",
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        },
        {
            "segment_key": "critical_devices",
            "segment_name": "Critical Network Devices",
            "description": "Core routers and switches",
            "segment_type": "device",
            "criteria": {"device_type": {"operator": "in", "value": ["router", "switch"]}, "criticality": {"operator": "=", "value": "high"}},
            "base_table": "network_devices",
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        }
    ]
    
    for segment_data in segments:
        existing = db.query(SegmentDefinition).filter_by(segment_key=segment_data["segment_key"]).first()
        if not existing:
            segment = SegmentDefinition(**segment_data)
            db.add(segment)
    
    db.commit()


def seed_dashboard_widgets(db: Session):
    """Seed default dashboard widgets."""
    widgets = [
        {
            "widget_key": "financial_overview",
            "title": "Financial Overview",
            "description": "Key financial metrics dashboard",
            "category": "financial",
            "widget_type": "chart",
            "chart_type": "line",
            "metrics": ["total_revenue", "arpu", "mrr"],
            "display_config": {
                "x_axis": "date",
                "y_axis": "value",
                "colors": ["#007bff", "#28a745", "#ffc107"],
                "show_legend": True
            },
            "position": {"row": 1, "col": 1, "width": 8, "height": 4},
            "visibility_roles": ["admin", "manager"],
            "tenant_scope": "reseller"
        },
        {
            "widget_key": "network_health",
            "title": "Network Health",
            "description": "Real-time network status",
            "category": "network",
            "widget_type": "gauge",
            "metrics": ["device_uptime_avg", "bandwidth_utilization_avg"],
            "display_config": {
                "min_value": 0,
                "max_value": 100,
                "thresholds": [
                    {"value": 95, "color": "green"},
                    {"value": 85, "color": "yellow"},
                    {"value": 0, "color": "red"}
                ]
            },
            "position": {"row": 1, "col": 9, "width": 4, "height": 4},
            "auto_refresh": True,
            "refresh_interval_seconds": 60,
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        },
        {
            "widget_key": "customer_metrics",
            "title": "Customer Metrics",
            "description": "Customer acquisition and retention",
            "category": "customer",
            "widget_type": "metric",
            "metrics": ["total_customers", "active_customers", "new_customers_monthly", "churn_rate"],
            "display_config": {
                "layout": "grid",
                "show_change": True,
                "comparison_period": "previous_month"
            },
            "position": {"row": 2, "col": 1, "width": 6, "height": 3},
            "visibility_roles": ["admin", "manager", "sales"],
            "tenant_scope": "reseller"
        },
        {
            "widget_key": "alerts_summary",
            "title": "Active Alerts",
            "description": "Current system alerts",
            "category": "network",
            "widget_type": "table",
            "metrics": ["active_alerts_count", "critical_alerts_count"],
            "display_config": {
                "columns": ["alert_type", "severity", "count", "last_updated"],
                "sortable": True,
                "max_rows": 10
            },
            "position": {"row": 2, "col": 7, "width": 6, "height": 3},
            "auto_refresh": True,
            "refresh_interval_seconds": 60,
            "visibility_roles": ["admin", "manager", "technician"],
            "tenant_scope": "global"
        }
    ]
    
    for widget_data in widgets:
        existing = db.query(DashboardWidget).filter_by(widget_key=widget_data["widget_key"]).first()
        if not existing:
            widget = DashboardWidget(**widget_data)
            db.add(widget)
    
    db.commit()


def seed_all_dashboard_data(db: Session):
    """Seed all dashboard data."""
    print("Seeding financial metrics...")
    seed_financial_metrics(db)
    
    print("Seeding network metrics...")
    seed_network_metrics(db)
    
    print("Seeding customer metrics...")
    seed_customer_metrics(db)
    
    print("Seeding operational metrics...")
    seed_operational_metrics(db)
    
    print("Seeding dashboard segments...")
    seed_dashboard_segments(db)
    
    print("Seeding dashboard widgets...")
    seed_dashboard_widgets(db)
    
    print("Dashboard seeding completed!")


if __name__ == "__main__":
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        seed_all_dashboard_data(db)
    finally:
        db.close()

"""Dashboard widget model for configurable dashboard layouts."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class DashboardWidget(Base):
    """
    Configurable dashboard widgets that can display metrics in various formats.
    Supports charts, tables, gauges, and custom visualizations.
    """
    __tablename__ = "dashboard_widgets"

    id = Column(Integer, primary_key=True, index=True)
    
    # Widget identification
    widget_key = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)  # 'financial', 'network', 'customer', 'operational'
    
    # Widget configuration
    widget_type = Column(String(50), nullable=False)  # 'chart', 'metric', 'table', 'gauge', 'map', 'custom'
    chart_type = Column(String(50))  # 'line', 'bar', 'pie', 'donut', 'area', 'scatter', 'heatmap'
    
    # Data configuration
    metrics = Column(JSONB, nullable=False)  # List of metric keys to display
    # Example: ["arpu", "churn_rate", "total_customers"]
    
    # Display configuration
    display_config = Column(JSONB)
    # Examples:
    # Chart: {"x_axis": "date", "y_axis": "value", "colors": ["#007bff", "#28a745"], "show_legend": true}
    # Table: {"columns": ["metric", "value", "change"], "sortable": true, "paginated": false}
    # Gauge: {"min_value": 0, "max_value": 100, "thresholds": [{"value": 80, "color": "green"}]}
    
    # Layout configuration
    position = Column(JSONB)  # Grid position and size
    # Example: {"row": 1, "col": 1, "width": 6, "height": 4, "min_width": 3, "min_height": 2}
    
    # Filtering and segmentation
    default_filters = Column(JSONB)  # Default filters applied to widget data
    available_segments = Column(JSONB)  # Segments available for user selection
    
    # Refresh configuration
    refresh_interval_seconds = Column(Integer, default=300)  # 5 minutes
    auto_refresh = Column(Boolean, default=True)
    
    # Access control
    visibility_roles = Column(JSONB)  # ["admin", "manager", "viewer"]
    tenant_scope = Column(String(50))  # 'global', 'reseller', 'customer'
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<DashboardWidget(key='{self.widget_key}', type='{self.widget_type}')>"

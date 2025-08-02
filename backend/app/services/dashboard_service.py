"""Dashboard service for dynamic metrics and KPI calculations."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text, or_
from sqlalchemy.orm import Session

from app.models.dashboard import (
    MetricDefinition,
    DataSourceConfig,
    SegmentDefinition,
    DashboardWidget,
    ThresholdDefinition
)


class DashboardService:
    """Service for dynamic dashboard metrics and KPI calculations."""
    
    def __init__(self, db: Session):
        self.db = db
        self._cache = {}  # Simple in-memory cache
    
    def get_metric_definitions(
        self, 
        categories: Optional[List[str]] = None,
        metric_keys: Optional[List[str]] = None,
        tenant_scope: Optional[str] = None,
        user_roles: Optional[List[str]] = None
    ) -> List[MetricDefinition]:
        """Get metric definitions with optional filtering."""
        query = self.db.query(MetricDefinition).filter(MetricDefinition.is_active == True)
        
        if categories:
            query = query.filter(MetricDefinition.category.in_(categories))
        
        if metric_keys:
            query = query.filter(MetricDefinition.metric_key.in_(metric_keys))
        
        if tenant_scope:
            query = query.filter(
                (MetricDefinition.tenant_scope == tenant_scope) |
                (MetricDefinition.tenant_scope == 'global')
            )
        
        # Apply RBAC filtering
        if user_roles:
            # Filter metrics based on visibility_roles
            # For PostgreSQL JSON array queries, we need to check each role individually
            role_conditions = []
            for role in user_roles:
                role_conditions.append(MetricDefinition.visibility_roles.op('?')(role))
            
            if role_conditions:
                query = query.filter(
                    (MetricDefinition.visibility_roles.is_(None)) |
                    or_(*role_conditions)
                )
        
        return query.all()
    
    def calculate_metric(
        self,
        config: MetricDefinition,
        period: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate a single metric based on its configuration."""
        
        # Check cache first
        cache_key = self._generate_cache_key(config.metric_key, period, start_date, end_date, filters)
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < timedelta(seconds=config.cache_ttl_seconds):
                return cached_result['data']
        
        # Calculate date range if not provided
        if not start_date or not end_date:
            start_date, end_date = self._get_period_dates(period)
        
        try:
            if config.calculation_method == "custom_sql":
                value = self._execute_custom_sql(config, start_date, end_date, filters)
            else:
                value = self._calculate_standard_metric(config, start_date, end_date, filters)
            
            result = {
                "metric_key": config.metric_key,
                "metric_name": config.metric_name,
                "value": value,
                "unit": config.unit,
                "display_format": config.display_format,
                "category": config.category,
                "period": period,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "calculated_at": datetime.now().isoformat()
            }
            
            # Cache the result
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            return {
                "metric_key": config.metric_key,
                "metric_name": config.metric_name,
                "value": None,
                "error": str(e),
                "calculated_at": datetime.now().isoformat()
            }
    
    def _calculate_standard_metric(
        self,
        config: MetricDefinition,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> Union[int, float]:
        """Calculate metrics using standard methods (sum, avg, count, ratio)."""
        
        # Build base query
        if config.calculation_method == "count":
            query = f"SELECT COUNT({config.source_column or '*'}) as value FROM {config.source_table}"
        elif config.calculation_method == "sum":
            query = f"SELECT COALESCE(SUM({config.source_column}), 0) as value FROM {config.source_table}"
        elif config.calculation_method == "avg":
            query = f"SELECT COALESCE(AVG({config.source_column}), 0) as value FROM {config.source_table}"
        else:
            raise ValueError(f"Unsupported calculation method: {config.calculation_method}")
        
        # Add WHERE conditions
        where_conditions = []
        params = {}
        
        # Add date filtering if the table has created_at column
        if start_date and end_date:
            where_conditions.append("created_at >= :start_date AND created_at <= :end_date")
            params['start_date'] = start_date
            params['end_date'] = end_date
        
        # Add configured filters
        if config.filters:
            for key, value in config.filters.items():
                if isinstance(value, list):
                    placeholders = ','.join([f":filter_{key}_{i}" for i in range(len(value))])
                    where_conditions.append(f"{key} IN ({placeholders})")
                    for i, v in enumerate(value):
                        params[f'filter_{key}_{i}'] = v
                else:
                    where_conditions.append(f"{key} = :filter_{key}")
                    params[f'filter_{key}'] = value
        
        # Add additional filters
        if filters:
            for key, value in filters.items():
                where_conditions.append(f"{key} = :additional_{key}")
                params[f'additional_{key}'] = value
        
        # Add JOIN clauses if configured
        if config.joins:
            for join_config in config.joins:
                query += f" JOIN {join_config['table']} ON {join_config['on']}"
        
        # Add WHERE clause
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Execute query
        result = self.db.execute(text(query), params)
        row = result.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0
    
    def _execute_custom_sql(
        self,
        config: MetricDefinition,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> Union[int, float]:
        """Execute custom SQL for complex metrics."""
        
        # Prepare parameters for custom SQL
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        if filters:
            params.update(filters)
        
        # Execute custom SQL
        result = self.db.execute(text(config.custom_sql), params)
        row = result.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0
    
    def get_kpis(
        self,
        categories: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        period: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        segments: Optional[List[str]] = None,
        tenant_scope: Optional[str] = None,
        user_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get multiple KPIs with optional filtering and segmentation."""
        
        # Get metric definitions
        metric_configs = self.get_metric_definitions(
            categories=categories,
            metric_keys=metrics,
            tenant_scope=tenant_scope,
            user_roles=user_roles
        )
        
        # Apply segmentation filters
        segment_filters = self.get_segment_filters(segments) if segments else {}
        
        # Calculate all metrics
        results = {}
        for config in metric_configs:
            result = self.calculate_metric(
                config=config,
                period=period,
                start_date=start_date,
                end_date=end_date,
                filters=segment_filters
            )
            results[config.metric_key] = result
        
        return {
            "kpis": results,
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "segments": segments or [],
            "calculated_at": datetime.now().isoformat()
        }
    
    def get_financial_report(
        self,
        period: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        breakdown_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate financial report with breakdowns."""
        
        financial_metrics = self.get_metric_definitions(categories=["financial"])
        
        report = {
            "summary": {},
            "breakdown": {},
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "generated_at": datetime.now().isoformat()
        }
        
        # Calculate summary metrics
        for config in financial_metrics:
            result = self.calculate_metric(config, period, start_date, end_date)
            report["summary"][config.metric_key] = result
        
        # Add breakdown if requested
        if breakdown_by:
            report["breakdown"] = self._generate_breakdown(
                financial_metrics, breakdown_by, period, start_date, end_date
            )
        
        return report
    
    def get_network_report(
        self,
        period: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate network performance report."""
        
        network_metrics = self.get_metric_definitions(categories=["network"])
        
        report = {
            "summary": {},
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "generated_at": datetime.now().isoformat()
        }
        
        # Calculate network metrics
        for config in network_metrics:
            result = self.calculate_metric(config, period, start_date, end_date)
            report["summary"][config.metric_key] = result
        
        return report
    
    def get_segment_filters(self, segment_keys: List[str]) -> Dict[str, Any]:
        """Get filters for specified segments."""
        segments = self.db.query(SegmentDefinition).filter(
            SegmentDefinition.segment_key.in_(segment_keys),
            SegmentDefinition.is_active == True
        ).all()
        
        filters = {}
        for segment in segments:
            # Convert segment criteria to SQL filters
            # This is a simplified implementation
            if segment.criteria:
                for key, condition in segment.criteria.items():
                    operator = condition.get('operator', '=')
                    value = condition.get('value')
                    
                    if operator == '=':
                        filters[key] = value
                    elif operator == 'in':
                        filters[key] = value
                    # Add more operators as needed
        
        return filters
    
    def get_dashboard_widgets(
        self,
        categories: Optional[List[str]] = None,
        user_roles: Optional[List[str]] = None,
        tenant_scope: Optional[str] = None
    ) -> List[DashboardWidget]:
        """Get dashboard widgets with RBAC filtering."""
        query = self.db.query(DashboardWidget).filter(DashboardWidget.is_active == True)
        
        if categories:
            query = query.filter(DashboardWidget.category.in_(categories))
        
        if tenant_scope:
            query = query.filter(
                (DashboardWidget.tenant_scope == tenant_scope) |
                (DashboardWidget.tenant_scope == 'global')
            )
        
        if user_roles:
            # For PostgreSQL JSON array queries, we need to check each role individually
            role_conditions = []
            for role in user_roles:
                role_conditions.append(DashboardWidget.visibility_roles.op('?')(role))
            
            if role_conditions:
                query = query.filter(
                    (DashboardWidget.visibility_roles.is_(None)) |
                    or_(*role_conditions)
                )
        
        return query.all()
    
    def _get_period_dates(self, period: str) -> tuple[datetime, datetime]:
        """Get start and end dates for a period."""
        now = datetime.now()
        
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
        elif period == "week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7) - timedelta(microseconds=1)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1) - timedelta(microseconds=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1) - timedelta(microseconds=1)
        elif period == "quarter":
            quarter = (now.month - 1) // 3 + 1
            start_date = now.replace(month=(quarter - 1) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(month=start_date.month + 3) - timedelta(microseconds=1)
        elif period == "year":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(year=start_date.year + 1) - timedelta(microseconds=1)
        else:
            # Default to current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1) - timedelta(microseconds=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1) - timedelta(microseconds=1)
        
        return start_date, end_date
    
    def _generate_cache_key(
        self,
        metric_key: str,
        period: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for metric calculation."""
        key_parts = [
            metric_key,
            period,
            start_date.isoformat() if start_date else "none",
            end_date.isoformat() if end_date else "none",
            json.dumps(filters, sort_keys=True) if filters else "none"
        ]
        return "|".join(key_parts)
    
    def _generate_breakdown(
        self,
        metrics: List[MetricDefinition],
        breakdown_by: str,
        period: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Generate breakdown analysis for metrics."""
        # This is a placeholder for breakdown logic
        # In a real implementation, you'd query data grouped by the breakdown dimension
        return {
            "breakdown_by": breakdown_by,
            "data": [],
            "note": "Breakdown functionality to be implemented based on specific requirements"
        }
    
    def clear_cache(self):
        """Clear the metric calculation cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys())
        }

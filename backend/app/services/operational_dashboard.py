"""
Operational Dashboard Service.

Provides comprehensive operational metrics, health monitoring, and dashboard data
for ISP Framework operations including error handling, dead-letter queue monitoring,
and system health metrics.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.models.foundation import DeadLetterQueue, TaskExecutionLog
from app.models.services.instances import CustomerService
from app.core.celery import get_active_tasks

logger = structlog.get_logger("isp.services.operational_dashboard")


class OperationalDashboardService:
    """Service for generating operational dashboard data and metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_system_health_overview(self) -> Dict[str, Any]:
        """Get comprehensive system health overview."""
        try:
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)
            
            # Dead Letter Queue Health
            dlq_stats = await self._get_dead_letter_queue_health()
            
            # Task Execution Health
            task_stats = await self._get_task_execution_health(last_24h)
            
            # Customer Service Health
            customer_stats = await self._get_customer_service_health()
            
            # Calculate overall health score
            health_score = self._calculate_health_score(dlq_stats, task_stats, customer_stats)
            
            return {
                'timestamp': now.isoformat(),
                'health_score': health_score,
                'status': self._get_health_status(health_score),
                'components': {
                    'dead_letter_queue': dlq_stats,
                    'task_execution': task_stats,
                    'customer_services': customer_stats
                },
                'alerts': await self._get_active_alerts(),
                'recommendations': await self._get_health_recommendations(dlq_stats, task_stats, customer_stats)
            }
            
        except Exception as e:
            logger.error("Failed to get system health overview", error=str(e))
            raise
    
    async def get_error_metrics_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive error metrics and trends."""
        try:
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # Dead Letter Queue Metrics
            dlq_metrics = await self._get_dlq_detailed_metrics(last_24h, last_7d)
            
            # Task Failure Trends
            task_trends = await self._get_task_failure_trends(last_7d)
            
            # Error Categories Analysis
            error_analysis = await self._get_error_category_analysis(last_7d)
            
            return {
                'timestamp': now.isoformat(),
                'summary': {
                    'total_errors_24h': dlq_metrics.get('failed_24h', 0) + dlq_metrics.get('error_24h', 0),
                    'total_errors_7d': dlq_metrics.get('failed_7d', 0) + dlq_metrics.get('error_7d', 0),
                    'recovery_rate': dlq_metrics.get('recovery_rate', 0)
                },
                'dead_letter_queue': dlq_metrics,
                'task_trends': task_trends,
                'error_analysis': error_analysis,
                'top_failing_tasks': await self._get_top_failing_tasks(last_7d)
            }
            
        except Exception as e:
            logger.error("Failed to get error metrics dashboard", error=str(e))
            raise
    
    async def get_operational_kpis(self) -> Dict[str, Any]:
        """Get key operational performance indicators."""
        try:
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # System Availability
            availability = await self._calculate_system_availability(last_24h, last_7d)
            
            # Task Success Rates
            task_success = await self._calculate_task_success_rates(last_24h)
            
            # Resource Utilization
            resource_util = await self._get_resource_utilization()
            
            return {
                'timestamp': now.isoformat(),
                'availability': availability,
                'task_success': task_success,
                'resource_utilization': resource_util
            }
            
        except Exception as e:
            logger.error("Failed to get operational KPIs", error=str(e))
            raise
    
    # Helper methods for health monitoring
    
    async def _get_dead_letter_queue_health(self) -> Dict[str, Any]:
        """Get dead letter queue health metrics."""
        try:
            pending_count = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.status == 'pending'
            ).count()
            
            failed_count = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.status == 'failed'
            ).count()
            
            requeued_count = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.status == 'requeued'
            ).count()
            
            recent_failures = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.failed_at >= datetime.now(timezone.utc) - timedelta(hours=1),
                DeadLetterQueue.status.in_(['pending', 'failed'])
            ).count()
            
            total_items = pending_count + failed_count + requeued_count
            if total_items == 0:
                health_score = 100
            else:
                failure_rate = (pending_count + failed_count) / total_items
                health_score = max(0, 100 - (failure_rate * 100))
            
            return {
                'health_score': round(health_score, 2),
                'status': 'healthy' if health_score >= 90 else 'warning' if health_score >= 70 else 'critical',
                'pending_count': pending_count,
                'failed_count': failed_count,
                'requeued_count': requeued_count,
                'recent_failures': recent_failures,
                'total_items': total_items
            }
            
        except Exception as e:
            logger.error("Failed to get DLQ health", error=str(e))
            return {'health_score': 0, 'status': 'error', 'error': str(e)}
    
    async def _get_task_execution_health(self, since: datetime) -> Dict[str, Any]:
        """Get task execution health metrics."""
        try:
            total_executions = self.db.query(TaskExecutionLog).filter(
                TaskExecutionLog.created_at >= since
            ).count()
            
            successful_executions = self.db.query(TaskExecutionLog).filter(
                TaskExecutionLog.created_at >= since,
                TaskExecutionLog.status == 'success'
            ).count()
            
            failed_executions = self.db.query(TaskExecutionLog).filter(
                TaskExecutionLog.created_at >= since,
                TaskExecutionLog.status == 'failed'
            ).count()
            
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 100
            
            avg_duration = self.db.query(func.avg(TaskExecutionLog.duration_seconds)).filter(
                TaskExecutionLog.created_at >= since,
                TaskExecutionLog.status == 'success'
            ).scalar() or 0
            
            return {
                'health_score': min(100, success_rate),
                'status': 'healthy' if success_rate >= 95 else 'warning' if success_rate >= 85 else 'critical',
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': round(success_rate, 2),
                'avg_duration_seconds': round(avg_duration, 2)
            }
            
        except Exception as e:
            logger.error("Failed to get task execution health", error=str(e))
            return {'health_score': 0, 'status': 'error', 'error': str(e)}
    
    async def _get_customer_service_health(self) -> Dict[str, Any]:
        """Get customer service health metrics."""
        try:
            active_services = self.db.query(CustomerService).filter(
                CustomerService.status == 'active'
            ).count()
            
            suspended_services = self.db.query(CustomerService).filter(
                CustomerService.status == 'suspended'
            ).count()
            
            failed_services = self.db.query(CustomerService).filter(
                CustomerService.status.in_(['provisioning_failed', 'failed'])
            ).count()
            
            total_services = active_services + suspended_services + failed_services
            
            if total_services == 0:
                health_score = 100
            else:
                active_rate = active_services / total_services
                health_score = active_rate * 100
            
            return {
                'health_score': round(health_score, 2),
                'status': 'healthy' if health_score >= 90 else 'warning' if health_score >= 70 else 'critical',
                'active_services': active_services,
                'suspended_services': suspended_services,
                'failed_services': failed_services,
                'total_services': total_services
            }
            
        except Exception as e:
            logger.error("Failed to get customer service health", error=str(e))
            return {'health_score': 0, 'status': 'error', 'error': str(e)}
    
    def _calculate_health_score(self, *component_stats) -> float:
        """Calculate overall system health score."""
        try:
            scores = []
            weights = [0.4, 0.35, 0.25]  # DLQ, Tasks, Customer Services
            
            for i, stats in enumerate(component_stats):
                if isinstance(stats, dict) and 'health_score' in stats:
                    weight = weights[i] if i < len(weights) else 0.1
                    scores.append(stats['health_score'] * weight)
            
            return round(sum(scores), 2) if scores else 0
            
        except Exception as e:
            logger.error("Failed to calculate health score", error=str(e))
            return 0
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status based on score."""
        if health_score >= 90:
            return 'healthy'
        elif health_score >= 70:
            return 'warning'
        else:
            return 'critical'
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active system alerts."""
        try:
            alerts = []
            
            pending_dlq = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.status == 'pending'
            ).count()
            
            if pending_dlq > 10:
                alerts.append({
                    'severity': 'high',
                    'category': 'dead_letter_queue',
                    'message': f'{pending_dlq} tasks pending in dead letter queue',
                    'action': 'Review and retry failed tasks'
                })
            
            recent_critical = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.failed_at >= datetime.now(timezone.utc) - timedelta(hours=1),
                DeadLetterQueue.retry_count >= 3
            ).count()
            
            if recent_critical > 0:
                alerts.append({
                    'severity': 'critical',
                    'category': 'task_failures',
                    'message': f'{recent_critical} critical task failures in the last hour',
                    'action': 'Investigate root cause immediately'
                })
            
            return alerts
            
        except Exception as e:
            logger.error("Failed to get active alerts", error=str(e))
            return []
    
    async def _get_health_recommendations(self, *component_stats) -> List[str]:
        """Get health improvement recommendations."""
        try:
            recommendations = []
            
            dlq_stats = component_stats[0] if len(component_stats) > 0 else {}
            if dlq_stats.get('health_score', 100) < 80:
                recommendations.append("Review and retry pending dead letter queue items")
                recommendations.append("Investigate root causes of task failures")
            
            task_stats = component_stats[1] if len(component_stats) > 1 else {}
            if task_stats.get('success_rate', 100) < 90:
                recommendations.append("Optimize task execution performance")
                recommendations.append("Review task timeout and retry configurations")
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to get health recommendations", error=str(e))
            return []
    
    # Additional helper methods for detailed metrics
    
    async def _get_dlq_detailed_metrics(self, last_24h: datetime, last_7d: datetime) -> Dict[str, Any]:
        """Get detailed dead letter queue metrics."""
        try:
            failed_24h = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.failed_at >= last_24h,
                DeadLetterQueue.status == 'failed'
            ).count()
            
            failed_7d = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.failed_at >= last_7d,
                DeadLetterQueue.status == 'failed'
            ).count()
            
            error_24h = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.failed_at >= last_24h,
                DeadLetterQueue.status == 'error'
            ).count()
            
            error_7d = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.failed_at >= last_7d,
                DeadLetterQueue.status == 'error'
            ).count()
            
            requeued_7d = self.db.query(DeadLetterQueue).filter(
                DeadLetterQueue.requeued_at >= last_7d
            ).count()
            
            total_failed_7d = failed_7d + error_7d
            recovery_rate = (requeued_7d / total_failed_7d * 100) if total_failed_7d > 0 else 0
            
            return {
                'failed_24h': failed_24h,
                'failed_7d': failed_7d,
                'error_24h': error_24h,
                'error_7d': error_7d,
                'requeued_7d': requeued_7d,
                'recovery_rate': round(recovery_rate, 2)
            }
            
        except Exception as e:
            logger.error("Failed to get DLQ detailed metrics", error=str(e))
            return {}
    
    async def _get_task_failure_trends(self, last_7d: datetime) -> List[Dict[str, Any]]:
        """Get task failure trends over time."""
        try:
            trends = []
            for i in range(7):
                day_start = last_7d + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                failures = self.db.query(DeadLetterQueue).filter(
                    DeadLetterQueue.failed_at >= day_start,
                    DeadLetterQueue.failed_at < day_end
                ).count()
                
                trends.append({
                    'date': day_start.date().isoformat(),
                    'failures': failures
                })
            
            return trends
            
        except Exception as e:
            logger.error("Failed to get task failure trends", error=str(e))
            return []
    
    async def _get_error_category_analysis(self, last_7d: datetime) -> Dict[str, Any]:
        """Get error analysis by category."""
        try:
            failures_by_task = self.db.query(
                DeadLetterQueue.task_name,
                func.count(DeadLetterQueue.id).label('count')
            ).filter(
                DeadLetterQueue.failed_at >= last_7d
            ).group_by(DeadLetterQueue.task_name).all()
            
            return {
                'by_task': [{'task_name': task, 'count': count} for task, count in failures_by_task],
                'total_categories': len(failures_by_task)
            }
            
        except Exception as e:
            logger.error("Failed to get error category analysis", error=str(e))
            return {}
    
    async def _get_top_failing_tasks(self, last_7d: datetime) -> List[Dict[str, Any]]:
        """Get top failing tasks."""
        try:
            top_failing = self.db.query(
                DeadLetterQueue.task_name,
                func.count(DeadLetterQueue.id).label('failure_count')
            ).filter(
                DeadLetterQueue.failed_at >= last_7d
            ).group_by(DeadLetterQueue.task_name).order_by(
                func.count(DeadLetterQueue.id).desc()
            ).limit(5).all()
            
            return [{'task_name': task, 'failure_count': count} for task, count in top_failing]
            
        except Exception as e:
            logger.error("Failed to get top failing tasks", error=str(e))
            return []
    
    async def _calculate_system_availability(self, last_24h: datetime, last_7d: datetime) -> Dict[str, Any]:
        """Calculate system availability metrics."""
        try:
            total_tasks_24h = self.db.query(TaskExecutionLog).filter(
                TaskExecutionLog.created_at >= last_24h
            ).count()
            
            successful_tasks_24h = self.db.query(TaskExecutionLog).filter(
                TaskExecutionLog.created_at >= last_24h,
                TaskExecutionLog.status == 'success'
            ).count()
            
            availability_24h = (successful_tasks_24h / total_tasks_24h * 100) if total_tasks_24h > 0 else 100
            
            total_tasks_7d = self.db.query(TaskExecutionLog).filter(
                TaskExecutionLog.created_at >= last_7d
            ).count()
            
            successful_tasks_7d = self.db.query(TaskExecutionLog).filter(
                TaskExecutionLog.created_at >= last_7d,
                TaskExecutionLog.status == 'success'
            ).count()
            
            availability_7d = (successful_tasks_7d / total_tasks_7d * 100) if total_tasks_7d > 0 else 100
            
            return {
                'availability_24h': round(availability_24h, 2),
                'availability_7d': round(availability_7d, 2),
                'uptime_percentage': round(availability_7d, 2),
                'sla_target': 99.9
            }
            
        except Exception as e:
            logger.error("Failed to calculate system availability", error=str(e))
            return {}
    
    async def _calculate_task_success_rates(self, last_24h: datetime) -> Dict[str, Any]:
        """Calculate task success rates by category."""
        try:
            task_categories = [
                'service_provisioning',
                'customer_notifications', 
                'billing_tasks',
                'network_tasks',
                'monitoring_tasks'
            ]
            
            success_rates = {}
            for category in task_categories:
                total = self.db.query(TaskExecutionLog).filter(
                    TaskExecutionLog.created_at >= last_24h,
                    TaskExecutionLog.task_name.contains(category)
                ).count()
                
                successful = self.db.query(TaskExecutionLog).filter(
                    TaskExecutionLog.created_at >= last_24h,
                    TaskExecutionLog.task_name.contains(category),
                    TaskExecutionLog.status == 'success'
                ).count()
                
                success_rates[category] = round((successful / total * 100) if total > 0 else 100, 2)
            
            return success_rates
            
        except Exception as e:
            logger.error("Failed to calculate task success rates", error=str(e))
            return {}
    
    async def _get_resource_utilization(self) -> Dict[str, Any]:
        """Get resource utilization metrics."""
        try:
            # Get active Celery tasks
            active_tasks = get_active_tasks()
            
            # Calculate basic utilization metrics
            total_workers = len(active_tasks.get('active', {})) if active_tasks.get('active') else 0
            total_active_tasks = sum(len(tasks) for tasks in active_tasks.get('active', {}).values()) if active_tasks.get('active') else 0
            
            return {
                'active_workers': total_workers,
                'active_tasks': total_active_tasks,
                'queue_utilization': min(100, (total_active_tasks / max(1, total_workers * 10)) * 100),
                'memory_usage': 'N/A',  # Would integrate with system monitoring
                'cpu_usage': 'N/A'      # Would integrate with system monitoring
            }
            
        except Exception as e:
            logger.error("Failed to get resource utilization", error=str(e))
            return {}

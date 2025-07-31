"""
System Monitoring and Alerting Tasks
Background tasks for system health monitoring, alerting, and performance tracking
"""

from datetime import datetime

import structlog

from app.core.celery import celery_app
from app.core.database import get_db
from app.services.monitoring import MonitoringService

logger = structlog.get_logger("isp.tasks.monitoring")


@celery_app.task(bind=True, name="monitoring.system_health_check")
def system_health_check_task(self):
    """Perform comprehensive system health check."""
    try:
        logger.info("Starting system health check")

        db = next(get_db())
        monitoring_service = MonitoringService(db)

        result = monitoring_service.perform_system_health_check()

        logger.info(
            "System health check completed",
            components_checked=result.get("components_checked", 0),
            healthy_components=result.get("healthy_components", 0),
            unhealthy_components=result.get("unhealthy_components", 0),
        )

        return {
            "status": "success",
            "components_checked": result.get("components_checked", 0),
            "healthy_components": result.get("healthy_components", 0),
            "unhealthy_components": result.get("unhealthy_components", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("System health check failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="monitoring.collect_performance_metrics")
def collect_performance_metrics_task(self):
    """Collect system performance metrics."""
    try:
        logger.info("Starting performance metrics collection")

        db = next(get_db())
        monitoring_service = MonitoringService(db)

        result = monitoring_service.collect_performance_metrics()

        logger.info(
            "Performance metrics collection completed",
            metrics_collected=result.get("metrics_collected", 0),
        )

        return {
            "status": "success",
            "metrics_collected": result.get("metrics_collected", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("Performance metrics collection failed", error=str(exc))
        raise self.retry(exc=exc, countdown=180, max_retries=5)


@celery_app.task(bind=True, name="monitoring.check_service_sla")
def check_service_sla_task(self, service_id: int = None):
    """Check SLA compliance for services."""
    try:
        logger.info("Starting SLA compliance check", service_id=service_id)

        db = next(get_db())
        monitoring_service = MonitoringService(db)

        if service_id:
            result = monitoring_service.check_service_sla(service_id)
        else:
            result = monitoring_service.check_all_services_sla()

        logger.info(
            "SLA compliance check completed",
            services_checked=result.get("services_checked", 0),
            sla_violations=result.get("sla_violations", 0),
        )

        return {
            "status": "success",
            "services_checked": result.get("services_checked", 0),
            "sla_violations": result.get("sla_violations", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("SLA compliance check failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="monitoring.generate_alerts")
def generate_alerts_task(self, alert_type: str = None):
    """Generate system alerts based on monitoring data."""
    try:
        logger.info("Starting alert generation", alert_type=alert_type)

        db = next(get_db())
        monitoring_service = MonitoringService(db)

        result = monitoring_service.generate_alerts(alert_type)

        logger.info(
            "Alert generation completed",
            alerts_generated=result.get("alerts_generated", 0),
            critical_alerts=result.get("critical_alerts", 0),
        )

        return {
            "status": "success",
            "alerts_generated": result.get("alerts_generated", 0),
            "critical_alerts": result.get("critical_alerts", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("Alert generation failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="monitoring.cleanup_old_metrics")
def cleanup_old_metrics_task(self, retention_days: int = 90):
    """Clean up old monitoring metrics and logs."""
    try:
        logger.info("Starting metrics cleanup", retention_days=retention_days)

        db = next(get_db())
        monitoring_service = MonitoringService(db)

        result = monitoring_service.cleanup_old_metrics(retention_days)

        logger.info(
            "Metrics cleanup completed",
            records_cleaned=result.get("records_cleaned", 0),
            space_freed_mb=result.get("space_freed_mb", 0),
        )

        return {
            "status": "success",
            "records_cleaned": result.get("records_cleaned", 0),
            "space_freed_mb": result.get("space_freed_mb", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("Metrics cleanup failed", error=str(exc))
        raise self.retry(exc=exc, countdown=600, max_retries=2)


@celery_app.task(bind=True, name="monitoring.bandwidth_usage_analysis")
def bandwidth_usage_analysis_task(self, customer_id: int = None):
    """Analyze bandwidth usage patterns."""
    try:
        logger.info("Starting bandwidth usage analysis", customer_id=customer_id)

        db = next(get_db())
        monitoring_service = MonitoringService(db)

        if customer_id:
            result = monitoring_service.analyze_customer_bandwidth(customer_id)
        else:
            result = monitoring_service.analyze_all_bandwidth_usage()

        logger.info(
            "Bandwidth usage analysis completed",
            customers_analyzed=result.get("customers_analyzed", 0),
            usage_anomalies=result.get("usage_anomalies", 0),
        )

        return {
            "status": "success",
            "customers_analyzed": result.get("customers_analyzed", 0),
            "usage_anomalies": result.get("usage_anomalies", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("Bandwidth usage analysis failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


# Scheduled monitoring tasks
@celery_app.task(bind=True, name="monitoring.every_5_minutes")
def every_5_minutes_monitoring(self):
    """Run monitoring tasks every 5 minutes."""
    try:
        logger.info("Starting 5-minute monitoring cycle")

        results = {}

        # System health check
        health_result = system_health_check_task.delay()
        results["health_check"] = health_result.id

        # Collect performance metrics
        metrics_result = collect_performance_metrics_task.delay()
        results["metrics_collection"] = metrics_result.id

        logger.info("5-minute monitoring tasks scheduled", task_ids=results)

        return {
            "status": "success",
            "scheduled_tasks": results,
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("5-minute monitoring cycle failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=2)


@celery_app.task(bind=True, name="monitoring.hourly_monitoring")
def hourly_monitoring_task(self):
    """Run monitoring tasks every hour."""
    try:
        logger.info("Starting hourly monitoring cycle")

        results = {}

        # SLA compliance check
        sla_result = check_service_sla_task.delay()
        results["sla_check"] = sla_result.id

        # Generate alerts
        alerts_result = generate_alerts_task.delay()
        results["alert_generation"] = alerts_result.id

        # Bandwidth analysis
        bandwidth_result = bandwidth_usage_analysis_task.delay()
        results["bandwidth_analysis"] = bandwidth_result.id

        logger.info("Hourly monitoring tasks scheduled", task_ids=results)

        return {
            "status": "success",
            "scheduled_tasks": results,
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("Hourly monitoring cycle failed", error=str(exc))
        raise self.retry(exc=exc, countdown=900, max_retries=2)


@celery_app.task(bind=True, name="monitoring.daily_cleanup")
def daily_cleanup_task(self):
    """Run daily monitoring cleanup tasks."""
    try:
        logger.info("Starting daily monitoring cleanup")

        results = {}

        # Clean up old metrics (keep 90 days)
        cleanup_result = cleanup_old_metrics_task.delay(90)
        results["metrics_cleanup"] = cleanup_result.id

        logger.info("Daily cleanup tasks scheduled", task_ids=results)

        return {
            "status": "success",
            "scheduled_tasks": results,
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("Daily cleanup tasks failed", error=str(exc))
        raise self.retry(exc=exc, countdown=1800, max_retries=2)

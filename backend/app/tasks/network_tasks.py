"""
Network Operations and Monitoring Tasks
Background tasks for network device management, monitoring, and automation
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_app
from sqlalchemy.orm import Session

from app.core.celery import celery_app
from app.core.database import get_db
from app.models.networking.networks import NetworkDevice, Site
from app.models.networking.radius import RadiusSession
from app.services.networking import NetworkService
import structlog

logger = structlog.get_logger("isp.tasks.network")


@celery_app.task(bind=True, name="network.device_health_check")
def device_health_check_task(self, device_id: int = None):
    """Perform health checks on network devices."""
    try:
        logger.info("Starting device health check", device_id=device_id)
        
        db = next(get_db())
        network_service = NetworkService(db)
        
        if device_id:
            result = network_service.check_device_health(device_id)
        else:
            result = network_service.check_all_devices_health()
        
        logger.info("Device health check completed",
                   devices_checked=result.get('devices_checked', 0),
                   devices_healthy=result.get('devices_healthy', 0),
                   devices_unhealthy=result.get('devices_unhealthy', 0))
        
        return {
            "status": "success",
            "devices_checked": result.get('devices_checked', 0),
            "devices_healthy": result.get('devices_healthy', 0),
            "devices_unhealthy": result.get('devices_unhealthy', 0),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Device health check failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="network.collect_device_metrics")
def collect_device_metrics_task(self, device_id: int = None):
    """Collect performance metrics from network devices."""
    try:
        logger.info("Starting device metrics collection", device_id=device_id)
        
        db = next(get_db())
        network_service = NetworkService(db)
        
        if device_id:
            result = network_service.collect_device_metrics(device_id)
        else:
            result = network_service.collect_all_device_metrics()
        
        logger.info("Device metrics collection completed",
                   devices_processed=result.get('devices_processed', 0),
                   metrics_collected=result.get('metrics_collected', 0))
        
        return {
            "status": "success",
            "devices_processed": result.get('devices_processed', 0),
            "metrics_collected": result.get('metrics_collected', 0),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Device metrics collection failed", error=str(exc))
        raise self.retry(exc=exc, countdown=180, max_retries=5)


@celery_app.task(bind=True, name="network.backup_device_configs")
def backup_device_configs_task(self, device_id: int = None):
    """Backup network device configurations."""
    try:
        logger.info("Starting device config backup", device_id=device_id)
        
        db = next(get_db())
        network_service = NetworkService(db)
        
        if device_id:
            result = network_service.backup_device_config(device_id)
        else:
            result = network_service.backup_all_device_configs()
        
        logger.info("Device config backup completed",
                   devices_backed_up=result.get('devices_backed_up', 0),
                   backup_size_mb=result.get('backup_size_mb', 0))
        
        return {
            "status": "success",
            "devices_backed_up": result.get('devices_backed_up', 0),
            "backup_size_mb": result.get('backup_size_mb', 0),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Device config backup failed", error=str(exc))
        raise self.retry(exc=exc, countdown=600, max_retries=2)


@celery_app.task(bind=True, name="network.radius_session_cleanup")
def radius_session_cleanup_task(self, max_age_hours: int = 24):
    """Clean up old RADIUS sessions and accounting records."""
    try:
        logger.info("Starting RADIUS session cleanup", max_age_hours=max_age_hours)
        
        db = next(get_db())
        network_service = NetworkService(db)
        
        result = network_service.cleanup_radius_sessions(max_age_hours)
        
        logger.info("RADIUS session cleanup completed",
                   sessions_cleaned=result.get('sessions_cleaned', 0),
                   records_archived=result.get('records_archived', 0))
        
        return {
            "status": "success",
            "sessions_cleaned": result.get('sessions_cleaned', 0),
            "records_archived": result.get('records_archived', 0),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("RADIUS session cleanup failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="network.update_device_firmware")
def update_device_firmware_task(self, device_id: int, firmware_version: str):
    """Update firmware on network devices."""
    try:
        logger.info("Starting device firmware update", 
                   device_id=device_id, 
                   firmware_version=firmware_version)
        
        db = next(get_db())
        network_service = NetworkService(db)
        
        result = network_service.update_device_firmware(device_id, firmware_version)
        
        logger.info("Device firmware update completed",
                   device_id=device_id,
                   update_successful=result.get('update_successful', False))
        
        return {
            "status": "success",
            "device_id": device_id,
            "firmware_version": firmware_version,
            "update_successful": result.get('update_successful', False),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Device firmware update failed", 
                    device_id=device_id, 
                    error=str(exc))
        raise self.retry(exc=exc, countdown=1800, max_retries=2)


@celery_app.task(bind=True, name="network.network_discovery")
def network_discovery_task(self, subnet: str = None):
    """Discover new devices on the network."""
    try:
        logger.info("Starting network discovery", subnet=subnet)
        
        db = next(get_db())
        network_service = NetworkService(db)
        
        result = network_service.discover_network_devices(subnet)
        
        logger.info("Network discovery completed",
                   devices_discovered=result.get('devices_discovered', 0),
                   new_devices=result.get('new_devices', 0))
        
        return {
            "status": "success",
            "devices_discovered": result.get('devices_discovered', 0),
            "new_devices": result.get('new_devices', 0),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Network discovery failed", error=str(exc))
        raise self.retry(exc=exc, countdown=600, max_retries=2)


# Scheduled tasks
@celery_app.task(bind=True, name="network.hourly_monitoring")
def hourly_monitoring_task(self):
    """Run hourly network monitoring tasks."""
    try:
        logger.info("Starting hourly network monitoring")
        
        results = {}
        
        # Device health checks
        health_result = device_health_check_task.delay()
        results['health_check'] = health_result.id
        
        # Collect metrics
        metrics_result = collect_device_metrics_task.delay()
        results['metrics_collection'] = metrics_result.id
        
        logger.info("Hourly monitoring tasks scheduled", task_ids=results)
        
        return {
            "status": "success",
            "scheduled_tasks": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Hourly monitoring tasks failed", error=str(exc))
        raise self.retry(exc=exc, countdown=900, max_retries=2)


@celery_app.task(bind=True, name="network.daily_maintenance")
def daily_maintenance_task(self):
    """Run daily network maintenance tasks."""
    try:
        logger.info("Starting daily network maintenance")
        
        results = {}
        
        # Backup device configs
        backup_result = backup_device_configs_task.delay()
        results['config_backup'] = backup_result.id
        
        # Clean up RADIUS sessions
        cleanup_result = radius_session_cleanup_task.delay(24)
        results['radius_cleanup'] = cleanup_result.id
        
        # Network discovery
        discovery_result = network_discovery_task.delay()
        results['network_discovery'] = discovery_result.id
        
        logger.info("Daily maintenance tasks scheduled", task_ids=results)
        
        return {
            "status": "success",
            "scheduled_tasks": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Daily maintenance tasks failed", error=str(exc))
        raise self.retry(exc=exc, countdown=1800, max_retries=2)

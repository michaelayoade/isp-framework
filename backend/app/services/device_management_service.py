"""
Device Management Service Layer

This service provides business logic for network device management including:
- Device discovery and registration
- SNMP monitoring and data collection
- Configuration backup and restore
- Health monitoring and alerting
- Performance analysis and reporting
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models.devices.device_management import (
    AlertSeverity,
    BackupStatus,
    DeviceAlert,
    DeviceConfigBackup,
    DeviceMonitoring,
    DeviceStatus,
    DeviceType,
    ManagedDevice,
)

logger = logging.getLogger(__name__)


class DeviceDiscoveryService:
    """Service for discovering and registering network devices"""

    def __init__(self, db: Session):
        self.db = db

    async def discover_devices_by_subnet(
        self, subnet: str, snmp_community: str = "public"
    ) -> List[ManagedDevice]:
        """Discover devices in a subnet using SNMP"""
        discovered_devices = []

        # Implementation would use libraries like pysnmp, nmap, etc.
        # This is a placeholder for the discovery logic
        logger.info(f"Starting device discovery for subnet: {subnet}")

        # Placeholder: In real implementation, this would:
        # 1. Scan subnet for responsive IPs
        # 2. Try SNMP queries to identify devices
        # 3. Extract device information (hostname, model, etc.)
        # 4. Create ManagedDevice records

        return discovered_devices

    async def register_device(self, device_data: Dict[str, Any]) -> ManagedDevice:
        """Register a new network device"""
        device = ManagedDevice(
            hostname=device_data.get("hostname"),
            device_type=DeviceType(device_data.get("device_type", "other")),
            vendor=device_data.get("vendor"),
            model=device_data.get("model"),
            management_ip=device_data.get("management_ip"),
            snmp_community_ro=device_data.get("snmp_community", "public"),
            discovered_at=datetime.utcnow(),
        )

        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)

        logger.info(
            f"Registered new device: {device.hostname} ({device.management_ip})"
        )
        return device


class DeviceMonitoringService:
    """Service for device monitoring and data collection"""

    def __init__(self, db: Session):
        self.db = db

    async def collect_device_metrics(self, device_id: int) -> Dict[str, Any]:
        """Collect monitoring metrics from a device"""
        device = (
            self.db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
        )
        if not device:
            raise ValueError(f"Device {device_id} not found")

        metrics = {}

        try:
            # Placeholder for SNMP data collection
            # In real implementation, this would use pysnmp or similar
            if device.snmp_enabled:
                metrics.update(await self._collect_snmp_metrics(device))

            # Store metrics in database
            await self._store_metrics(device_id, metrics)

            # Update device last_seen
            device.last_seen = datetime.utcnow()
            device.status = DeviceStatus.UP
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to collect metrics from device {device_id}: {str(e)}")
            device.status = DeviceStatus.UNREACHABLE
            self.db.commit()

            # Create alert for unreachable device
            await self._create_alert(
                device_id,
                "device_unreachable",
                AlertSeverity.CRITICAL,
                f"Device {device.hostname} is unreachable",
                str(e),
            )

        return metrics

    async def _collect_snmp_metrics(self, device: ManagedDevice) -> Dict[str, Any]:
        """Collect SNMP metrics from device"""
        metrics = {}

        # Standard SNMP OIDs for common metrics

        # Placeholder for actual SNMP implementation
        # This would use pysnmp to query the device
        logger.info(f"Collecting SNMP metrics from {device.management_ip}")

        return metrics

    async def _store_metrics(self, device_id: int, metrics: Dict[str, Any]):
        """Store collected metrics in database"""
        timestamp = datetime.utcnow()

        for metric_name, value in metrics.items():
            monitoring_record = DeviceMonitoring(
                device_id=device_id,
                metric_name=metric_name,
                metric_value=float(value),
                collection_method="snmp",
                timestamp=timestamp,
            )
            self.db.add(monitoring_record)

        self.db.commit()

    async def get_device_performance_history(
        self, device_id: int, metric_name: str, hours: int = 24
    ) -> List[DeviceMonitoring]:
        """Get performance history for a device metric"""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        return (
            self.db.query(DeviceMonitoring)
            .filter(
                and_(
                    DeviceMonitoring.device_id == device_id,
                    DeviceMonitoring.metric_name == metric_name,
                    DeviceMonitoring.timestamp >= start_time,
                )
            )
            .order_by(DeviceMonitoring.timestamp)
            .all()
        )

    async def _create_alert(
        self,
        device_id: int,
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        description: str,
    ):
        """Create a device alert"""
        # Check if similar alert already exists and is active
        existing_alert = (
            self.db.query(DeviceAlert)
            .filter(
                and_(
                    DeviceAlert.device_id == device_id,
                    DeviceAlert.alert_type == alert_type,
                    DeviceAlert.is_active is True,
                )
            )
            .first()
        )

        if existing_alert:
            # Update existing alert
            existing_alert.description = description
            existing_alert.updated_at = datetime.utcnow()
        else:
            # Create new alert
            alert = DeviceAlert(
                device_id=device_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
            )
            self.db.add(alert)

        self.db.commit()


class DeviceConfigService:
    """Service for device configuration management"""

    def __init__(self, db: Session):
        self.db = db

    async def backup_device_config(
        self, device_id: int, backup_type: str = "full"
    ) -> DeviceConfigBackup:
        """Backup device configuration"""
        device = (
            self.db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
        )
        if not device:
            raise ValueError(f"Device {device_id} not found")

        backup = DeviceConfigBackup(
            device_id=device_id,
            backup_type=backup_type,
            backup_method="ssh",  # Default method
            backup_status=BackupStatus.IN_PROGRESS,
            backup_trigger="manual",
        )

        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)

        try:
            # Placeholder for actual config backup logic
            # This would use SSH, SNMP, or vendor APIs to retrieve config
            config_content = await self._retrieve_config(device)

            backup.config_content = config_content
            backup.file_size = len(config_content.encode("utf-8"))
            backup.backup_status = BackupStatus.SUCCESS
            backup.completed_at = datetime.utcnow()

            logger.info(f"Successfully backed up config for device {device.hostname}")

        except Exception as e:
            backup.backup_status = BackupStatus.FAILED
            backup.error_message = str(e)
            backup.completed_at = datetime.utcnow()

            logger.error(
                f"Failed to backup config for device {device.hostname}: {str(e)}"
            )

        self.db.commit()
        return backup

    async def _retrieve_config(self, device: ManagedDevice) -> str:
        """Retrieve configuration from device"""
        # Placeholder for actual config retrieval
        # This would implement SSH, SNMP, or API-based config retrieval
        logger.info(f"Retrieving config from {device.hostname}")

        # Return placeholder config
        return f"! Configuration for {device.hostname}\n! Retrieved at {datetime.utcnow()}\n"

    async def schedule_config_backups(self):
        """Schedule automatic config backups for devices"""
        devices = (
            self.db.query(ManagedDevice)
            .filter(ManagedDevice.config_backup_enabled is True)
            .all()
        )

        for device in devices:
            # Check if backup is due based on schedule
            if await self._is_backup_due(device):
                await self.backup_device_config(device.id, "scheduled")

    async def _is_backup_due(self, device: ManagedDevice) -> bool:
        """Check if device backup is due"""
        if not device.config_backup_schedule:
            return False

        # Get last successful backup
        last_backup = (
            self.db.query(DeviceConfigBackup)
            .filter(
                and_(
                    DeviceConfigBackup.device_id == device.id,
                    DeviceConfigBackup.backup_status == BackupStatus.SUCCESS,
                )
            )
            .order_by(desc(DeviceConfigBackup.completed_at))
            .first()
        )

        if not last_backup:
            return True  # No previous backup, so backup is due

        # Placeholder for cron schedule parsing
        # In real implementation, would parse cron expression and check if backup is due
        return False


class DeviceHealthService:
    """Service for device health monitoring and alerting"""

    def __init__(self, db: Session):
        self.db = db

    async def check_device_health(self, device_id: int) -> Dict[str, Any]:
        """Perform comprehensive health check on device"""
        device = (
            self.db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
        )
        if not device:
            raise ValueError(f"Device {device_id} not found")

        health_status = {
            "device_id": device_id,
            "hostname": device.hostname,
            "overall_status": "unknown",
            "checks": {},
        }

        # Connectivity check
        health_status["checks"]["connectivity"] = await self._check_connectivity(device)

        # SNMP check
        if device.snmp_enabled:
            health_status["checks"]["snmp"] = await self._check_snmp(device)

        # Performance checks
        health_status["checks"]["performance"] = (
            await self._check_performance_thresholds(device)
        )

        # Determine overall status
        health_status["overall_status"] = self._calculate_overall_health(
            health_status["checks"]
        )

        return health_status

    async def _check_connectivity(self, device: ManagedDevice) -> Dict[str, Any]:
        """Check device connectivity via ping"""
        # Placeholder for ping implementation
        return {"status": "ok", "response_time": 10.5, "packet_loss": 0}

    async def _check_snmp(self, device: ManagedDevice) -> Dict[str, Any]:
        """Check SNMP connectivity and response"""
        # Placeholder for SNMP check
        return {"status": "ok", "response_time": 50.2, "version": device.snmp_version}

    async def _check_performance_thresholds(
        self, device: ManagedDevice
    ) -> Dict[str, Any]:
        """Check if device performance metrics exceed thresholds"""
        # Get recent metrics
        recent_time = datetime.utcnow() - timedelta(minutes=15)
        recent_metrics = (
            self.db.query(DeviceMonitoring)
            .filter(
                and_(
                    DeviceMonitoring.device_id == device.id,
                    DeviceMonitoring.timestamp >= recent_time,
                )
            )
            .all()
        )

        performance_status = {"status": "ok", "warnings": [], "critical": []}

        # Check CPU usage
        cpu_metrics = [m for m in recent_metrics if m.metric_name == "cpu_usage"]
        if cpu_metrics:
            avg_cpu = sum(m.metric_value for m in cpu_metrics) / len(cpu_metrics)
            if avg_cpu > 90:
                performance_status["critical"].append(f"High CPU usage: {avg_cpu:.1f}%")
            elif avg_cpu > 80:
                performance_status["warnings"].append(
                    f"Elevated CPU usage: {avg_cpu:.1f}%"
                )

        # Check memory usage
        memory_metrics = [m for m in recent_metrics if m.metric_name == "memory_usage"]
        if memory_metrics:
            avg_memory = sum(m.metric_value for m in memory_metrics) / len(
                memory_metrics
            )
            if avg_memory > 95:
                performance_status["critical"].append(
                    f"High memory usage: {avg_memory:.1f}%"
                )
            elif avg_memory > 85:
                performance_status["warnings"].append(
                    f"Elevated memory usage: {avg_memory:.1f}%"
                )

        if performance_status["critical"]:
            performance_status["status"] = "critical"
        elif performance_status["warnings"]:
            performance_status["status"] = "warning"

        return performance_status

    def _calculate_overall_health(self, checks: Dict[str, Any]) -> str:
        """Calculate overall device health from individual checks"""
        if any(check.get("status") == "critical" for check in checks.values()):
            return "critical"
        elif any(check.get("status") == "warning" for check in checks.values()):
            return "warning"
        elif all(check.get("status") == "ok" for check in checks.values()):
            return "ok"
        else:
            return "unknown"


class DeviceManagementFactory:
    """Factory for creating device management services"""

    @staticmethod
    def get_discovery_service(db: Session) -> DeviceDiscoveryService:
        return DeviceDiscoveryService(db)

    @staticmethod
    def get_monitoring_service(db: Session) -> DeviceMonitoringService:
        return DeviceMonitoringService(db)

    @staticmethod
    def get_config_service(db: Session) -> DeviceConfigService:
        return DeviceConfigService(db)

    @staticmethod
    def get_health_service(db: Session) -> DeviceHealthService:
        return DeviceHealthService(db)

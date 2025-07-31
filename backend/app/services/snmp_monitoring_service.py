"""
Advanced SNMP Monitoring Service

Provides comprehensive SNMP-based monitoring for network devices including:
- Real-time metrics collection
- Interface monitoring
- System health checks
- Performance threshold monitoring
- Automated alerting
- Device discovery via SNMP
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pysnmp.hlapi.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    getCmd,
)
from pysnmp.proto.rfc1902 import Counter32, Counter64, Gauge32, Integer32
from sqlalchemy.orm import Session

from app.models.devices.device_management import (
    AlertSeverity,
    DeviceAlert,
    DeviceInterface,
    DeviceMonitoring,
    DeviceStatus,
    DeviceType,
    ManagedDevice,
    MonitoringProtocol,
)

logger = logging.getLogger(__name__)


class SNMPVersion(Enum):
    """SNMP Protocol Versions"""

    V1 = "v1"
    V2C = "v2c"
    V3 = "v3"


@dataclass
class SNMPCredentials:
    """SNMP Authentication Credentials"""

    community: str = "public"
    version: SNMPVersion = SNMPVersion.V2C
    username: Optional[str] = None
    auth_key: Optional[str] = None
    priv_key: Optional[str] = None
    auth_protocol: Optional[str] = None
    priv_protocol: Optional[str] = None


@dataclass
class SNMPMetric:
    """SNMP Metric Data Structure"""

    oid: str
    name: str
    value: Any
    timestamp: datetime
    device_id: int
    interface_id: Optional[int] = None


class StandardOIDs:
    """Standard SNMP OIDs for common metrics"""

    # System Information
    SYS_DESCR = "1.3.6.1.2.1.1.1.0"
    SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
    SYS_CONTACT = "1.3.6.1.2.1.1.4.0"
    SYS_NAME = "1.3.6.1.2.1.1.5.0"
    SYS_LOCATION = "1.3.6.1.2.1.1.6.0"

    # Interface Statistics
    IF_NUMBER = "1.3.6.1.2.1.2.1.0"
    IF_TABLE = "1.3.6.1.2.1.2.2.1"
    IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
    IF_TYPE = "1.3.6.1.2.1.2.2.1.3"
    IF_MTU = "1.3.6.1.2.1.2.2.1.4"
    IF_SPEED = "1.3.6.1.2.1.2.2.1.5"
    IF_ADMIN_STATUS = "1.3.6.1.2.1.2.2.1.7"
    IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"
    IF_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"
    IF_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16"
    IF_IN_ERRORS = "1.3.6.1.2.1.2.2.1.14"
    IF_OUT_ERRORS = "1.3.6.1.2.1.2.2.1.20"

    # CPU and Memory
    HOST_PROCESSOR_LOAD = "1.3.6.1.2.1.25.3.3.1.2"
    HOST_MEMORY_SIZE = "1.3.6.1.2.1.25.2.2.0"
    HOST_MEMORY_USED = "1.3.6.1.2.1.25.2.3.1.6"

    # SNMP Statistics
    SNMP_IN_PKTS = "1.3.6.1.2.1.11.1.0"
    SNMP_OUT_PKTS = "1.3.6.1.2.1.11.2.0"
    SNMP_IN_BAD_VERSIONS = "1.3.6.1.2.1.11.3.0"


class SNMPMonitoringService:
    """Advanced SNMP Monitoring Service"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def discover_device_info(
        self, ip_address: str, credentials: SNMPCredentials
    ) -> Dict[str, Any]:
        """Discover basic device information via SNMP"""
        try:
            device_info = {}

            # System information OIDs to query
            system_oids = {
                "description": StandardOIDs.SYS_DESCR,
                "uptime": StandardOIDs.SYS_UPTIME,
                "contact": StandardOIDs.SYS_CONTACT,
                "name": StandardOIDs.SYS_NAME,
                "location": StandardOIDs.SYS_LOCATION,
            }

            for info_name, oid in system_oids.items():
                value = await self._snmp_get(ip_address, oid, credentials)
                if value is not None:
                    device_info[info_name] = str(value)

            # Determine device type from system description
            device_info["device_type"] = self._determine_device_type(
                device_info.get("description", "")
            )

            # Get interface count
            interface_count = await self._snmp_get(
                ip_address, StandardOIDs.IF_NUMBER, credentials
            )
            if interface_count:
                device_info["interface_count"] = int(interface_count)

            return device_info

        except Exception as e:
            self.logger.error(f"Failed to discover device info for {ip_address}: {e}")
            return {}

    async def collect_system_metrics(self, device: ManagedDevice) -> List[SNMPMetric]:
        """Collect comprehensive system metrics from device"""
        credentials = self._get_device_credentials(device)
        metrics = []
        timestamp = datetime.utcnow()

        try:
            # System metrics
            system_metrics = {
                "uptime": StandardOIDs.SYS_UPTIME,
                "cpu_load": StandardOIDs.HOST_PROCESSOR_LOAD,
                "memory_total": StandardOIDs.HOST_MEMORY_SIZE,
                "memory_used": StandardOIDs.HOST_MEMORY_USED,
                "snmp_in_packets": StandardOIDs.SNMP_IN_PKTS,
                "snmp_out_packets": StandardOIDs.SNMP_OUT_PKTS,
            }

            for metric_name, oid in system_metrics.items():
                value = await self._snmp_get(device.ip_address, oid, credentials)
                if value is not None:
                    metrics.append(
                        SNMPMetric(
                            oid=oid,
                            name=metric_name,
                            value=self._convert_snmp_value(value),
                            timestamp=timestamp,
                            device_id=device.id,
                        )
                    )

            # Store metrics in database
            await self._store_metrics(metrics)

            return metrics

        except Exception as e:
            self.logger.error(
                f"Failed to collect system metrics for device {device.id}: {e}"
            )
            return []

    async def collect_interface_metrics(
        self, device: ManagedDevice
    ) -> List[SNMPMetric]:
        """Collect interface statistics from device"""
        credentials = self._get_device_credentials(device)
        metrics = []
        timestamp = datetime.utcnow()

        try:
            # Get interface count first
            interface_count = await self._snmp_get(
                device.ip_address, StandardOIDs.IF_NUMBER, credentials
            )
            if not interface_count:
                return metrics

            interface_count = int(interface_count)

            # Collect metrics for each interface
            for if_index in range(1, interface_count + 1):
                interface_metrics = await self._collect_single_interface_metrics(
                    device, if_index, credentials, timestamp
                )
                metrics.extend(interface_metrics)

            # Store metrics in database
            await self._store_metrics(metrics)

            return metrics

        except Exception as e:
            self.logger.error(
                f"Failed to collect interface metrics for device {device.id}: {e}"
            )
            return []

    async def _collect_single_interface_metrics(
        self,
        device: ManagedDevice,
        if_index: int,
        credentials: SNMPCredentials,
        timestamp: datetime,
    ) -> List[SNMPMetric]:
        """Collect metrics for a single interface"""
        metrics = []

        interface_oids = {
            "description": f"{StandardOIDs.IF_DESCR}.{if_index}",
            "admin_status": f"{StandardOIDs.IF_ADMIN_STATUS}.{if_index}",
            "oper_status": f"{StandardOIDs.IF_OPER_STATUS}.{if_index}",
            "speed": f"{StandardOIDs.IF_SPEED}.{if_index}",
            "in_octets": f"{StandardOIDs.IF_IN_OCTETS}.{if_index}",
            "out_octets": f"{StandardOIDs.IF_OUT_OCTETS}.{if_index}",
            "in_errors": f"{StandardOIDs.IF_IN_ERRORS}.{if_index}",
            "out_errors": f"{StandardOIDs.IF_OUT_ERRORS}.{if_index}",
        }

        # Get or create interface record
        interface = await self._get_or_create_interface(device, if_index)

        for metric_name, oid in interface_oids.items():
            value = await self._snmp_get(device.ip_address, oid, credentials)
            if value is not None:
                metrics.append(
                    SNMPMetric(
                        oid=oid,
                        name=f"interface_{metric_name}",
                        value=self._convert_snmp_value(value),
                        timestamp=timestamp,
                        device_id=device.id,
                        interface_id=interface.id if interface else None,
                    )
                )

        return metrics

    async def perform_health_check(self, device: ManagedDevice) -> Dict[str, Any]:
        """Perform comprehensive SNMP-based health check"""
        credentials = self._get_device_credentials(device)
        health_status = {
            "device_id": device.id,
            "timestamp": datetime.utcnow(),
            "overall_status": "unknown",
            "checks": {},
        }

        try:
            # SNMP connectivity check
            snmp_check = await self._check_snmp_connectivity(
                device.ip_address, credentials
            )
            health_status["checks"]["snmp_connectivity"] = snmp_check

            # System uptime check
            uptime_check = await self._check_system_uptime(
                device.ip_address, credentials
            )
            health_status["checks"]["system_uptime"] = uptime_check

            # Interface status check
            interface_check = await self._check_interface_status(
                device.ip_address, credentials
            )
            health_status["checks"]["interface_status"] = interface_check

            # Performance thresholds check
            performance_check = await self._check_performance_thresholds(device)
            health_status["checks"]["performance"] = performance_check

            # Determine overall status
            health_status["overall_status"] = self._calculate_overall_health(
                health_status["checks"]
            )

            # Generate alerts if needed
            await self._process_health_alerts(device, health_status)

            return health_status

        except Exception as e:
            self.logger.error(f"Health check failed for device {device.id}: {e}")
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
            return health_status

    async def discover_devices_in_subnet(
        self, subnet: str, credentials: SNMPCredentials
    ) -> List[Dict[str, Any]]:
        """Discover SNMP-enabled devices in a subnet"""
        discovered_devices = []

        try:
            # Parse subnet (simple implementation for /24 networks)
            if not subnet.endswith("/24"):
                raise ValueError("Currently only /24 subnets are supported")

            base_ip = subnet.split("/")[0].rsplit(".", 1)[0]

            # Scan IP range
            tasks = []
            for i in range(1, 255):
                ip = f"{base_ip}.{i}"
                tasks.append(self._probe_device(ip, credentials))

            # Execute probes concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                if isinstance(result, dict) and result:
                    ip = f"{base_ip}.{i + 1}"
                    result["ip_address"] = ip
                    discovered_devices.append(result)

            return discovered_devices

        except Exception as e:
            self.logger.error(f"Device discovery failed for subnet {subnet}: {e}")
            return []

    async def _probe_device(
        self, ip_address: str, credentials: SNMPCredentials
    ) -> Dict[str, Any]:
        """Probe a single IP address for SNMP response"""
        try:
            # Quick SNMP test - get system description
            value = await self._snmp_get(
                ip_address, StandardOIDs.SYS_DESCR, credentials, timeout=2
            )
            if value:
                return await self.discover_device_info(ip_address, credentials)
            return {}
        except Exception:
            return {}

    async def _snmp_get(
        self, ip_address: str, oid: str, credentials: SNMPCredentials, timeout: int = 5
    ) -> Optional[Any]:
        """Perform SNMP GET operation"""
        try:
            # Configure SNMP engine based on version
            if credentials.version == SNMPVersion.V2C:
                auth_data = CommunityData(credentials.community)
            elif credentials.version == SNMPVersion.V3:
                auth_data = UsmUserData(
                    credentials.username, credentials.auth_key, credentials.priv_key
                )
            else:
                auth_data = CommunityData(credentials.community, mpModel=0)

            transport = UdpTransportTarget((ip_address, 161), timeout=timeout)

            # Perform SNMP GET
            async for errorIndication, errorStatus, errorIndex, varBinds in getCmd(
                SnmpEngine(),
                auth_data,
                transport,
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            ):
                if errorIndication:
                    self.logger.warning(
                        f"SNMP error for {ip_address}: {errorIndication}"
                    )
                    return None

                if errorStatus:
                    self.logger.warning(
                        f"SNMP error for {ip_address}: {errorStatus.prettyPrint()}"
                    )
                    return None

                for varBind in varBinds:
                    return varBind[1]

            return None

        except Exception as e:
            self.logger.debug(f"SNMP GET failed for {ip_address} OID {oid}: {e}")
            return None

    def _get_device_credentials(self, device: ManagedDevice) -> SNMPCredentials:
        """Get SNMP credentials for device"""
        return SNMPCredentials(
            community=device.snmp_community or "public",
            version=SNMPVersion(device.snmp_version or "v2c"),
            username=device.snmp_username,
            auth_key=device.snmp_auth_key,
            priv_key=device.snmp_priv_key,
        )

    def _determine_device_type(self, sys_descr: str) -> DeviceType:
        """Determine device type from system description"""
        sys_descr_lower = sys_descr.lower()

        if any(vendor in sys_descr_lower for vendor in ["cisco", "catalyst"]):
            return (
                DeviceType.SWITCH if "switch" in sys_descr_lower else DeviceType.ROUTER
            )
        elif "mikrotik" in sys_descr_lower:
            return DeviceType.ROUTER
        elif any(
            term in sys_descr_lower for term in ["access point", "ap", "wireless"]
        ):
            return DeviceType.ACCESS_POINT
        elif "firewall" in sys_descr_lower:
            return DeviceType.FIREWALL
        else:
            return DeviceType.OTHER

    def _convert_snmp_value(self, value: Any) -> Any:
        """Convert SNMP value to appropriate Python type"""
        if isinstance(value, (Counter32, Counter64, Gauge32, Integer32)):
            return int(value)
        elif hasattr(value, "prettyPrint"):
            return value.prettyPrint()
        else:
            return str(value)

    async def _get_or_create_interface(
        self, device: ManagedDevice, if_index: int
    ) -> Optional[DeviceInterface]:
        """Get or create interface record"""
        try:
            interface = (
                self.db.query(DeviceInterface)
                .filter(
                    DeviceInterface.device_id == device.id,
                    DeviceInterface.interface_index == if_index,
                )
                .first()
            )

            if not interface:
                interface = DeviceInterface(
                    device_id=device.id,
                    interface_index=if_index,
                    name=f"Interface {if_index}",
                    status="unknown",
                )
                self.db.add(interface)
                self.db.commit()

            return interface

        except Exception as e:
            self.logger.error(f"Failed to get/create interface: {e}")
            return None

    async def _store_metrics(self, metrics: List[SNMPMetric]):
        """Store metrics in database"""
        try:
            for metric in metrics:
                monitoring_record = DeviceMonitoring(
                    device_id=metric.device_id,
                    interface_id=metric.interface_id,
                    metric_name=metric.name,
                    metric_value=str(metric.value),
                    timestamp=metric.timestamp,
                    protocol=MonitoringProtocol.SNMP,
                )
                self.db.add(monitoring_record)

            self.db.commit()

        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")
            self.db.rollback()

    async def _check_snmp_connectivity(
        self, ip_address: str, credentials: SNMPCredentials
    ) -> Dict[str, Any]:
        """Check SNMP connectivity"""
        try:
            value = await self._snmp_get(
                ip_address, StandardOIDs.SYS_UPTIME, credentials, timeout=3
            )
            return {
                "status": "ok" if value is not None else "failed",
                "response_time": 0.1,  # Placeholder
                "message": "SNMP responsive" if value else "SNMP timeout",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _check_system_uptime(
        self, ip_address: str, credentials: SNMPCredentials
    ) -> Dict[str, Any]:
        """Check system uptime"""
        try:
            uptime = await self._snmp_get(
                ip_address, StandardOIDs.SYS_UPTIME, credentials
            )
            if uptime:
                uptime_seconds = int(uptime) / 100  # Convert from centiseconds
                return {
                    "status": "ok",
                    "uptime_seconds": uptime_seconds,
                    "uptime_days": uptime_seconds / 86400,
                    "message": f"Uptime: {uptime_seconds / 86400:.1f} days",
                }
            else:
                return {"status": "failed", "message": "Could not retrieve uptime"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _check_interface_status(
        self, ip_address: str, credentials: SNMPCredentials
    ) -> Dict[str, Any]:
        """Check interface status"""
        try:
            interface_count = await self._snmp_get(
                ip_address, StandardOIDs.IF_NUMBER, credentials
            )
            if not interface_count:
                return {"status": "failed", "message": "Could not get interface count"}

            up_interfaces = 0
            total_interfaces = int(interface_count)

            # Check first few interfaces (limit for performance)
            check_limit = min(total_interfaces, 10)
            for i in range(1, check_limit + 1):
                oper_status = await self._snmp_get(
                    ip_address, f"{StandardOIDs.IF_OPER_STATUS}.{i}", credentials
                )
                if oper_status and int(oper_status) == 1:  # 1 = up
                    up_interfaces += 1

            return {
                "status": "ok",
                "total_interfaces": total_interfaces,
                "up_interfaces": up_interfaces,
                "checked_interfaces": check_limit,
                "message": f"{up_interfaces}/{check_limit} interfaces up",
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _check_performance_thresholds(
        self, device: ManagedDevice
    ) -> Dict[str, Any]:
        """Check performance against thresholds"""
        try:
            # Get recent metrics
            recent_time = datetime.utcnow() - timedelta(minutes=15)
            recent_metrics = (
                self.db.query(DeviceMonitoring)
                .filter(
                    DeviceMonitoring.device_id == device.id,
                    DeviceMonitoring.timestamp >= recent_time,
                )
                .all()
            )

            if not recent_metrics:
                return {"status": "warning", "message": "No recent metrics available"}

            # Analyze metrics (simplified)
            cpu_metrics = [m for m in recent_metrics if "cpu" in m.metric_name.lower()]
            [m for m in recent_metrics if "memory" in m.metric_name.lower()]

            alerts = []
            if cpu_metrics:
                avg_cpu = sum(float(m.metric_value) for m in cpu_metrics[-5:]) / len(
                    cpu_metrics[-5:]
                )
                if avg_cpu > 80:
                    alerts.append(f"High CPU usage: {avg_cpu:.1f}%")

            return {
                "status": "warning" if alerts else "ok",
                "alerts": alerts,
                "message": (
                    "; ".join(alerts) if alerts else "Performance within thresholds"
                ),
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_overall_health(self, checks: Dict[str, Dict[str, Any]]) -> str:
        """Calculate overall health status from individual checks"""
        if any(check.get("status") == "error" for check in checks.values()):
            return "critical"
        elif any(check.get("status") == "failed" for check in checks.values()):
            return "down"
        elif any(check.get("status") == "warning" for check in checks.values()):
            return "warning"
        else:
            return "up"

    async def _process_health_alerts(
        self, device: ManagedDevice, health_status: Dict[str, Any]
    ):
        """Process health check results and generate alerts"""
        try:
            overall_status = health_status["overall_status"]

            # Check if device status changed
            if device.status.value != overall_status:
                # Create alert for status change
                alert = DeviceAlert(
                    device_id=device.id,
                    alert_type="status_change",
                    severity=(
                        AlertSeverity.CRITICAL
                        if overall_status == "critical"
                        else AlertSeverity.WARNING
                    ),
                    message=f"Device status changed from {device.status.value} to {overall_status}",
                    details=health_status,
                    is_active=True,
                    created_at=datetime.utcnow(),
                )
                self.db.add(alert)

                # Update device status
                device.status = DeviceStatus(overall_status.upper())
                device.last_seen = datetime.utcnow()

                self.db.commit()

        except Exception as e:
            self.logger.error(f"Failed to process health alerts: {e}")
            self.db.rollback()


class SNMPMonitoringFactory:
    """Factory for creating SNMP monitoring service instances"""

    @staticmethod
    def create_monitoring_service(db: Session) -> SNMPMonitoringService:
        """Create SNMP monitoring service instance"""
        return SNMPMonitoringService(db)

    @staticmethod
    def get_standard_credentials(community: str = "public") -> SNMPCredentials:
        """Get standard SNMP v2c credentials"""
        return SNMPCredentials(community=community, version=SNMPVersion.V2C)

    @staticmethod
    def get_v3_credentials(
        username: str,
        auth_key: str,
        priv_key: str,
        auth_protocol: str = "SHA",
        priv_protocol: str = "AES",
    ) -> SNMPCredentials:
        """Get SNMP v3 credentials"""
        return SNMPCredentials(
            version=SNMPVersion.V3,
            username=username,
            auth_key=auth_key,
            priv_key=priv_key,
            auth_protocol=auth_protocol,
            priv_protocol=priv_protocol,
        )

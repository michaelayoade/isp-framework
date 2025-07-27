"""
Device Management API Endpoints

REST API endpoints for network device management including:
- Device registration and discovery
- Monitoring and health checks
- Configuration backup and restore
- Alert management
- Performance analytics
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.core.database import get_db
from app.models.devices.device_management import (
    ManagedDevice, DeviceInterface, DeviceMonitoring, DeviceAlert,
    DeviceConfigBackup, DeviceTemplate, DeviceType, DeviceStatus,
    AlertSeverity, BackupStatus
)
from app.services.device_management_service import DeviceManagementFactory
from app.services.snmp_monitoring_service import SNMPMonitoringFactory, SNMPCredentials
from app.api.v1.dependencies import get_current_admin

router = APIRouter()


# Device Management Endpoints

@router.get("/", response_model=List[Dict[str, Any]])
async def list_devices(
    device_type: Optional[DeviceType] = None,
    status: Optional[DeviceStatus] = None,
    vendor: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all network devices with optional filtering"""
    query = db.query(ManagedDevice)
    
    if device_type:
        query = query.filter(ManagedDevice.device_type == device_type)
    if status:
        query = query.filter(ManagedDevice.status == status)
    if vendor:
        query = query.filter(ManagedDevice.vendor.ilike(f"%{vendor}%"))
    
    devices = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": device.id,
            "hostname": device.hostname,
            "device_type": device.device_type.value,
            "vendor": device.vendor,
            "model": device.model,
            "management_ip": str(device.management_ip),
            "status": device.status.value,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "monitoring_enabled": device.monitoring_enabled,
            "created_at": device.created_at.isoformat()
        }
        for device in devices
    ]


@router.post("/", response_model=Dict[str, Any])
async def register_device(
    device_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Register a new network device"""
    discovery_service = DeviceManagementFactory.get_discovery_service(db)
    
    try:
        device = await discovery_service.register_device(device_data)
        return {
            "id": device.id,
            "hostname": device.hostname,
            "device_type": device.device_type.value,
            "management_ip": str(device.management_ip),
            "status": "registered"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{device_id}", response_model=Dict[str, Any])
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get detailed information about a specific device"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get recent monitoring data
    recent_metrics = db.query(DeviceMonitoring).filter(
        DeviceMonitoring.device_id == device_id
    ).order_by(desc(DeviceMonitoring.timestamp)).limit(10).all()
    
    # Get active alerts
    active_alerts = db.query(DeviceAlert).filter(
        and_(
            DeviceAlert.device_id == device_id,
            DeviceAlert.is_active == True
        )
    ).all()
    
    return {
        "id": device.id,
        "hostname": device.hostname,
        "device_type": device.device_type.value,
        "vendor": device.vendor,
        "model": device.model,
        "serial_number": device.serial_number,
        "management_ip": str(device.management_ip),
        "status": device.status.value,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "uptime": device.uptime,
        "os_version": device.os_version,
        "firmware_version": device.firmware_version,
        "monitoring_enabled": device.monitoring_enabled,
        "recent_metrics": [
            {
                "metric_name": metric.metric_name,
                "value": metric.metric_value,
                "timestamp": metric.timestamp.isoformat()
            }
            for metric in recent_metrics
        ],
        "active_alerts": [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity.value,
                "title": alert.title,
                "created_at": alert.created_at.isoformat()
            }
            for alert in active_alerts
        ]
    }


@router.post("/{device_id}/monitor")
async def collect_device_metrics(
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Trigger metric collection for a device"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    monitoring_service = DeviceManagementFactory.get_monitoring_service(db)
    
    # Run monitoring in background
    background_tasks.add_task(monitoring_service.collect_device_metrics, device_id)
    
    return {"message": "Monitoring collection started", "device_id": device_id}


@router.get("/{device_id}/health")
async def check_device_health(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Perform health check on a device"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    health_service = DeviceManagementFactory.get_health_service(db)
    health_status = await health_service.check_device_health(device_id)
    
    return health_status


# Configuration Management Endpoints

@router.post("/{device_id}/backup")
async def backup_device_config(
    device_id: int,
    background_tasks: BackgroundTasks,
    backup_type: str = "full",
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Backup device configuration"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    config_service = DeviceManagementFactory.get_config_service(db)
    
    # Run backup in background
    background_tasks.add_task(config_service.backup_device_config, device_id, backup_type)
    
    return {"message": "Configuration backup started", "device_id": device_id}


@router.get("/{device_id}/backups")
async def list_device_backups(
    device_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List configuration backups for a device"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    backups = db.query(DeviceConfigBackup).filter(
        DeviceConfigBackup.device_id == device_id
    ).order_by(desc(DeviceConfigBackup.created_at)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": backup.id,
            "backup_type": backup.backup_type,
            "backup_status": backup.backup_status.value,
            "file_size": backup.file_size,
            "created_at": backup.created_at.isoformat(),
            "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
            "error_message": backup.error_message
        }
        for backup in backups
    ]


# Monitoring and Analytics Endpoints

@router.get("/{device_id}/metrics/{metric_name}")
async def get_device_metric_history(
    device_id: int,
    metric_name: str,
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get historical data for a specific device metric"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    monitoring_service = DeviceManagementFactory.get_monitoring_service(db)
    metrics = await monitoring_service.get_device_performance_history(device_id, metric_name, hours)
    
    return {
        "device_id": device_id,
        "metric_name": metric_name,
        "hours": hours,
        "data_points": len(metrics),
        "metrics": [
            {
                "value": metric.metric_value,
                "timestamp": metric.timestamp.isoformat()
            }
            for metric in metrics
        ]
    }


@router.get("/{device_id}/interfaces")
async def list_device_interfaces(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List all interfaces for a device"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    interfaces = db.query(DeviceInterface).filter(
        DeviceInterface.device_id == device_id
    ).all()
    
    return [
        {
            "id": interface.id,
            "interface_name": interface.interface_name,
            "interface_type": interface.interface_type,
            "admin_status": interface.admin_status,
            "oper_status": interface.oper_status,
            "speed": interface.speed,
            "mtu": interface.mtu,
            "in_octets": interface.in_octets,
            "out_octets": interface.out_octets,
            "last_stats_update": interface.last_stats_update.isoformat() if interface.last_stats_update else None
        }
        for interface in interfaces
    ]


# Alert Management Endpoints

@router.get("/alerts")
async def list_alerts(
    device_id: Optional[int] = None,
    severity: Optional[AlertSeverity] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """List device alerts with optional filtering"""
    query = db.query(DeviceAlert)
    
    if device_id:
        query = query.filter(DeviceAlert.device_id == device_id)
    if severity:
        query = query.filter(DeviceAlert.severity == severity)
    if is_active is not None:
        query = query.filter(DeviceAlert.is_active == is_active)
    
    alerts = query.order_by(desc(DeviceAlert.created_at)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": alert.id,
            "device_id": alert.device_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "is_active": alert.is_active,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        }
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Acknowledge a device alert"""
    alert = db.query(DeviceAlert).filter(DeviceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_acknowledged = True
    alert.acknowledged_by = current_admin.username
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Alert acknowledged", "alert_id": alert_id}


# Discovery Endpoints

@router.post("/discovery/subnet")
async def discover_devices_in_subnet(
    subnet: str,
    background_tasks: BackgroundTasks,
    snmp_community: str = "public",
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Discover devices in a subnet using SNMP"""
    snmp_service = SNMPMonitoringFactory.create_monitoring_service(db)
    credentials = SNMPMonitoringFactory.get_standard_credentials(snmp_community)
    
    # Add background task for SNMP-based device discovery
    background_tasks.add_task(
        snmp_service.discover_devices_in_subnet, subnet, credentials
    )
    
    return {
        "message": f"SNMP device discovery initiated for subnet {subnet}",
        "subnet": subnet,
        "snmp_community": snmp_community
    }


# SNMP Monitoring Endpoints

@router.post("/{device_id}/snmp/collect-system-metrics")
async def collect_snmp_system_metrics(
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Collect comprehensive system metrics via SNMP"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    snmp_service = SNMPMonitoringFactory.create_monitoring_service(db)
    
    # Add background task for SNMP metrics collection
    background_tasks.add_task(
        snmp_service.collect_system_metrics, device
    )
    
    return {
        "message": "SNMP system metrics collection initiated",
        "device_id": device_id,
        "device_name": device.hostname
    }


@router.post("/{device_id}/snmp/collect-interface-metrics")
async def collect_snmp_interface_metrics(
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Collect interface statistics via SNMP"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    snmp_service = SNMPMonitoringFactory.create_monitoring_service(db)
    
    # Add background task for SNMP interface metrics collection
    background_tasks.add_task(
        snmp_service.collect_interface_metrics, device
    )
    
    return {
        "message": "SNMP interface metrics collection initiated",
        "device_id": device_id,
        "device_name": device.hostname
    }


@router.post("/{device_id}/snmp/health-check")
async def perform_snmp_health_check(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Perform comprehensive SNMP-based health check"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    snmp_service = SNMPMonitoringFactory.create_monitoring_service(db)
    
    try:
        health_status = await snmp_service.perform_health_check(device)
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"SNMP health check failed: {str(e)}"
        )


@router.get("/{device_id}/snmp/discover-info")
async def discover_device_snmp_info(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Discover device information via SNMP"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    snmp_service = SNMPMonitoringFactory.create_monitoring_service(db)
    credentials = SNMPMonitoringFactory.get_standard_credentials(
        device.snmp_community or "public"
    )
    
    try:
        device_info = await snmp_service.discover_device_info(
            device.ip_address, credentials
        )
        return {
            "device_id": device_id,
            "ip_address": device.ip_address,
            "discovered_info": device_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"SNMP device discovery failed: {str(e)}"
        )


@router.get("/{device_id}/snmp/metrics/recent")
async def get_recent_snmp_metrics(
    device_id: int,
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    metric_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get recent SNMP metrics for a device"""
    device = db.query(ManagedDevice).filter(ManagedDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get metrics from the specified time range
    from datetime import datetime, timedelta
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(DeviceMonitoring).filter(
        DeviceMonitoring.device_id == device_id,
        DeviceMonitoring.timestamp >= start_time,
        DeviceMonitoring.protocol == MonitoringProtocol.SNMP
    )
    
    if metric_name:
        query = query.filter(DeviceMonitoring.metric_name.ilike(f"%{metric_name}%"))
    
    metrics = query.order_by(DeviceMonitoring.timestamp.desc()).limit(1000).all()
    
    return {
        "device_id": device_id,
        "device_name": device.hostname,
        "time_range_hours": hours,
        "metric_filter": metric_name,
        "total_metrics": len(metrics),
        "metrics": [
            {
                "id": metric.id,
                "metric_name": metric.metric_name,
                "metric_value": metric.metric_value,
                "timestamp": metric.timestamp.isoformat(),
                "interface_id": metric.interface_id
            }
            for metric in metrics
        ]
    }


@router.get("/snmp/monitoring/dashboard")
async def get_snmp_monitoring_dashboard(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get SNMP monitoring dashboard summary"""
    from datetime import datetime, timedelta
    
    # Get devices with SNMP monitoring enabled
    snmp_devices = db.query(ManagedDevice).filter(
        ManagedDevice.snmp_community.isnot(None)
    ).all()
    
    # Get recent SNMP metrics (last 24 hours)
    recent_time = datetime.utcnow() - timedelta(hours=24)
    recent_metrics = db.query(DeviceMonitoring).filter(
        DeviceMonitoring.timestamp >= recent_time,
        DeviceMonitoring.protocol == MonitoringProtocol.SNMP
    ).count()
    
    # Get SNMP-related alerts
    snmp_alerts = db.query(DeviceAlert).filter(
        DeviceAlert.is_active == True,
        DeviceAlert.alert_type.in_(['snmp_timeout', 'snmp_error', 'performance_threshold'])
    ).count()
    
    # Device status breakdown for SNMP-enabled devices
    device_status_counts = {}
    for device in snmp_devices:
        status = device.status.value
        device_status_counts[status] = device_status_counts.get(status, 0) + 1
    
    return {
        "total_snmp_devices": len(snmp_devices),
        "recent_metrics_24h": recent_metrics,
        "active_snmp_alerts": snmp_alerts,
        "device_status_breakdown": device_status_counts,
        "monitoring_protocols": {
            "snmp_v1": len([d for d in snmp_devices if d.snmp_version == 'v1']),
            "snmp_v2c": len([d for d in snmp_devices if d.snmp_version == 'v2c']),
            "snmp_v3": len([d for d in snmp_devices if d.snmp_version == 'v3'])
        }
    }


# Statistics and Dashboard Endpoints

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get device management dashboard summary"""
    total_devices = db.query(ManagedDevice).count()
    online_devices = db.query(ManagedDevice).filter(ManagedDevice.status == DeviceStatus.UP).count()
    offline_devices = db.query(ManagedDevice).filter(ManagedDevice.status == DeviceStatus.DOWN).count()
    active_alerts = db.query(DeviceAlert).filter(DeviceAlert.is_active == True).count()
    critical_alerts = db.query(DeviceAlert).filter(
        and_(DeviceAlert.is_active == True, DeviceAlert.severity == AlertSeverity.CRITICAL)
    ).count()
    
    # Device type breakdown
    device_types = db.query(ManagedDevice.device_type, func.count(ManagedDevice.id)).group_by(ManagedDevice.device_type).all()
    
    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "unreachable_devices": total_devices - online_devices - offline_devices,
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "device_types": {device_type.value: count for device_type, count in device_types}
    }

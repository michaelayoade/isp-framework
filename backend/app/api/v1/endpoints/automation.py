"""FastAPI endpoints for Ansible automation and device management."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_admin
from app.core.database import get_db
from app.core.permissions import require_permission
from app.models.auth.base import Administrator
from app.models.automation.infrastructure import (
    AutomationDevice,
    ProvisioningTask,
    Site,
)
from app.services.automation import AnsibleRunnerService, AutomationService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["automation"])


# Dynamic Inventory Endpoint
@router.get("/inventory", response_model=Dict[str, Any])
@require_permission("automation.view")
async def get_ansible_inventory(
    site_id: Optional[int] = Query(None, description="Filter by site ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Get dynamic Ansible inventory in JSON format."""
    try:
        service = AutomationService(db)
        inventory = service.inventory_service.generate_inventory(site_id, device_type)
        return inventory

    except Exception as e:
        logger.error(f"Error generating inventory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate inventory",
        )


# Dashboard and Statistics
@router.get("/dashboard", response_model=Dict[str, Any])
@require_permission("automation.view")
async def get_automation_dashboard(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Get automation dashboard with statistics and recent activity."""
    try:
        service = AutomationService(db)
        dashboard = service.get_automation_dashboard()
        return dashboard

    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data",
        )


# Site Management
@router.get("/sites", response_model=List[Dict[str, Any]])
@require_permission("automation.sites.view")
async def list_sites(
    active_only: bool = Query(True, description="Show only active sites"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """List all automation sites."""
    try:
        query = db.query(Site)
        if active_only:
            query = query.filter(Site.is_active is True)

        sites = query.all()

        return [
            {
                "id": site.id,
                "name": site.name,
                "code": site.code,
                "site_type": site.site_type,
                "address": site.address,
                "device_count": len(site.devices),
                "is_active": site.is_active,
            }
            for site in sites
        ]

    except Exception as e:
        logger.error(f"Error listing sites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sites",
        )


@router.post(
    "/sites",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Site created successfully"},
        400: {"description": "Invalid site data or validation error"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Site with this code already exists"},
    },
)
@require_permission("automation.sites.create")
async def create_site(
    site_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Create a new automation site."""
    try:
        site = Site(
            name=site_data["name"],
            code=site_data["code"],
            description=site_data.get("description"),
            address=site_data.get("address"),
            city=site_data.get("city"),
            state=site_data.get("state"),
            country=site_data.get("country"),
            site_type=site_data["site_type"],
            latitude=site_data.get("latitude"),
            longitude=site_data.get("longitude"),
        )

        db.add(site)
        db.commit()
        db.refresh(site)

        logger.info(f"Admin {current_admin.username} created site {site.name}")
        return {"id": site.id, "message": "Site created successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating site: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create site",
        )


# Device Management
@router.get("/devices", response_model=List[Dict[str, Any]])
@require_permission("automation.devices.view")
async def list_devices(
    site_id: Optional[int] = Query(None, description="Filter by site ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    status: Optional[str] = Query(None, description="Filter by status"),
    managed_only: bool = Query(True, description="Show only managed devices"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """List automation devices with filtering."""
    try:
        query = db.query(AutomationDevice)

        if site_id:
            query = query.filter(AutomationDevice.site_id == site_id)
        if device_type:
            query = query.filter(AutomationDevice.device_type == device_type)
        if vendor:
            query = query.filter(AutomationDevice.vendor == vendor)
        if status:
            query = query.filter(AutomationDevice.status == status)
        if managed_only:
            query = query.filter(AutomationDevice.is_managed is True)

        devices = query.all()

        return [
            {
                "id": device.id,
                "hostname": device.hostname,
                "device_type": device.device_type,
                "vendor": device.vendor,
                "model": device.model,
                "management_ip": device.management_ip,
                "site_id": device.site_id,
                "site_name": device.site.name if device.site else None,
                "status": device.status,
                "is_managed": device.is_managed,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "is_online": device.is_online,
            }
            for device in devices
        ]

    except Exception as e:
        logger.error(f"Error listing devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices",
        )


@router.post("/devices", status_code=status.HTTP_201_CREATED)
@require_permission("automation.devices.create")
async def create_device(
    device_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Create a new automation device."""
    try:
        device = AutomationDevice(
            hostname=device_data["hostname"],
            device_type=device_data["device_type"],
            vendor=device_data["vendor"],
            model=device_data.get("model"),
            serial_number=device_data.get("serial_number"),
            management_ip=device_data["management_ip"],
            management_port=device_data.get("management_port", 22),
            site_id=device_data["site_id"],
            ansible_variables=device_data.get("ansible_variables", {}),
        )

        db.add(device)
        db.commit()
        db.refresh(device)

        logger.info(f"Admin {current_admin.username} created device {device.hostname}")
        return {"id": device.id, "message": "Device created successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device",
        )


# Provisioning Tasks
@router.get("/tasks", response_model=List[Dict[str, Any]])
@require_permission("automation.tasks.view")
async def list_provisioning_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    limit: int = Query(50, le=100, description="Limit number of results"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """List provisioning tasks with filtering."""
    try:
        query = db.query(ProvisioningTask)

        if status:
            query = query.filter(ProvisioningTask.status == status)
        if task_type:
            query = query.filter(ProvisioningTask.task_type == task_type)
        if device_id:
            query = query.filter(ProvisioningTask.device_id == device_id)

        tasks = query.order_by(ProvisioningTask.created_at.desc()).limit(limit).all()

        return [
            {
                "id": task.id,
                "task_name": task.task_name,
                "task_type": task.task_type,
                "status": task.status,
                "playbook_name": task.playbook_name,
                "device_id": task.device_id,
                "site_id": task.site_id,
                "customer_id": task.customer_id,
                "priority": task.priority,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
                "exit_code": task.exit_code,
                "duration_seconds": task.duration_seconds,
            }
            for task in tasks
        ]

    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks",
        )


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
@require_permission("automation.tasks.create")
async def create_provisioning_task(
    task_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Create a new provisioning task."""
    try:
        runner_service = AnsibleRunnerService(db)

        task = runner_service.create_provisioning_task(
            task_name=task_data["task_name"],
            playbook_name=task_data["playbook_name"],
            task_type=task_data.get("task_type", "provision"),
            device_id=task_data.get("device_id"),
            site_id=task_data.get("site_id"),
            customer_id=task_data.get("customer_id"),
            service_id=task_data.get("service_id"),
            variables=task_data.get("variables", {}),
            tags=task_data.get("tags", []),
            priority=task_data.get("priority", "medium"),
            executed_by=current_admin.id,
        )

        # Schedule task execution in background
        if task_data.get("execute_immediately", False):
            background_tasks.add_task(runner_service.execute_playbook, task.id)

        logger.info(f"Admin {current_admin.username} created task {task.id}")
        return {"id": task.id, "message": "Task created successfully"}

    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


@router.post("/tasks/{task_id}/execute")
@require_permission("automation.tasks.execute")
async def execute_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Execute a provisioning task."""
    try:
        task = db.query(ProvisioningTask).filter(ProvisioningTask.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        if task.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task cannot be executed in status: {task.status}",
            )

        runner_service = AnsibleRunnerService(db)
        background_tasks.add_task(runner_service.execute_playbook, task_id)

        logger.info(f"Admin {current_admin.username} executed task {task_id}")
        return {"message": "Task execution started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute task",
        )


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
@require_permission("automation.tasks.view")
async def get_task_details(
    task_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Get detailed information about a provisioning task."""
    try:
        task = db.query(ProvisioningTask).filter(ProvisioningTask.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        return {
            "id": task.id,
            "task_name": task.task_name,
            "description": task.description,
            "task_type": task.task_type,
            "category": task.category,
            "status": task.status,
            "priority": task.priority,
            "playbook_name": task.playbook_name,
            "playbook_tags": task.playbook_tags,
            "ansible_variables": task.ansible_variables,
            "device_id": task.device_id,
            "site_id": task.site_id,
            "customer_id": task.customer_id,
            "service_id": task.service_id,
            "exit_code": task.exit_code,
            "stdout_log": task.stdout_log,
            "stderr_log": task.stderr_log,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "duration_seconds": task.duration_seconds,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task details",
        )


@router.post("/tasks/{task_id}/cancel")
@require_permission("automation.tasks.cancel")
async def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Cancel a provisioning task."""
    try:
        runner_service = AnsibleRunnerService(db)
        success = runner_service.cancel_task(task_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task cannot be cancelled",
            )

        logger.info(f"Admin {current_admin.username} cancelled task {task_id}")
        return {"message": "Task cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel task",
        )


# Service Provisioning Shortcuts
@router.post("/provision/customer-service/{service_id}")
@require_permission("automation.provision")
async def provision_customer_service(
    service_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Provision network configuration for a customer service."""
    try:
        service = AutomationService(db)
        success = service.device_service.provision_customer_service(service_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create provisioning task",
            )

        logger.info(
            f"Admin {current_admin.username} initiated service provisioning for service {service_id}"
        )
        return {"message": "Service provisioning initiated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error provisioning service {service_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision service",
        )


@router.post("/backup/device/{device_id}")
@require_permission("automation.backup")
async def backup_device_config(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_active_admin),
):
    """Create a configuration backup task for a device."""
    try:
        service = AutomationService(db)
        success = service.device_service.backup_device_config(device_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create backup task",
            )

        logger.info(
            f"Admin {current_admin.username} initiated config backup for device {device_id}"
        )
        return {"message": "Configuration backup initiated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error backing up device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to backup device configuration",
        )

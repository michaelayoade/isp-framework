"""Ansible automation service for device provisioning and configuration management."""
import asyncio
import json
import subprocess
import tempfile
import os
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
import logging

from app.models.automation.infrastructure import (
    Site, AutomationDevice, DeviceCredential, ProvisioningTask, AnsiblePlaybook
)
from app.models.customer.base import Customer
from app.models.services.instances import CustomerService

logger = logging.getLogger(__name__)


class AnsibleInventoryService:
    """Service for generating dynamic Ansible inventory."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_inventory(self, site_id: Optional[int] = None, device_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate dynamic Ansible inventory in JSON format."""
        try:
            inventory = {
                "_meta": {
                    "hostvars": {}
                },
                "all": {
                    "children": ["sites", "device_types", "vendors"]
                },
                "sites": {
                    "children": []
                },
                "device_types": {
                    "children": []
                },
                "vendors": {
                    "children": []
                }
            }
            
            # Build query with filters
            query = self.db.query(AutomationDevice).options(
                joinedload(AutomationDevice.site),
                joinedload(AutomationDevice.credentials)
            ).filter(AutomationDevice.is_managed == True)
            
            if site_id:
                query = query.filter(AutomationDevice.site_id == site_id)
            if device_type:
                query = query.filter(AutomationDevice.device_type == device_type)
            
            devices = query.all()
            
            # Group devices by site, type, and vendor
            site_groups = {}
            type_groups = {}
            vendor_groups = {}
            
            for device in devices:
                # Site grouping
                site_name = f"site_{device.site.code}" if device.site else "site_unknown"
                if site_name not in site_groups:
                    site_groups[site_name] = []
                    inventory["sites"]["children"].append(site_name)
                    inventory[site_name] = {"hosts": []}
                site_groups[site_name].append(device.hostname)
                inventory[site_name]["hosts"].append(device.hostname)
                
                # Device type grouping
                type_name = f"type_{device.device_type}"
                if type_name not in type_groups:
                    type_groups[type_name] = []
                    inventory["device_types"]["children"].append(type_name)
                    inventory[type_name] = {"hosts": []}
                type_groups[type_name].append(device.hostname)
                inventory[type_name]["hosts"].append(device.hostname)
                
                # Vendor grouping
                vendor_name = f"vendor_{device.vendor}"
                if vendor_name not in vendor_groups:
                    vendor_groups[vendor_name] = []
                    inventory["vendors"]["children"].append(vendor_name)
                    inventory[vendor_name] = {"hosts": []}
                vendor_groups[vendor_name].append(device.hostname)
                inventory[vendor_name]["hosts"].append(device.hostname)
                
                # Host variables
                host_vars = {
                    "ansible_host": device.management_ip,
                    "ansible_port": device.management_port,
                    "device_type": device.device_type,
                    "vendor": device.vendor,
                    "model": device.model,
                    "site_id": device.site_id,
                    "site_name": device.site.name if device.site else None,
                    "serial_number": device.serial_number,
                    "os_version": device.os_version,
                    "firmware_version": device.firmware_version
                }
                
                # Add device-specific Ansible variables
                if device.ansible_variables:
                    host_vars.update(device.ansible_variables)
                
                # Add credentials (for SSH/API access)
                ssh_cred = next((c for c in device.credentials if c.credential_type == "ssh" and c.is_active), None)
                if ssh_cred:
                    host_vars["ansible_user"] = ssh_cred.username
                    # Note: Passwords should be handled via Ansible Vault or external credential management
                
                inventory["_meta"]["hostvars"][device.hostname] = host_vars
            
            return inventory
            
        except Exception as e:
            logger.error(f"Error generating Ansible inventory: {str(e)}")
            raise


class AnsibleRunnerService:
    """Service for executing Ansible playbooks and managing tasks."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ansible_base_path = "/opt/isp-framework/ansible"
        self.playbooks_path = f"{self.ansible_base_path}/playbooks"
        self.inventory_path = f"{self.ansible_base_path}/inventory"
    
    async def execute_playbook(self, task_id: int) -> bool:
        """Execute an Ansible playbook for a provisioning task."""
        try:
            task = self.db.query(ProvisioningTask).filter(ProvisioningTask.id == task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            # Update task status
            task.status = "running"
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            # Generate dynamic inventory
            inventory_service = AnsibleInventoryService(self.db)
            inventory = inventory_service.generate_inventory()
            
            # Create temporary inventory file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as inv_file:
                json.dump(inventory, inv_file, indent=2)
                inventory_file = inv_file.name
            
            try:
                # Build ansible-playbook command
                playbook_path = f"{self.playbooks_path}/{task.playbook_name}"
                cmd = [
                    "ansible-playbook",
                    "-i", inventory_file,
                    playbook_path,
                    "--extra-vars", json.dumps(task.ansible_variables),
                ]
                
                # Add tags if specified
                if task.playbook_tags:
                    cmd.extend(["--tags", ",".join(task.playbook_tags)])
                
                # Add limit if targeting specific device/site
                if task.device_id:
                    device = self.db.query(AutomationDevice).filter(AutomationDevice.id == task.device_id).first()
                    if device:
                        cmd.extend(["--limit", device.hostname])
                elif task.site_id:
                    site = self.db.query(Site).filter(Site.id == task.site_id).first()
                    if site:
                        cmd.extend(["--limit", f"site_{site.code}"])
                
                # Execute playbook
                logger.info(f"Executing Ansible command: {' '.join(cmd)}")
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.ansible_base_path
                )
                
                stdout, stderr = await process.communicate()
                
                # Update task with results
                task.exit_code = process.returncode
                task.stdout_log = stdout.decode('utf-8') if stdout else ""
                task.stderr_log = stderr.decode('utf-8') if stderr else ""
                task.completed_at = datetime.utcnow()
                
                if process.returncode == 0:
                    task.status = "completed"
                    logger.info(f"Task {task_id} completed successfully")
                else:
                    task.status = "failed"
                    logger.error(f"Task {task_id} failed with exit code {process.returncode}")
                
                self.db.commit()
                return process.returncode == 0
                
            finally:
                # Clean up temporary inventory file
                if os.path.exists(inventory_file):
                    os.unlink(inventory_file)
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")
            # Update task status to failed
            if task:
                task.status = "failed"
                task.stderr_log = str(e)
                task.completed_at = datetime.utcnow()
                self.db.commit()
            return False
    
    def create_provisioning_task(
        self,
        task_name: str,
        playbook_name: str,
        task_type: str = "provision",
        device_id: Optional[int] = None,
        site_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        service_id: Optional[int] = None,
        variables: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: str = "medium",
        scheduled_at: Optional[datetime] = None,
        executed_by: Optional[int] = None
    ) -> ProvisioningTask:
        """Create a new provisioning task."""
        try:
            task = ProvisioningTask(
                task_name=task_name,
                task_type=task_type,
                playbook_name=playbook_name,
                device_id=device_id,
                site_id=site_id,
                customer_id=customer_id,
                service_id=service_id,
                ansible_variables=variables or {},
                playbook_tags=tags or [],
                priority=priority,
                scheduled_at=scheduled_at,
                executed_by=executed_by
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Created provisioning task {task.id}: {task_name}")
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating provisioning task: {str(e)}")
            raise
    
    def get_task_status(self, task_id: int) -> Optional[ProvisioningTask]:
        """Get the status of a provisioning task."""
        return self.db.query(ProvisioningTask).filter(ProvisioningTask.id == task_id).first()
    
    def cancel_task(self, task_id: int) -> bool:
        """Cancel a pending or running task."""
        try:
            task = self.db.query(ProvisioningTask).filter(ProvisioningTask.id == task_id).first()
            if not task:
                return False
            
            if task.status in ["pending", "running"]:
                task.status = "cancelled"
                task.completed_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Cancelled task {task_id}")
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False


class DeviceManagementService:
    """Service for managing network devices and their configurations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def discover_devices(self, site_id: int, ip_range: str) -> List[AutomationDevice]:
        """Discover devices in a network range (placeholder for network scanning)."""
        # This would integrate with network discovery tools like nmap, SNMP walks, etc.
        # For now, return empty list as this requires external tools
        logger.info(f"Device discovery requested for site {site_id}, range {ip_range}")
        return []
    
    def backup_device_config(self, device_id: int) -> bool:
        """Create a configuration backup task for a device."""
        try:
            device = self.db.query(AutomationDevice).filter(AutomationDevice.id == device_id).first()
            if not device:
                return False
            
            # Create backup task
            runner = AnsibleRunnerService(self.db)
            task = runner.create_provisioning_task(
                task_name=f"Backup configuration for {device.hostname}",
                playbook_name="backup_config.yml",
                task_type="backup",
                device_id=device_id,
                variables={"backup_type": "config", "device_type": device.device_type}
            )
            
            return task is not None
            
        except Exception as e:
            logger.error(f"Error creating backup task for device {device_id}: {str(e)}")
            return False
    
    def provision_customer_service(self, service_id: int) -> bool:
        """Provision network configuration for a customer service."""
        try:
            service = self.db.query(CustomerService).options(
                joinedload(CustomerService.customer)
            ).filter(CustomerService.id == service_id).first()
            
            if not service:
                return False
            
            # Determine provisioning playbook based on service type
            playbook_map = {
                "internet": "provision_internet_service.yml",
                "voice": "provision_voice_service.yml",
                "tv": "provision_tv_service.yml"
            }
            
            service_template = service.service_template
            playbook_name = playbook_map.get(service_template.category, "provision_generic_service.yml")
            
            # Create provisioning task
            runner = AnsibleRunnerService(self.db)
            task = runner.create_provisioning_task(
                task_name=f"Provision service for customer {service.customer.username}",
                playbook_name=playbook_name,
                task_type="provision",
                customer_id=service.customer_id,
                service_id=service_id,
                variables={
                    "customer_username": service.customer.username,
                    "service_id": service_id,
                    "service_type": service_template.category,
                    "bandwidth_down": getattr(service.internet_config, 'download_speed_kbps', None),
                    "bandwidth_up": getattr(service.internet_config, 'upload_speed_kbps', None),
                }
            )
            
            return task is not None
            
        except Exception as e:
            logger.error(f"Error creating provisioning task for service {service_id}: {str(e)}")
            return False
    
    def update_device_monitoring(self, device_id: int) -> Dict[str, Any]:
        """Update device monitoring information."""
        try:
            device = self.db.query(AutomationDevice).filter(AutomationDevice.id == device_id).first()
            if not device:
                return {"error": "Device not found"}
            
            # Create monitoring task
            runner = AnsibleRunnerService(self.db)
            task = runner.create_provisioning_task(
                task_name=f"Update monitoring for {device.hostname}",
                playbook_name="update_monitoring.yml",
                task_type="monitor",
                device_id=device_id,
                variables={"device_type": device.device_type, "vendor": device.vendor}
            )
            
            return {"task_id": task.id, "status": "scheduled"}
            
        except Exception as e:
            logger.error(f"Error creating monitoring task for device {device_id}: {str(e)}")
            return {"error": str(e)}


class AutomationService:
    """Main automation service combining all automation functionality."""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = AnsibleInventoryService(db)
        self.runner_service = AnsibleRunnerService(db)
        self.device_service = DeviceManagementService(db)
    
    def get_automation_dashboard(self) -> Dict[str, Any]:
        """Get automation dashboard statistics."""
        try:
            # Device statistics
            total_devices = self.db.query(AutomationDevice).count()
            active_devices = self.db.query(AutomationDevice).filter(AutomationDevice.status == "active").count()
            managed_devices = self.db.query(AutomationDevice).filter(AutomationDevice.is_managed == True).count()
            
            # Site statistics
            total_sites = self.db.query(Site).count()
            active_sites = self.db.query(Site).filter(Site.is_active == True).count()
            
            # Task statistics
            total_tasks = self.db.query(ProvisioningTask).count()
            pending_tasks = self.db.query(ProvisioningTask).filter(ProvisioningTask.status == "pending").count()
            running_tasks = self.db.query(ProvisioningTask).filter(ProvisioningTask.status == "running").count()
            failed_tasks = self.db.query(ProvisioningTask).filter(ProvisioningTask.status == "failed").count()
            
            # Recent tasks
            recent_tasks = self.db.query(ProvisioningTask).order_by(
                desc(ProvisioningTask.created_at)
            ).limit(10).all()
            
            return {
                "devices": {
                    "total": total_devices,
                    "active": active_devices,
                    "managed": managed_devices,
                    "offline": total_devices - active_devices
                },
                "sites": {
                    "total": total_sites,
                    "active": active_sites
                },
                "tasks": {
                    "total": total_tasks,
                    "pending": pending_tasks,
                    "running": running_tasks,
                    "failed": failed_tasks
                },
                "recent_tasks": [
                    {
                        "id": task.id,
                        "name": task.task_name,
                        "status": task.status,
                        "type": task.task_type,
                        "created_at": task.created_at.isoformat() if task.created_at else None
                    }
                    for task in recent_tasks
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting automation dashboard: {str(e)}")
            return {"error": str(e)}

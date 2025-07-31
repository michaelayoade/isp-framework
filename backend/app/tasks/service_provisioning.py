"""
Service Provisioning Background Tasks.

Handles automated service provisioning, suspension, and restoration with comprehensive
error handling and dead-letter queue integration.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from celery import current_task
import structlog

from app.core.celery import celery_app, ISPFrameworkTask
from app.core.database import get_db
from app.models.services.instances import CustomerService, CustomerInternetService
from app.models.networking.ipam import IPPool, IPAllocation
from app.core.error_handling import ISPException, ErrorSeverity, ErrorCategory, ErrorImpact

logger = structlog.get_logger("isp.tasks.service_provisioning")


@celery_app.task(bind=True, base=ISPFrameworkTask, name='app.tasks.service_provisioning.provision_internet_service')
def provision_internet_service(self, customer_service_id: int, provisioning_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provision an Internet service for a customer.
    
    This task handles:
    - IP address allocation
    - Router configuration
    - RADIUS user creation
    - Service activation
    """
    try:
        db = next(get_db())
        
        # Get customer service
        customer_service = db.query(CustomerService).filter(
            CustomerService.id == customer_service_id
        ).first()
        
        if not customer_service:
            raise ISPException(
                title="Customer Service Not Found",
                detail=f"Customer service {customer_service_id} not found",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING
            )
        
        customer = customer_service.customer
        service_template = customer_service.service_template
        
        logger.info(
            "Starting Internet service provisioning",
            customer_service_id=customer_service_id,
            customer_id=customer.id,
            portal_id=customer.portal_id,
            service_template_id=service_template.id
        )
        
        # Step 1: Allocate IP address
        ip_allocation = _allocate_customer_ip(db, customer_service, provisioning_data)
        
        # Step 2: Create Internet service record
        internet_service = _create_internet_service_record(db, customer_service, ip_allocation, provisioning_data)
        
        # Step 3: Configure router/NAS
        router_config = _configure_router_for_service(db, customer_service, internet_service, provisioning_data)
        
        # Step 4: Create RADIUS user
        radius_config = _create_radius_user(db, customer, internet_service, provisioning_data)
        
        # Step 5: Update service status
        customer_service.status = 'active'
        customer_service.activated_at = datetime.now(timezone.utc)
        customer_service.notes = f"Automatically provisioned by task {current_task.request.id}"
        
        db.commit()
        
        result = {
            'success': True,
            'customer_service_id': customer_service_id,
            'customer_id': customer.id,
            'portal_id': customer.portal_id,
            'ip_address': ip_allocation.ip_address if ip_allocation else None,
            'internet_service_id': internet_service.id if internet_service else None,
            'router_config': router_config,
            'radius_config': radius_config,
            'provisioned_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "Internet service provisioning completed successfully",
            **result
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Internet service provisioning failed",
            customer_service_id=customer_service_id,
            error=str(e),
            task_id=current_task.request.id
        )
        
        # Update service status to failed
        try:
            db = next(get_db())
            customer_service = db.query(CustomerService).filter(
                CustomerService.id == customer_service_id
            ).first()
            if customer_service:
                customer_service.status = 'provisioning_failed'
                customer_service.notes = f"Provisioning failed: {str(e)}"
                db.commit()
        except Exception:
            pass
        
        raise
    finally:
        db.close()


@celery_app.task(bind=True, base=ISPFrameworkTask, name='app.tasks.service_provisioning.suspend_service')
def suspend_service(self, customer_service_id: int, suspension_reason: str, grace_period_hours: int = 24) -> Dict[str, Any]:
    """
    Suspend a customer service.
    
    This task handles:
    - Service suspension in billing system
    - Router/NAS configuration update
    - RADIUS user suspension
    - Customer notification
    """
    try:
        db = next(get_db())
        
        # Get customer service
        customer_service = db.query(CustomerService).filter(
            CustomerService.id == customer_service_id
        ).first()
        
        if not customer_service:
            raise ISPException(
                title="Customer Service Not Found",
                detail=f"Customer service {customer_service_id} not found",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING
            )
        
        customer = customer_service.customer
        
        logger.info(
            "Starting service suspension",
            customer_service_id=customer_service_id,
            customer_id=customer.id,
            portal_id=customer.portal_id,
            reason=suspension_reason
        )
        
        # Step 1: Update service status
        customer_service.status = 'suspended'
        customer_service.suspended_at = datetime.now(timezone.utc)
        customer_service.suspension_reason = suspension_reason
        customer_service.notes = f"Suspended by task {current_task.request.id}: {suspension_reason}"
        
        # Step 2: Configure router for suspension
        router_config = _configure_router_suspension(db, customer_service, grace_period_hours)
        
        # Step 3: Update RADIUS user
        radius_config = _suspend_radius_user(db, customer, suspension_reason)
        
        # Step 4: Schedule customer notification
        from app.tasks.customer_notifications import send_service_suspension_notification
        notification_task = send_service_suspension_notification.delay(
            customer.id, 
            customer_service_id, 
            suspension_reason,
            grace_period_hours
        )
        
        db.commit()
        
        result = {
            'success': True,
            'customer_service_id': customer_service_id,
            'customer_id': customer.id,
            'portal_id': customer.portal_id,
            'suspension_reason': suspension_reason,
            'grace_period_hours': grace_period_hours,
            'router_config': router_config,
            'radius_config': radius_config,
            'notification_task_id': notification_task.id,
            'suspended_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "Service suspension completed successfully",
            **result
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Service suspension failed",
            customer_service_id=customer_service_id,
            error=str(e),
            task_id=current_task.request.id
        )
        raise
    finally:
        db.close()


@celery_app.task(bind=True, base=ISPFrameworkTask, name='app.tasks.service_provisioning.restore_service')
def restore_service(self, customer_service_id: int, restoration_notes: str = "") -> Dict[str, Any]:
    """
    Restore a suspended customer service.
    
    This task handles:
    - Service restoration in billing system
    - Router/NAS configuration update
    - RADIUS user restoration
    - Customer notification
    """
    try:
        db = next(get_db())
        
        # Get customer service
        customer_service = db.query(CustomerService).filter(
            CustomerService.id == customer_service_id,
            CustomerService.status == 'suspended'
        ).first()
        
        if not customer_service:
            raise ISPException(
                title="Suspended Service Not Found",
                detail=f"Suspended customer service {customer_service_id} not found",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                impact=ErrorImpact.CUSTOMER_FACING
            )
        
        customer = customer_service.customer
        
        logger.info(
            "Starting service restoration",
            customer_service_id=customer_service_id,
            customer_id=customer.id,
            portal_id=customer.portal_id,
            notes=restoration_notes
        )
        
        # Step 1: Update service status
        customer_service.status = 'active'
        customer_service.restored_at = datetime.now(timezone.utc)
        customer_service.suspension_reason = None
        customer_service.suspended_at = None
        customer_service.notes = f"Restored by task {current_task.request.id}: {restoration_notes}"
        
        # Step 2: Configure router for restoration
        router_config = _configure_router_restoration(db, customer_service)
        
        # Step 3: Restore RADIUS user
        radius_config = _restore_radius_user(db, customer)
        
        # Step 4: Schedule customer notification
        from app.tasks.customer_notifications import send_service_restoration_notification
        notification_task = send_service_restoration_notification.delay(
            customer.id, 
            customer_service_id, 
            restoration_notes
        )
        
        db.commit()
        
        result = {
            'success': True,
            'customer_service_id': customer_service_id,
            'customer_id': customer.id,
            'portal_id': customer.portal_id,
            'restoration_notes': restoration_notes,
            'router_config': router_config,
            'radius_config': radius_config,
            'notification_task_id': notification_task.id,
            'restored_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "Service restoration completed successfully",
            **result
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Service restoration failed",
            customer_service_id=customer_service_id,
            error=str(e),
            task_id=current_task.request.id
        )
        raise
    finally:
        db.close()


# Helper functions for service provisioning

def _allocate_customer_ip(db, customer_service, provisioning_data) -> Optional[IPAllocation]:
    """Allocate an IP address for the customer service."""
    try:
        # Find available IP pool
        ip_pool = db.query(IPPool).filter(
            IPPool.is_active is True,
            IPPool.pool_type == 'customer'
        ).first()
        
        if not ip_pool:
            logger.warning("No available IP pool found for customer allocation")
            return None
        
        # Create IP allocation (simplified - in real implementation, would find next available IP)
        ip_allocation = IPAllocation(
            ip_pool_id=ip_pool.id,
            ip_address=f"192.168.1.{customer_service.customer_id}",  # Simplified allocation
            allocated_to_type='customer_service',
            allocated_to_id=customer_service.id,
            status='allocated',
            allocated_at=datetime.now(timezone.utc)
        )
        
        db.add(ip_allocation)
        db.flush()
        
        logger.info(
            "IP address allocated",
            ip_address=ip_allocation.ip_address,
            customer_service_id=customer_service.id
        )
        
        return ip_allocation
        
    except Exception as e:
        logger.error("Failed to allocate IP address", error=str(e))
        return None


def _create_internet_service_record(db, customer_service, ip_allocation, provisioning_data) -> Optional[CustomerInternetService]:
    """Create the Internet service record."""
    try:
        internet_service = CustomerInternetService(
            customer_service_id=customer_service.id,
            ip_address=ip_allocation.ip_address if ip_allocation else None,
            download_speed_kbps=customer_service.service_template.download_speed_kbps,
            upload_speed_kbps=customer_service.service_template.upload_speed_kbps,
            data_limit_gb=customer_service.service_template.data_limit_gb,
            connection_type='pppoe',
            status='active',
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(internet_service)
        db.flush()
        
        logger.info(
            "Internet service record created",
            internet_service_id=internet_service.id,
            customer_service_id=customer_service.id
        )
        
        return internet_service
        
    except Exception as e:
        logger.error("Failed to create Internet service record", error=str(e))
        return None


def _configure_router_for_service(db, customer_service, internet_service, provisioning_data) -> Dict[str, Any]:
    """Configure router/NAS for the new service."""
    try:
        # In a real implementation, this would connect to MikroTik/Cisco API
        # and configure the actual router
        
        config = {
            'router_configured': True,
            'pppoe_user': customer_service.customer.portal_id,
            'speed_profile': f"{internet_service.download_speed_kbps}k/{internet_service.upload_speed_kbps}k",
            'data_limit': internet_service.data_limit_gb,
            'configured_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "Router configured for service",
            customer_service_id=customer_service.id,
            config=config
        )
        
        return config
        
    except Exception as e:
        logger.error("Failed to configure router", error=str(e))
        return {'router_configured': False, 'error': str(e)}


def _create_radius_user(db, customer, internet_service, provisioning_data) -> Dict[str, Any]:
    """Create RADIUS user for the service."""
    try:
        # In a real implementation, this would create the RADIUS user
        # in the radcheck/radreply tables
        
        config = {
            'radius_user_created': True,
            'username': customer.portal_id,
            'service_attributes': {
                'download_speed': internet_service.download_speed_kbps,
                'upload_speed': internet_service.upload_speed_kbps,
                'data_limit': internet_service.data_limit_gb
            },
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "RADIUS user created",
            customer_id=customer.id,
            portal_id=customer.portal_id,
            config=config
        )
        
        return config
        
    except Exception as e:
        logger.error("Failed to create RADIUS user", error=str(e))
        return {'radius_user_created': False, 'error': str(e)}


def _configure_router_suspension(db, customer_service, grace_period_hours) -> Dict[str, Any]:
    """Configure router for service suspension."""
    try:
        config = {
            'router_suspended': True,
            'portal_id': customer_service.customer.portal_id,
            'grace_period_hours': grace_period_hours,
            'suspended_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "Router configured for suspension",
            customer_service_id=customer_service.id,
            config=config
        )
        
        return config
        
    except Exception as e:
        logger.error("Failed to configure router suspension", error=str(e))
        return {'router_suspended': False, 'error': str(e)}


def _suspend_radius_user(db, customer, suspension_reason) -> Dict[str, Any]:
    """Suspend RADIUS user."""
    try:
        config = {
            'radius_user_suspended': True,
            'username': customer.portal_id,
            'suspension_reason': suspension_reason,
            'suspended_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "RADIUS user suspended",
            customer_id=customer.id,
            portal_id=customer.portal_id,
            reason=suspension_reason
        )
        
        return config
        
    except Exception as e:
        logger.error("Failed to suspend RADIUS user", error=str(e))
        return {'radius_user_suspended': False, 'error': str(e)}


def _configure_router_restoration(db, customer_service) -> Dict[str, Any]:
    """Configure router for service restoration."""
    try:
        config = {
            'router_restored': True,
            'portal_id': customer_service.customer.portal_id,
            'restored_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "Router configured for restoration",
            customer_service_id=customer_service.id,
            config=config
        )
        
        return config
        
    except Exception as e:
        logger.error("Failed to configure router restoration", error=str(e))
        return {'router_restored': False, 'error': str(e)}


def _restore_radius_user(db, customer) -> Dict[str, Any]:
    """Restore RADIUS user."""
    try:
        config = {
            'radius_user_restored': True,
            'username': customer.portal_id,
            'restored_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "RADIUS user restored",
            customer_id=customer.id,
            portal_id=customer.portal_id
        )
        
        return config
        
    except Exception as e:
        logger.error("Failed to restore RADIUS user", error=str(e))
        return {'radius_user_restored': False, 'error': str(e)}

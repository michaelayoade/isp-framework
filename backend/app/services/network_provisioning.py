#!/usr/bin/env python3
"""
Network Provisioning Service

This service handles automated network provisioning, router configuration,
and service deployment for ISP customers.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.customer.base import Customer
from ..models.services.instances import CustomerService
from ..models.services.legacy import ServicePlan
# Using new modular network architecture
from ..models.networking.networks import NetworkSite, NetworkDevice
from ..models.networking.ipam import IPPool, IPAllocation
from ..models.networking.nas_radius import NASDevice
from ..models.services.instances import InternetService, VoiceService
from ..repositories.base import BaseRepository
from ..core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class NetworkProvisioningService:
    """
    Network Provisioning Service
    
    Handles automated provisioning of network services including:
    - Router and sector assignment
    - IP address pool management
    - Service configuration deployment
    - Network resource allocation
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize repositories for modular architecture
        self.network_device_repo = BaseRepository(NetworkDevice, db)
        self.network_site_repo = BaseRepository(NetworkSite, db)
        self.nas_device_repo = BaseRepository(NASDevice, db)
        self.ip_pool_repo = BaseRepository(IPPool, db)
        self.ip_allocation_repo = BaseRepository(IPAllocation, db)
        self.customer_service_repo = BaseRepository(CustomerService, db)
    
    def provision_customer_service(self, customer_id: int, service_plan_id: int, 
                                 router_id: Optional[int] = None, 
                                 sector_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Provision network services for a customer
        
        Args:
            customer_id: Customer ID
            service_plan_id: Service plan ID
            router_id: Optional specific router ID
            sector_id: Optional specific sector ID
            
        Returns:
            Provisioning result with assigned resources
        """
        try:
            logger.info(f"Starting network provisioning for customer {customer_id}, service plan {service_plan_id}")
            
            # Get customer and service plan
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise NotFoundError(f"Customer {customer_id} not found")
            
            service_plan = self.db.query(ServicePlan).filter(ServicePlan.id == service_plan_id).first()
            if not service_plan:
                raise NotFoundError(f"Service plan {service_plan_id} not found")
            
            # Determine optimal router and sector
            assigned_router, assigned_sector = self._assign_router_and_sector(
                customer_id, service_plan, router_id, sector_id
            )
            
            if not assigned_router:
                raise ValidationError("No suitable router available for provisioning")
            
            # Assign IP addresses
            assigned_ipv4 = self._assign_ipv4_address(customer_id, assigned_router.id)
            assigned_ipv6 = self._assign_ipv6_address(customer_id, assigned_router.id)
            
            # Create or update customer service assignment
            customer_service = self._create_customer_service_assignment(
                customer_id, service_plan_id, assigned_router.id, assigned_sector.id if assigned_sector else None
            )
            
            # Apply network configuration
            config_applied = self._apply_network_configuration(
                customer_id, service_plan, assigned_router, assigned_sector, assigned_ipv4, assigned_ipv6
            )
            
            # Log provisioning success
            logger.info(f"Network provisioning completed for customer {customer_id}")
            
            return {
                "customer_id": customer_id,
                "service_plan_id": service_plan_id,
                "provisioning_status": "completed",
                "assigned_router": {
                    "id": assigned_router.id,
                    "name": assigned_router.name,
                    "ip_address": assigned_router.management_ip
                },
                "assigned_sector": {
                    "id": assigned_sector.id,
                    "name": assigned_sector.name
                } if assigned_sector else None,
                "assigned_ipv4": assigned_ipv4,
                "assigned_ipv6": assigned_ipv6,
                "customer_service_id": customer_service.id,
                "configuration_applied": config_applied,
                "provisioning_timestamp": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error provisioning network service for customer {customer_id}: {str(e)}")
            raise
    
    def deprovision_customer_service(self, customer_id: int, service_plan_id: int) -> bool:
        """
        Deprovision network services for a customer
        """
        try:
            logger.info(f"Starting network deprovisioning for customer {customer_id}, service plan {service_plan_id}")
            
            # Find customer service assignment
            customer_service = self.db.query(CustomerService).filter(
                and_(
                    CustomerService.customer_id == customer_id,
                    CustomerService.service_plan_id == service_plan_id,
                    CustomerService.status == "active"
                )
            ).first()
            
            if not customer_service:
                logger.warning(f"No active service assignment found for customer {customer_id}")
                return False
            
            # Release IP addresses
            self._release_customer_ip_addresses(customer_id)
            
            # Remove network configuration
            self._remove_network_configuration(customer_service)
            
            # Update customer service status
            customer_service.status = "inactive"
            customer_service.end_date = datetime.now(timezone.utc)
            self.db.merge(customer_service)
            self.db.commit()
            
            logger.info(f"Network deprovisioning completed for customer {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deprovisioning network service for customer {customer_id}: {str(e)}")
            return False
    
    def get_customer_network_status(self, customer_id: int) -> Dict[str, Any]:
        """
        Get current network status for a customer
        """
        try:
            # Get active customer services
            active_services = self.db.query(CustomerService).filter(
                and_(
                    CustomerService.customer_id == customer_id,
                    CustomerService.status == "active"
                )
            ).all()
            
            if not active_services:
                return {
                    "customer_id": customer_id,
                    "status": "no_active_services",
                    "services": []
                }
            
            services_info = []
            for service in active_services:
                # Get service plan
                service_plan = self.db.query(ServicePlan).filter(
                    ServicePlan.id == service.service_plan_id
                ).first()
                
                # Get assigned IP addresses
                assigned_ips = self._get_customer_assigned_ips(customer_id)
                
                # Get router information
                router_info = None
                if hasattr(service, 'router_id') and service.router_id:
                    router = self.router_repo.get(service.router_id)
                    if router:
                        router_info = {
                            "id": router.id,
                            "name": router.name,
                            "ip_address": router.management_ip,
                            "status": router.status
                        }
                
                services_info.append({
                    "service_id": service.id,
                    "service_plan": {
                        "id": service_plan.id,
                        "name": service_plan.name,
                        "service_type": service_plan.service_type
                    } if service_plan else None,
                    "status": service.status,
                    "start_date": service.start_date,
                    "assigned_ips": assigned_ips,
                    "router": router_info
                })
            
            return {
                "customer_id": customer_id,
                "status": "active",
                "total_services": len(services_info),
                "services": services_info
            }
            
        except Exception as e:
            logger.error(f"Error getting network status for customer {customer_id}: {str(e)}")
            return {
                "customer_id": customer_id,
                "status": "error",
                "error": str(e)
            }
    
    def get_router_utilization(self, router_id: int) -> Dict[str, Any]:
        """
        Get utilization statistics for a router
        """
        try:
            router = self.router_repo.get(router_id)
            if not router:
                raise NotFoundError(f"Router {router_id} not found")
            
            # Count active customer services on this router
            active_customers = self.db.query(CustomerService).filter(
                and_(
                    CustomerService.router_id == router_id,
                    CustomerService.status == "active"
                )
            ).count()
            
            # Count assigned IP addresses
            assigned_ipv4 = self.db.query(IPv4IP).filter(
                and_(
                    IPv4IP.router_id == router_id,
                    IPv4IP.status == "assigned"
                )
            ).count()
            
            # Get total IP capacity
            total_ipv4 = self.db.query(IPv4IP).filter(
                IPv4IP.router_id == router_id
            ).count()
            
            # Calculate utilization percentages
            customer_utilization = (active_customers / router.max_customers * 100) if router.max_customers else 0
            ip_utilization = (assigned_ipv4 / total_ipv4 * 100) if total_ipv4 else 0
            
            return {
                "router_id": router_id,
                "router_name": router.name,
                "status": router.status,
                "active_customers": active_customers,
                "max_customers": router.max_customers,
                "customer_utilization_percent": round(customer_utilization, 2),
                "assigned_ipv4": assigned_ipv4,
                "total_ipv4": total_ipv4,
                "ip_utilization_percent": round(ip_utilization, 2),
                "timestamp": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error getting router utilization for router {router_id}: {str(e)}")
            raise
    
    # Private helper methods
    
    def _assign_router_and_sector(self, customer_id: int, service_plan: ServicePlan, 
                                router_id: Optional[int], sector_id: Optional[int]) -> Tuple[Optional[Router], Optional[RouterSector]]:
        """
        Assign optimal router and sector for a customer
        """
        try:
            assigned_router = None
            assigned_sector = None
            
            # If specific router requested, use it
            if router_id:
                assigned_router = self.router_repo.get(router_id)
                if not assigned_router or assigned_router.status != "active":
                    raise ValidationError(f"Requested router {router_id} is not available")
            else:
                # Find optimal router based on load and service type
                available_routers = self.db.query(Router).filter(
                    and_(
                        Router.status == "active",
                        Router.service_types.contains(service_plan.service_type)
                    )
                ).all()
                
                if not available_routers:
                    raise ValidationError(f"No routers available for service type {service_plan.service_type}")
                
                # Select router with lowest utilization
                best_router = None
                lowest_utilization = float('inf')
                
                for router in available_routers:
                    utilization = self._calculate_router_utilization(router.id)
                    if utilization < lowest_utilization:
                        lowest_utilization = utilization
                        best_router = router
                
                assigned_router = best_router
            
            # Assign sector if specified or find optimal one
            if assigned_router:
                if sector_id:
                    assigned_sector = self.db.query(RouterSector).filter(
                        and_(
                            RouterSector.id == sector_id,
                            RouterSector.router_id == assigned_router.id,
                            RouterSector.status == "active"
                        )
                    ).first()
                else:
                    # Find sector with lowest utilization
                    available_sectors = self.db.query(RouterSector).filter(
                        and_(
                            RouterSector.router_id == assigned_router.id,
                            RouterSector.status == "active"
                        )
                    ).all()
                    
                    if available_sectors:
                        # Simple selection - could be enhanced with load balancing
                        assigned_sector = available_sectors[0]
            
            return assigned_router, assigned_sector
            
        except Exception as e:
            logger.error(f"Error assigning router and sector: {str(e)}")
            raise
    
    def _assign_ipv4_address(self, customer_id: int, router_id: int) -> Optional[str]:
        """
        Assign an IPv4 address to a customer
        """
        try:
            # Find available IPv4 address in router's networks
            available_ip = self.db.query(IPv4IP).filter(
                and_(
                    IPv4IP.router_id == router_id,
                    IPv4IP.status == "available"
                )
            ).first()
            
            if available_ip:
                available_ip.status = "assigned"
                available_ip.customer_id = customer_id
                available_ip.assigned_at = datetime.now(timezone.utc)
                
                self.db.merge(available_ip)
                self.db.commit()
                
                logger.info(f"Assigned IPv4 {available_ip.ip_address} to customer {customer_id}")
                return available_ip.ip_address
            
            logger.warning(f"No available IPv4 addresses for router {router_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error assigning IPv4 address: {str(e)}")
            return None
    
    def _assign_ipv6_address(self, customer_id: int, router_id: int) -> Optional[str]:
        """
        Assign an IPv6 address to a customer
        """
        try:
            # Find available IPv6 address in router's networks
            available_ip = self.db.query(IPv6IP).filter(
                and_(
                    IPv6IP.router_id == router_id,
                    IPv6IP.status == "available"
                )
            ).first()
            
            if available_ip:
                available_ip.status = "assigned"
                available_ip.customer_id = customer_id
                available_ip.assigned_at = datetime.now(timezone.utc)
                
                self.db.merge(available_ip)
                self.db.commit()
                
                logger.info(f"Assigned IPv6 {available_ip.ip_address} to customer {customer_id}")
                return available_ip.ip_address
            
            logger.debug(f"No available IPv6 addresses for router {router_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error assigning IPv6 address: {str(e)}")
            return None
    
    def _create_customer_service_assignment(self, customer_id: int, service_plan_id: int, 
                                          router_id: int, sector_id: Optional[int]) -> CustomerService:
        """
        Create or update customer service assignment
        """
        try:
            # Check if assignment already exists
            existing_assignment = self.db.query(CustomerService).filter(
                and_(
                    CustomerService.customer_id == customer_id,
                    CustomerService.service_plan_id == service_plan_id,
                    CustomerService.status == "active"
                )
            ).first()
            
            if existing_assignment:
                # Update existing assignment
                existing_assignment.router_id = router_id
                existing_assignment.sector_id = sector_id
                existing_assignment.updated_at = datetime.now(timezone.utc)
                
                self.db.merge(existing_assignment)
                self.db.commit()
                
                return existing_assignment
            else:
                # Create new assignment
                new_assignment = CustomerService(
                    customer_id=customer_id,
                    service_plan_id=service_plan_id,
                    status="active",
                    start_date=datetime.now(timezone.utc),
                    router_id=router_id,
                    sector_id=sector_id
                )
                
                self.db.add(new_assignment)
                self.db.commit()
                
                return new_assignment
                
        except Exception as e:
            logger.error(f"Error creating customer service assignment: {str(e)}")
            raise
    
    def _apply_network_configuration(self, customer_id: int, service_plan: ServicePlan, 
                                   router: Router, sector: Optional[RouterSector], 
                                   ipv4: Optional[str], ipv6: Optional[str]) -> bool:
        """
        Apply network configuration to router/sector
        
        This is a placeholder for actual router configuration.
        In production, this would integrate with router APIs (MikroTik, Cisco, etc.)
        """
        try:
            logger.info(f"Applying network configuration for customer {customer_id} on router {router.name}")
            
            # Placeholder for router configuration
            # In production, this would:
            # 1. Connect to router management interface
            # 2. Apply bandwidth limits based on service plan
            # 3. Configure firewall rules
            # 4. Set up QoS policies
            # 5. Configure RADIUS integration
            
            # For now, just log the configuration that would be applied
            config_details = {
                "customer_id": customer_id,
                "router": router.name,
                "sector": sector.name if sector else None,
                "service_plan": service_plan.name,
                "ipv4": ipv4,
                "ipv6": ipv6,
                "bandwidth_limits": self._get_bandwidth_limits(service_plan),
                "timestamp": datetime.now(timezone.utc)
            }
            
            logger.info(f"Network configuration applied: {config_details}")
            
            # Return True to indicate successful configuration
            return True
            
        except Exception as e:
            logger.error(f"Error applying network configuration: {str(e)}")
            return False
    
    def _remove_network_configuration(self, customer_service: CustomerService) -> bool:
        """
        Remove network configuration from router/sector
        """
        try:
            logger.info(f"Removing network configuration for customer service {customer_service.id}")
            
            # Placeholder for configuration removal
            # In production, this would remove customer-specific configuration from router
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing network configuration: {str(e)}")
            return False
    
    def _release_customer_ip_addresses(self, customer_id: int) -> None:
        """
        Release all IP addresses assigned to a customer
        """
        try:
            # Release IPv4 addresses
            ipv4_addresses = self.db.query(IPv4IP).filter(
                IPv4IP.customer_id == customer_id
            ).all()
            
            for ip in ipv4_addresses:
                ip.status = "available"
                ip.customer_id = None
                ip.assigned_at = None
                self.db.merge(ip)
            
            # Release IPv6 addresses
            ipv6_addresses = self.db.query(IPv6IP).filter(
                IPv6IP.customer_id == customer_id
            ).all()
            
            for ip in ipv6_addresses:
                ip.status = "available"
                ip.customer_id = None
                ip.assigned_at = None
                self.db.merge(ip)
            
            self.db.commit()
            logger.info(f"Released IP addresses for customer {customer_id}")
            
        except Exception as e:
            logger.error(f"Error releasing IP addresses for customer {customer_id}: {str(e)}")
    
    def _get_customer_assigned_ips(self, customer_id: int) -> Dict[str, List[str]]:
        """
        Get all IP addresses assigned to a customer
        """
        try:
            ipv4_addresses = self.db.query(IPv4IP).filter(
                IPv4IP.customer_id == customer_id
            ).all()
            
            ipv6_addresses = self.db.query(IPv6IP).filter(
                IPv6IP.customer_id == customer_id
            ).all()
            
            return {
                "ipv4": [ip.ip_address for ip in ipv4_addresses],
                "ipv6": [ip.ip_address for ip in ipv6_addresses]
            }
            
        except Exception as e:
            logger.error(f"Error getting assigned IPs for customer {customer_id}: {str(e)}")
            return {"ipv4": [], "ipv6": []}
    
    def _calculate_router_utilization(self, router_id: int) -> float:
        """
        Calculate router utilization percentage
        """
        try:
            router = self.router_repo.get(router_id)
            if not router:
                return 100.0  # Consider unavailable routers as fully utilized
            
            active_customers = self.db.query(CustomerService).filter(
                and_(
                    CustomerService.router_id == router_id,
                    CustomerService.status == "active"
                )
            ).count()
            
            if router.max_customers:
                return (active_customers / router.max_customers) * 100
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating router utilization: {str(e)}")
            return 100.0  # Consider error as fully utilized
    
    def _get_bandwidth_limits(self, service_plan: ServicePlan) -> Dict[str, Any]:
        """
        Get bandwidth limits from service plan
        """
        try:
            limits = {}
            
            if service_plan.service_type == "internet":
                internet_service = self.db.query(InternetService).filter(
                    InternetService.service_plan_id == service_plan.id
                ).first()
                
                if internet_service:
                    limits["download_speed"] = internet_service.download_speed
                    limits["upload_speed"] = internet_service.upload_speed
                    limits["data_limit"] = internet_service.data_limit
            
            return limits
            
        except Exception as e:
            logger.error(f"Error getting bandwidth limits: {str(e)}")
            return {}

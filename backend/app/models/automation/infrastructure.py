"""Ansible automation infrastructure models for device and site management."""

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Site(Base):
    """Physical sites/locations for network infrastructure."""

    __tablename__ = "automation_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Location Information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)

    # Site Classification
    site_type = Column(
        String(50), nullable=False
    )  # datacenter, pop, tower, office, customer_premises
    tier = Column(String(20), nullable=True)  # tier1, tier2, tier3 for criticality

    # Contact Information
    contact_person = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Technical Details
    power_type = Column(String(50), nullable=True)  # grid, generator, ups, solar
    connectivity_type = Column(String(50), nullable=True)  # fiber, wireless, satellite
    rack_count = Column(Integer, default=0)

    # Status and Monitoring
    is_active = Column(Boolean, default=True)
    monitoring_enabled = Column(Boolean, default=True)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    devices = relationship("AutomationDevice", back_populates="site")
    provisioning_tasks = relationship("ProvisioningTask", back_populates="site")

    def __repr__(self):
        return f"<Site(id={self.id}, name={self.name}, code={self.code}, type={self.site_type})>"


class AutomationDevice(Base):
    """Network devices managed by Ansible automation."""

    __tablename__ = "automation_devices"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), nullable=False, unique=True, index=True)

    # Device Classification
    device_type = Column(
        String(50), nullable=False
    )  # router, switch, olt, onu, ap, firewall
    vendor = Column(
        String(50), nullable=False
    )  # mikrotik, cisco, huawei, zte, ubiquiti
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True, unique=True)

    # Network Configuration
    management_ip = Column(String(45), nullable=False, index=True)
    management_port = Column(Integer, default=22)
    management_protocol = Column(String(20), default="ssh")  # ssh, telnet, snmp, api

    # Location
    site_id = Column(
        Integer, ForeignKey("automation_sites.id"), nullable=False, index=True
    )
    rack_position = Column(String(50), nullable=True)
    physical_location = Column(String(255), nullable=True)

    # Device Status
    status = Column(
        String(20), nullable=False, default="active"
    )  # active, inactive, maintenance, faulty
    is_managed = Column(
        Boolean, default=True
    )  # Whether device is under Ansible management
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Software Information
    os_version = Column(String(100), nullable=True)
    firmware_version = Column(String(100), nullable=True)
    config_version = Column(String(100), nullable=True)
    last_backup = Column(DateTime(timezone=True), nullable=True)

    # Ansible Integration
    ansible_host_group = Column(String(100), nullable=True)  # Ansible inventory group
    ansible_variables = Column(JSON, default=dict)  # Host-specific variables
    playbook_tags = Column(JSON, default=list)  # Applicable playbook tags

    # Performance Metrics
    cpu_usage_percent = Column(DECIMAL(5, 2), nullable=True)
    memory_usage_percent = Column(DECIMAL(5, 2), nullable=True)
    uptime_days = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    site = relationship("Site", back_populates="devices")
    credentials = relationship("DeviceCredential", back_populates="device")
    provisioning_tasks = relationship("ProvisioningTask", back_populates="device")

    # Indexes for performance
    __table_args__ = (
        Index("idx_device_site_type", "site_id", "device_type"),
        Index("idx_device_vendor_model", "vendor", "model"),
        Index("idx_device_status", "status"),
    )

    def __repr__(self):
        return f"<AutomationDevice(id={self.id}, hostname={self.hostname}, type={self.device_type}, vendor={self.vendor})>"

    @property
    def is_online(self) -> bool:
        """Check if device is currently online."""
        if not self.last_seen:
            return False
        # Consider device online if seen within last 10 minutes
        from datetime import timedelta

        return (func.now() - self.last_seen) < timedelta(minutes=10)


class DeviceCredential(Base):
    """Encrypted credentials for device access."""

    __tablename__ = "automation_device_credentials"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("automation_devices.id"), nullable=False, index=True
    )

    # Credential Information
    credential_type = Column(String(20), nullable=False)  # ssh, snmp, api, web
    username = Column(String(255), nullable=True)
    password_encrypted = Column(Text, nullable=True)  # Encrypted password
    private_key_encrypted = Column(Text, nullable=True)  # Encrypted SSH private key

    # SNMP Specific
    snmp_community = Column(String(255), nullable=True)
    snmp_version = Column(String(10), nullable=True)  # v1, v2c, v3

    # API Specific
    api_key_encrypted = Column(Text, nullable=True)
    api_secret_encrypted = Column(Text, nullable=True)

    # Status and Validation
    is_active = Column(Boolean, default=True)
    last_validated = Column(DateTime(timezone=True), nullable=True)
    validation_status = Column(
        String(20), default="pending"
    )  # pending, valid, invalid, expired

    # Security
    created_by = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    encryption_key_id = Column(
        String(100), nullable=True
    )  # Reference to encryption key

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("AutomationDevice", back_populates="credentials")
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<DeviceCredential(id={self.id}, device_id={self.device_id}, type={self.credential_type})>"


class ProvisioningTask(Base):
    """Ansible provisioning and configuration tasks."""

    __tablename__ = "automation_provisioning_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Task Classification
    task_type = Column(
        String(50), nullable=False
    )  # provision, configure, backup, update, monitor
    category = Column(
        String(50), nullable=True
    )  # customer_setup, maintenance, security, monitoring
    priority = Column(String(20), default="medium")  # low, medium, high, critical

    # Target Information
    device_id = Column(
        Integer, ForeignKey("automation_devices.id"), nullable=True, index=True
    )
    site_id = Column(
        Integer, ForeignKey("automation_sites.id"), nullable=True, index=True
    )
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    service_id = Column(
        Integer, ForeignKey("customer_services.id"), nullable=True, index=True
    )

    # Ansible Configuration
    playbook_name = Column(String(255), nullable=False)
    playbook_tags = Column(JSON, default=list)
    ansible_variables = Column(JSON, default=dict)
    inventory_groups = Column(JSON, default=list)

    # Execution Details
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, running, completed, failed, cancelled
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Results and Logging
    exit_code = Column(Integer, nullable=True)
    stdout_log = Column(Text, nullable=True)
    stderr_log = Column(Text, nullable=True)
    ansible_facts = Column(JSON, default=dict)  # Gathered facts from execution

    # Retry and Dependencies
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    depends_on_task_id = Column(
        Integer, ForeignKey("automation_provisioning_tasks.id"), nullable=True
    )

    # Execution Context
    executed_by = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    execution_node = Column(
        String(255), nullable=True
    )  # Which server executed the task

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("AutomationDevice", back_populates="provisioning_tasks")
    site = relationship("Site", back_populates="provisioning_tasks")
    customer = relationship("Customer")
    service = relationship("CustomerService")
    executor = relationship("Administrator", foreign_keys=[executed_by])
    dependency = relationship("ProvisioningTask", remote_side=[id])

    # Indexes for performance
    __table_args__ = (
        Index("idx_task_status_priority", "status", "priority"),
        Index("idx_task_device_status", "device_id", "status"),
        Index("idx_task_scheduled_at", "scheduled_at"),
        Index("idx_task_type_category", "task_type", "category"),
    )

    def __repr__(self):
        return f"<ProvisioningTask(id={self.id}, name={self.task_name}, status={self.status}, type={self.task_type})>"

    @property
    def is_running(self) -> bool:
        """Check if task is currently running."""
        return self.status == "running"

    @property
    def duration_seconds(self) -> int:
        """Calculate task execution duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        elif self.started_at:
            return int((func.now() - self.started_at).total_seconds())
        return 0


class AnsiblePlaybook(Base):
    """Ansible playbook definitions and metadata."""

    __tablename__ = "automation_ansible_playbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Playbook Information
    file_path = Column(String(500), nullable=False)  # Path to playbook file
    version = Column(String(50), default="1.0")

    # Classification
    category = Column(
        String(50), nullable=False
    )  # provisioning, configuration, maintenance, monitoring
    device_types = Column(JSON, default=list)  # Supported device types
    vendors = Column(JSON, default=list)  # Supported vendors

    # Execution Parameters
    default_variables = Column(JSON, default=dict)
    required_variables = Column(JSON, default=list)
    tags = Column(JSON, default=list)

    # Validation and Testing
    is_tested = Column(Boolean, default=False)
    test_results = Column(JSON, default=dict)
    last_tested = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_production_ready = Column(Boolean, default=False)

    # Metadata
    author = Column(String(255), nullable=True)
    documentation_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AnsiblePlaybook(id={self.id}, name={self.name}, category={self.category})>"

"""
Plugin System Models for ISP Framework

Handles dynamic plugin loading, registration, lifecycle management,
and integration with the ISP Framework core systems.
"""

from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class PluginStatus(PyEnum):
    """Plugin status enumeration"""

    INACTIVE = "inactive"
    ACTIVE = "active"
    LOADING = "loading"
    ERROR = "error"
    DISABLED = "disabled"
    UPDATING = "updating"


class PluginType(PyEnum):
    """Plugin type enumeration"""

    COMMUNICATION = "communication"
    BILLING = "billing"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    STORAGE = "storage"
    MONITORING = "monitoring"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class PluginPriority(PyEnum):
    """Plugin priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Plugin(Base):
    """Core plugin model for managing installed plugins"""

    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)

    # Basic plugin information
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), nullable=False)
    author = Column(String(255))
    license = Column(String(100))
    homepage = Column(String(500))

    # Plugin classification
    plugin_type = Column(Enum(PluginType), nullable=False)
    category = Column(String(100))
    tags = Column(JSON, default=list)

    # Plugin status and configuration
    status = Column(Enum(PluginStatus), default=PluginStatus.INACTIVE)
    priority = Column(Enum(PluginPriority), default=PluginPriority.NORMAL)
    is_system = Column(Boolean, default=False)  # System plugins can't be uninstalled
    is_enabled = Column(Boolean, default=True)

    # Plugin files and paths
    module_path = Column(String(500), nullable=False)  # Python module path
    entry_point = Column(String(255), nullable=False)  # Main plugin class
    config_schema = Column(JSON, default=dict)  # Configuration schema

    # Plugin metadata
    requirements = Column(JSON, default=list)  # Python dependencies
    supported_versions = Column(JSON, default=list)  # ISP Framework versions
    api_version = Column(String(20), default="1.0")

    # Installation and update info
    installed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_loaded = Column(DateTime(timezone=True))
    installed_by = Column(Integer, ForeignKey("administrators.id"))

    # Plugin statistics
    load_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)

    # Relationships
    installer = relationship("Administrator")
    configurations = relationship(
        "PluginConfiguration", back_populates="plugin", cascade="all, delete-orphan"
    )
    hooks = relationship(
        "PluginHook", back_populates="plugin", cascade="all, delete-orphan"
    )
    logs = relationship(
        "PluginLog", back_populates="plugin", cascade="all, delete-orphan"
    )
    dependencies = relationship(
        "PluginDependency",
        foreign_keys="PluginDependency.plugin_id",
        back_populates="plugin",
    )


class PluginConfiguration(Base):
    """Plugin configuration storage"""

    __tablename__ = "plugin_configurations"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"), nullable=False)

    # Configuration data
    config_key = Column(String(255), nullable=False)
    config_value = Column(JSON)
    config_type = Column(
        String(50), default="string"
    )  # string, number, boolean, object, array

    # Configuration metadata
    is_encrypted = Column(Boolean, default=False)
    is_required = Column(Boolean, default=False)
    description = Column(Text)
    default_value = Column(JSON)

    # Validation
    validation_rules = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("administrators.id"))

    # Relationships
    plugin = relationship("Plugin", back_populates="configurations")
    updater = relationship("Administrator")

    # Unique constraint
    __table_args__ = ({"extend_existing": True},)


class PluginHook(Base):
    """Plugin hook registration for event handling"""

    __tablename__ = "plugin_hooks"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"), nullable=False)

    # Hook information
    hook_name = Column(
        String(255), nullable=False
    )  # e.g., "customer.created", "invoice.generated"
    hook_type = Column(String(50), nullable=False)  # action, filter, event
    callback_method = Column(String(255), nullable=False)  # Method to call in plugin

    # Hook configuration
    priority = Column(Integer, default=100)  # Lower = higher priority
    is_active = Column(Boolean, default=True)
    conditions = Column(JSON, default=dict)  # Conditions for hook execution

    # Hook metadata
    description = Column(Text)
    parameters = Column(JSON, default=dict)  # Expected parameters
    return_type = Column(String(100))  # Expected return type

    # Statistics
    execution_count = Column(Integer, default=0)
    last_executed = Column(DateTime(timezone=True))
    average_execution_time = Column(Integer, default=0)  # Milliseconds

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plugin = relationship("Plugin", back_populates="hooks")


class PluginDependency(Base):
    """Plugin dependency management"""

    __tablename__ = "plugin_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"), nullable=False)

    # Dependency information
    dependency_type = Column(String(50), nullable=False)  # plugin, package, service
    dependency_name = Column(String(255), nullable=False)
    version_constraint = Column(String(100))  # e.g., ">=1.0.0", "~1.2.0"

    # Dependency status
    is_satisfied = Column(Boolean, default=False)
    is_optional = Column(Boolean, default=False)

    # Metadata
    description = Column(Text)
    install_command = Column(String(500))  # Command to install dependency

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plugin = relationship("Plugin", back_populates="dependencies")


class PluginLog(Base):
    """Plugin execution and error logging"""

    __tablename__ = "plugin_logs"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"), nullable=False)

    # Log information
    log_level = Column(
        String(20), nullable=False
    )  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    context = Column(JSON, default=dict)  # Additional context data

    # Execution context
    hook_name = Column(String(255))  # Hook that was executed
    execution_time = Column(Integer)  # Execution time in milliseconds
    stack_trace = Column(Text)  # Stack trace for errors

    # Request context
    request_id = Column(String(100))  # Request ID for tracing
    user_id = Column(Integer, ForeignKey("administrators.id"))
    ip_address = Column(String(45))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    plugin = relationship("Plugin", back_populates="logs")
    user = relationship("Administrator")


class PluginRegistry(Base):
    """Plugin registry for available plugins"""

    __tablename__ = "plugin_registry"

    id = Column(Integer, primary_key=True, index=True)

    # Registry information
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Plugin details
    plugin_type = Column(Enum(PluginType), nullable=False)
    latest_version = Column(String(50), nullable=False)
    author = Column(String(255))
    license = Column(String(100))

    # Repository information
    repository_url = Column(String(500))
    download_url = Column(String(500))
    documentation_url = Column(String(500))

    # Plugin metadata
    requirements = Column(JSON, default=list)
    supported_versions = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    screenshots = Column(JSON, default=list)

    # Registry statistics
    download_count = Column(Integer, default=0)
    rating = Column(Integer, default=0)  # 1-5 stars
    review_count = Column(Integer, default=0)

    # Status
    is_verified = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_deprecated = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    installations = relationship(
        "Plugin",
        primaryjoin="PluginRegistry.name == Plugin.name",
        foreign_keys="Plugin.name",
        viewonly=True,
    )


class PluginTemplate(Base):
    """Plugin templates for quick plugin creation"""

    __tablename__ = "plugin_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template information
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Template details
    plugin_type = Column(Enum(PluginType), nullable=False)
    template_version = Column(String(50), nullable=False)

    # Template files
    template_files = Column(JSON, default=dict)  # File paths and contents
    config_schema = Column(JSON, default=dict)  # Configuration schema

    # Template metadata
    author = Column(String(255))
    documentation = Column(Text)
    example_usage = Column(Text)

    # Template status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)

    # Statistics
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("administrators.id"))

    # Relationships
    creator = relationship("Administrator")


# Add relationships to existing models
# These will be added via migration scripts or model updates

"""
# Add to Administrator model:
installed_plugins = relationship("Plugin", back_populates="installer")
plugin_configurations = relationship("PluginConfiguration", back_populates="updater")
plugin_logs = relationship("PluginLog", back_populates="user")
plugin_templates = relationship("PluginTemplate", back_populates="creator")
"""

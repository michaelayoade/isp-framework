"""
Audit System Startup Integration

This module handles the initialization and startup of the enhanced audit system,
including model configuration, processor startup, and health monitoring.
"""

import asyncio
import logging
from typing import Dict, Any
from app.core.database import get_db
from app.core.audit_config import configure_audit_tracking, get_audit_configuration_status
from app.services.audit_processor import audit_processor_manager, start_default_audit_processor
from app.models.audit import get_audit_processing_stats
import traceback

logger = logging.getLogger(__name__)


class AuditSystemStartup:
    """
    Manages the startup and initialization of the enhanced audit system.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.initialization_status = {}
        self.startup_errors = []
    
    async def initialize_audit_system(self) -> Dict[str, Any]:
        """
        Initialize the complete audit system during application startup.
        
        Returns:
            Dictionary containing initialization status and results
        """
        logger.info("Starting enhanced audit system initialization...")
        
        try:
            # Step 1: Configure audit tracking for models
            logger.info("Step 1: Configuring audit tracking for models...")
            model_config_result = self._configure_model_auditing()
            
            # Step 2: Start default audit processor
            logger.info("Step 2: Starting default audit processor...")
            processor_result = await self._start_audit_processors()
            
            # Step 3: Validate system health
            logger.info("Step 3: Validating audit system health...")
            health_result = await self._validate_audit_health()
            
            # Step 4: Log initialization summary
            self._log_initialization_summary(model_config_result, processor_result, health_result)
            
            self.initialization_status = {
                'model_configuration': model_config_result,
                'processor_startup': processor_result,
                'health_validation': health_result,
                'is_initialized': True,
                'startup_errors': self.startup_errors,
                'success': len(self.startup_errors) == 0
            }
            
            self.is_initialized = True
            logger.info("Enhanced audit system initialization completed successfully")
            
            return self.initialization_status
            
        except Exception as e:
            error_msg = f"Failed to initialize audit system: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            self.startup_errors.append(error_msg)
            self.initialization_status = {
                'is_initialized': False,
                'startup_errors': self.startup_errors,
                'success': False,
                'error': str(e)
            }
            
            return self.initialization_status
    
    def _configure_model_auditing(self) -> Dict[str, Any]:
        """Configure audit tracking for critical models."""
        try:
            logger.info("Configuring audit tracking for critical models...")
            
            # Get current configuration status
            config_status = get_audit_configuration_status()
            logger.info(f"Audit configuration status: {config_status}")
            
            # Configure audit tracking
            config_result = configure_audit_tracking()
            
            if config_result['success']:
                logger.info(f"Successfully enabled audit tracking for {config_result['total_enabled']} models")
            else:
                error_msg = f"Some models failed audit configuration: {config_result['total_failed']} failures"
                logger.warning(error_msg)
                self.startup_errors.append(error_msg)
            
            return {
                'success': config_result['success'],
                'enabled_count': config_result['total_enabled'],
                'failed_count': config_result['total_failed'],
                'configuration_status': config_status
            }
            
        except Exception as e:
            error_msg = f"Failed to configure model auditing: {e}"
            logger.error(error_msg)
            self.startup_errors.append(error_msg)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _start_audit_processors(self) -> Dict[str, Any]:
        """Start the default audit processor."""
        try:
            logger.info("Starting default audit processor...")
            
            # Start the default audit processor
            await start_default_audit_processor()
            
            # Give it a moment to initialize
            await asyncio.sleep(1)
            
            # Get processor statistics
            processor_stats = audit_processor_manager.get_processor_stats()
            
            logger.info(f"Audit processor started successfully: {processor_stats}")
            
            return {
                'success': True,
                'processor_stats': processor_stats
            }
            
        except Exception as e:
            error_msg = f"Failed to start audit processors: {e}"
            logger.error(error_msg)
            self.startup_errors.append(error_msg)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _validate_audit_health(self) -> Dict[str, Any]:
        """Validate the health of the audit system."""
        try:
            logger.info("Validating audit system health...")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Get audit processing statistics
                audit_stats = get_audit_processing_stats(db)
                
                # Check if audit tables are accessible
                from app.models.audit import AuditQueue, ConfigurationSnapshot, CDCLog, AuditProcessingStatus
                
                queue_count = db.query(AuditQueue).count()
                snapshot_count = db.query(ConfigurationSnapshot).count()
                cdc_count = db.query(CDCLog).count()
                processor_count = db.query(AuditProcessingStatus).count()
                
                health_data = {
                    'audit_stats': audit_stats,
                    'table_counts': {
                        'audit_queue': queue_count,
                        'configuration_snapshots': snapshot_count,
                        'cdc_log': cdc_count,
                        'audit_processing_status': processor_count
                    }
                }
                
                logger.info(f"Audit system health validation successful: {health_data}")
                
                return {
                    'success': True,
                    'health_data': health_data
                }
                
            finally:
                db.close()
            
        except Exception as e:
            error_msg = f"Failed to validate audit health: {e}"
            logger.error(error_msg)
            self.startup_errors.append(error_msg)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _log_initialization_summary(self, model_result, processor_result, health_result):
        """Log a comprehensive initialization summary."""
        logger.info("=== Enhanced Audit System Initialization Summary ===")
        
        # Model configuration summary
        if model_result['success']:
            logger.info(f"✅ Model Configuration: {model_result['enabled_count']} models enabled")
        else:
            logger.warning(f"⚠️  Model Configuration: {model_result['failed_count']} failures")
        
        # Processor startup summary
        if processor_result['success']:
            logger.info("✅ Audit Processor: Started successfully")
        else:
            logger.error("❌ Audit Processor: Failed to start")
        
        # Health validation summary
        if health_result['success']:
            logger.info("✅ Health Validation: All systems operational")
        else:
            logger.error("❌ Health Validation: Issues detected")
        
        # Overall status
        if len(self.startup_errors) == 0:
            logger.info("🎉 Enhanced Audit System: Fully operational and ready for production")
        else:
            logger.warning(f"⚠️  Enhanced Audit System: Operational with {len(self.startup_errors)} warnings")
        
        logger.info("=== End Initialization Summary ===")
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """Get the current initialization status."""
        return self.initialization_status.copy()
    
    async def shutdown_audit_system(self):
        """Gracefully shutdown the audit system."""
        try:
            logger.info("Shutting down enhanced audit system...")
            
            # Stop all audit processors
            await audit_processor_manager.stop_all_processors()
            
            logger.info("Enhanced audit system shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during audit system shutdown: {e}")


# Global audit system startup instance
audit_system_startup = AuditSystemStartup()


async def initialize_audit_system():
    """
    Initialize the enhanced audit system.
    
    This function should be called during application startup.
    """
    return await audit_system_startup.initialize_audit_system()


async def shutdown_audit_system():
    """
    Shutdown the enhanced audit system.
    
    This function should be called during application shutdown.
    """
    await audit_system_startup.shutdown_audit_system()


def get_audit_initialization_status():
    """Get the current audit system initialization status."""
    return audit_system_startup.get_initialization_status()


# Startup event handlers for FastAPI
async def audit_startup_event():
    """FastAPI startup event handler for audit system."""
    logger.info("FastAPI startup: Initializing enhanced audit system...")
    
    try:
        result = await initialize_audit_system()
        
        if result['success']:
            logger.info("FastAPI startup: Enhanced audit system initialized successfully")
        else:
            logger.warning("FastAPI startup: Enhanced audit system initialized with warnings")
            
    except Exception as e:
        logger.error(f"FastAPI startup: Failed to initialize enhanced audit system: {e}")


async def audit_shutdown_event():
    """FastAPI shutdown event handler for audit system."""
    logger.info("FastAPI shutdown: Shutting down enhanced audit system...")
    
    try:
        await shutdown_audit_system()
        logger.info("FastAPI shutdown: Enhanced audit system shutdown completed")
        
    except Exception as e:
        logger.error(f"FastAPI shutdown: Error during audit system shutdown: {e}")


# Health check functions
def is_audit_system_healthy() -> bool:
    """Check if the audit system is healthy and operational."""
    try:
        status = audit_system_startup.get_initialization_status()
        return status.get('is_initialized', False) and status.get('success', False)
    except Exception:
        return False


def get_audit_system_status() -> Dict[str, Any]:
    """Get comprehensive audit system status for monitoring."""
    try:
        initialization_status = audit_system_startup.get_initialization_status()
        processor_stats = audit_processor_manager.get_processor_stats()
        
        return {
            'is_healthy': is_audit_system_healthy(),
            'initialization_status': initialization_status,
            'processor_stats': processor_stats,
            'timestamp': logger.info("Getting audit system status...")
        }
        
    except Exception as e:
        return {
            'is_healthy': False,
            'error': str(e),
            'timestamp': logger.error(f"Failed to get audit system status: {e}")
        }

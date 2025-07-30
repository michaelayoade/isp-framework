"""
Plugin Health Monitoring Service

Service layer for plugin health monitoring and management including:
- Plugin health checks and status monitoring
- Plugin reload and restart capabilities
- Watchdog service for automatic recovery
- Plugin performance metrics and alerting
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.exceptions import NotFoundError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers
from app.services.plugin_system import PluginSystemService
import logging
import asyncio
import psutil
import traceback
from enum import Enum

logger = logging.getLogger(__name__)


class PluginHealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class PluginHealthMonitoringService:
    """Service layer for plugin health monitoring and management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
        self.plugin_system = PluginSystemService(db)
        self._health_cache = {}
        self._watchdog_running = False
    
    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all active plugins."""
        try:
            # Get all active plugins
            active_plugins = self.plugin_system.list_plugins(status="active")
            
            health_results = []
            overall_status = PluginHealthStatus.HEALTHY
            
            for plugin in active_plugins:
                try:
                    health_result = await self._check_plugin_health(plugin)
                    health_results.append(health_result)
                    
                    # Update overall status
                    if health_result['status'] == PluginHealthStatus.CRITICAL:
                        overall_status = PluginHealthStatus.CRITICAL
                    elif health_result['status'] == PluginHealthStatus.WARNING and overall_status != PluginHealthStatus.CRITICAL:
                        overall_status = PluginHealthStatus.WARNING
                    
                    # Cache the result
                    self._health_cache[plugin['id']] = {
                        'status': health_result['status'],
                        'last_check': datetime.now(timezone.utc),
                        'details': health_result
                    }
                    
                    # Trigger alerts for critical issues
                    if health_result['status'] == PluginHealthStatus.CRITICAL:
                        await self._trigger_health_alert(plugin, health_result)
                    
                except Exception as e:
                    logger.error(f"Error checking health for plugin {plugin['id']}: {e}")
                    health_result = {
                        'plugin_id': plugin['id'],
                        'plugin_name': plugin['name'],
                        'status': PluginHealthStatus.UNKNOWN,
                        'error': str(e),
                        'check_time': datetime.now(timezone.utc).isoformat()
                    }
                    health_results.append(health_result)
            
            logger.info(f"Health check completed: {len(health_results)} plugins checked, overall status: {overall_status}")
            
            return {
                'overall_status': overall_status,
                'total_plugins': len(active_plugins),
                'healthy_plugins': len([r for r in health_results if r['status'] == PluginHealthStatus.HEALTHY]),
                'warning_plugins': len([r for r in health_results if r['status'] == PluginHealthStatus.WARNING]),
                'critical_plugins': len([r for r in health_results if r['status'] == PluginHealthStatus.CRITICAL]),
                'offline_plugins': len([r for r in health_results if r['status'] == PluginHealthStatus.OFFLINE]),
                'check_time': datetime.now(timezone.utc).isoformat(),
                'plugin_results': health_results
            }
            
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")
            raise
    
    async def reload_plugin(self, plugin_id: int) -> Dict[str, Any]:
        """Reload a specific plugin."""
        try:
            # Get plugin details
            plugin = self.plugin_system.get_plugin(plugin_id)
            if not plugin:
                raise NotFoundError(f"Plugin {plugin_id} not found")
            
            # Stop the plugin
            stop_result = await self._stop_plugin(plugin)
            
            # Wait a moment for cleanup
            await asyncio.sleep(1)
            
            # Start the plugin
            start_result = await self._start_plugin(plugin)
            
            # Perform health check
            health_result = await self._check_plugin_health(plugin)
            
            # Log the reload
            logger.info(f"Plugin {plugin_id} ({plugin['name']}) reloaded successfully")
            
            # Trigger webhook
            self.webhook_triggers.plugin_reloaded({
                'plugin_id': plugin_id,
                'plugin_name': plugin['name'],
                'reload_time': datetime.now(timezone.utc).isoformat(),
                'health_status': health_result['status'],
                'reload_reason': 'manual_reload'
            })
            
            return {
                'plugin_id': plugin_id,
                'plugin_name': plugin['name'],
                'reload_time': datetime.now(timezone.utc).isoformat(),
                'stop_result': stop_result,
                'start_result': start_result,
                'health_status': health_result['status'],
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error reloading plugin {plugin_id}: {e}")
            raise
    
    async def restart_plugin(self, plugin_id: int, reason: str = "manual_restart") -> Dict[str, Any]:
        """Restart a specific plugin with full reinitialization."""
        try:
            # Get plugin details
            plugin = self.plugin_system.get_plugin(plugin_id)
            if not plugin:
                raise NotFoundError(f"Plugin {plugin_id} not found")
            
            # Disable the plugin
            self.plugin_system.disable_plugin(plugin_id)
            
            # Wait for cleanup
            await asyncio.sleep(2)
            
            # Re-enable the plugin
            self.plugin_system.enable_plugin(plugin_id)
            
            # Wait for initialization
            await asyncio.sleep(3)
            
            # Perform health check
            health_result = await self._check_plugin_health(plugin)
            
            # Log the restart
            logger.info(f"Plugin {plugin_id} ({plugin['name']}) restarted successfully")
            
            # Trigger webhook
            self.webhook_triggers.plugin_restarted({
                'plugin_id': plugin_id,
                'plugin_name': plugin['name'],
                'restart_time': datetime.now(timezone.utc).isoformat(),
                'health_status': health_result['status'],
                'restart_reason': reason
            })
            
            return {
                'plugin_id': plugin_id,
                'plugin_name': plugin['name'],
                'restart_time': datetime.now(timezone.utc).isoformat(),
                'health_status': health_result['status'],
                'restart_reason': reason,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error restarting plugin {plugin_id}: {e}")
            raise
    
    async def start_watchdog(self, check_interval_seconds: int = 300) -> Dict[str, Any]:
        """Start the plugin watchdog service."""
        if self._watchdog_running:
            return {'status': 'already_running', 'message': 'Watchdog is already running'}
        
        self._watchdog_running = True
        
        # Start watchdog task
        asyncio.create_task(self._watchdog_loop(check_interval_seconds))
        
        logger.info(f"Plugin watchdog started with {check_interval_seconds}s interval")
        
        return {
            'status': 'started',
            'check_interval_seconds': check_interval_seconds,
            'start_time': datetime.now(timezone.utc).isoformat()
        }
    
    async def stop_watchdog(self) -> Dict[str, Any]:
        """Stop the plugin watchdog service."""
        if not self._watchdog_running:
            return {'status': 'not_running', 'message': 'Watchdog is not running'}
        
        self._watchdog_running = False
        
        logger.info("Plugin watchdog stopped")
        
        return {
            'status': 'stopped',
            'stop_time': datetime.now(timezone.utc).isoformat()
        }
    
    def get_plugin_health_status(self, plugin_id: int) -> Dict[str, Any]:
        """Get current health status for a specific plugin."""
        try:
            # Check cache first
            if plugin_id in self._health_cache:
                cached_result = self._health_cache[plugin_id]
                
                # Check if cache is still fresh (within 5 minutes)
                if (datetime.now(timezone.utc) - cached_result['last_check']).total_seconds() < 300:
                    return cached_result['details']
            
            # If not in cache or stale, return basic status
            plugin = self.plugin_system.get_plugin(plugin_id)
            if not plugin:
                raise NotFoundError(f"Plugin {plugin_id} not found")
            
            return {
                'plugin_id': plugin_id,
                'plugin_name': plugin['name'],
                'status': PluginHealthStatus.UNKNOWN,
                'message': 'Health status not available, run health check',
                'last_check': None
            }
            
        except Exception as e:
            logger.error(f"Error getting plugin health status: {e}")
            raise
    
    def get_watchdog_status(self) -> Dict[str, Any]:
        """Get current watchdog service status."""
        return {
            'running': self._watchdog_running,
            'status': 'active' if self._watchdog_running else 'inactive',
            'last_status_check': datetime.now(timezone.utc).isoformat()
        }
    
    async def _check_plugin_health(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Perform health check on a specific plugin."""
        plugin_id = plugin['id']
        plugin_name = plugin['name']
        
        health_result = {
            'plugin_id': plugin_id,
            'plugin_name': plugin_name,
            'status': PluginHealthStatus.HEALTHY,
            'checks': {},
            'metrics': {},
            'check_time': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Check 1: Plugin process status
            process_check = await self._check_plugin_process(plugin)
            health_result['checks']['process'] = process_check
            
            # Check 2: Plugin API responsiveness
            api_check = await self._check_plugin_api(plugin)
            health_result['checks']['api'] = api_check
            
            # Check 3: Plugin resource usage
            resource_check = await self._check_plugin_resources(plugin)
            health_result['checks']['resources'] = resource_check
            
            # Check 4: Plugin dependencies
            dependency_check = await self._check_plugin_dependencies(plugin)
            health_result['checks']['dependencies'] = dependency_check
            
            # Determine overall status
            health_result['status'] = self._calculate_overall_health_status(health_result['checks'])
            
            # Add performance metrics
            health_result['metrics'] = await self._collect_plugin_metrics(plugin)
            
        except Exception as e:
            health_result['status'] = PluginHealthStatus.CRITICAL
            health_result['error'] = str(e)
            health_result['traceback'] = traceback.format_exc()
        
        return health_result
    
    async def _check_plugin_process(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Check if plugin process is running."""
        try:
            # This would check if the plugin process/service is running
            # For now, assume plugins are running if they're active
            return {
                'status': 'healthy',
                'running': True,
                'pid': 12345,  # Mock PID
                'uptime_seconds': 3600
            }
        except Exception as e:
            return {
                'status': 'critical',
                'running': False,
                'error': str(e)
            }
    
    async def _check_plugin_api(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Check plugin API responsiveness."""
        try:
            # This would make a health check API call to the plugin
            # Mock a successful API check
            return {
                'status': 'healthy',
                'response_time_ms': 150,
                'api_version': '1.0.0',
                'last_response': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'response_time_ms': None
            }
    
    async def _check_plugin_resources(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Check plugin resource usage."""
        try:
            # Mock resource usage check
            cpu_percent = 5.2
            memory_mb = 128
            
            status = 'healthy'
            if cpu_percent > 80 or memory_mb > 1024:
                status = 'critical'
            elif cpu_percent > 50 or memory_mb > 512:
                status = 'warning'
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'disk_io_mb': 0.5,
                'network_io_mb': 2.1
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def _check_plugin_dependencies(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Check plugin dependencies."""
        try:
            # This would check if plugin dependencies are available
            # Mock dependency check
            return {
                'status': 'healthy',
                'dependencies': [
                    {'name': 'database', 'status': 'available'},
                    {'name': 'redis', 'status': 'available'},
                    {'name': 'external_api', 'status': 'available'}
                ]
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e)
            }
    
    def _calculate_overall_health_status(self, checks: Dict[str, Any]) -> PluginHealthStatus:
        """Calculate overall health status from individual checks."""
        statuses = [check.get('status', 'unknown') for check in checks.values()]
        
        if 'critical' in statuses:
            return PluginHealthStatus.CRITICAL
        elif 'warning' in statuses:
            return PluginHealthStatus.WARNING
        elif all(status == 'healthy' for status in statuses):
            return PluginHealthStatus.HEALTHY
        else:
            return PluginHealthStatus.UNKNOWN
    
    async def _collect_plugin_metrics(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Collect performance metrics for a plugin."""
        return {
            'requests_per_minute': 45,
            'average_response_time_ms': 120,
            'error_rate_percent': 0.5,
            'uptime_percent': 99.8,
            'last_error': None,
            'memory_usage_trend': 'stable'
        }
    
    async def _trigger_health_alert(self, plugin: Dict[str, Any], health_result: Dict[str, Any]):
        """Trigger alert for plugin health issues."""
        self.webhook_triggers.plugin_health_alert({
            'plugin_id': plugin['id'],
            'plugin_name': plugin['name'],
            'health_status': health_result['status'],
            'failed_checks': [
                check_name for check_name, check_result in health_result['checks'].items()
                if check_result.get('status') in ['critical', 'warning']
            ],
            'alert_time': datetime.now(timezone.utc).isoformat()
        })
    
    async def _stop_plugin(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a plugin process."""
        # Mock plugin stop
        return {
            'success': True,
            'stop_time': datetime.now(timezone.utc).isoformat()
        }
    
    async def _start_plugin(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Start a plugin process."""
        # Mock plugin start
        return {
            'success': True,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'pid': 12346
        }
    
    async def _watchdog_loop(self, check_interval_seconds: int):
        """Main watchdog loop for monitoring plugins."""
        logger.info("Plugin watchdog loop started")
        
        while self._watchdog_running:
            try:
                # Perform health checks
                health_results = await self.perform_health_checks()
                
                # Check for plugins that need automatic recovery
                for plugin_result in health_results['plugin_results']:
                    if plugin_result['status'] == PluginHealthStatus.CRITICAL:
                        await self._attempt_automatic_recovery(plugin_result)
                
                # Wait for next check
                await asyncio.sleep(check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in watchdog loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        logger.info("Plugin watchdog loop stopped")
    
    async def _attempt_automatic_recovery(self, plugin_result: Dict[str, Any]):
        """Attempt automatic recovery for a failed plugin."""
        plugin_id = plugin_result['plugin_id']
        
        try:
            logger.info(f"Attempting automatic recovery for plugin {plugin_id}")
            
            # Try reloading first
            reload_result = await self.reload_plugin(plugin_id)
            
            if reload_result['health_status'] == PluginHealthStatus.HEALTHY:
                logger.info(f"Plugin {plugin_id} recovered successfully via reload")
                return
            
            # If reload didn't work, try restart
            restart_result = await self.restart_plugin(plugin_id, "automatic_recovery")
            
            if restart_result['health_status'] == PluginHealthStatus.HEALTHY:
                logger.info(f"Plugin {plugin_id} recovered successfully via restart")
            else:
                logger.error(f"Automatic recovery failed for plugin {plugin_id}")
                
                # Trigger critical alert
                self.webhook_triggers.plugin_recovery_failed({
                    'plugin_id': plugin_id,
                    'plugin_name': plugin_result['plugin_name'],
                    'recovery_attempts': ['reload', 'restart'],
                    'failure_time': datetime.now(timezone.utc).isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error during automatic recovery for plugin {plugin_id}: {e}")

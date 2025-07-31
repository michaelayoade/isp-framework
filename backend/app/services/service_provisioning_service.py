"""
Service Provisioning Service Layer - ISP Service Management System

Business logic layer for service provisioning management including:
- Service provisioning workflows (automated deployment orchestration)
- Provisioning templates (workflow definition and management)
- Provisioning queue (task scheduling and execution)

Provides high-level provisioning operations with workflow orchestration,
automation, rollback capabilities, and comprehensive progress tracking.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from app.models.services import (
    ProvisioningQueue,
    ProvisioningStatus,
    ProvisioningTemplate,
    ServiceProvisioning,
    ServiceType,
)
from app.models.services.instances import CustomerService
from app.repositories.service_repository_factory import ServiceRepositoryFactory
from app.services.webhook_integration_service import WebhookTriggers

logger = logging.getLogger(__name__)


class ServiceProvisioningService:
    """Service layer for service provisioning operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.provisioning_repo = self.repo_factory.get_provisioning_repo()
        self.template_repo = self.repo_factory.get_provisioning_template_repo()
        self.queue_repo = self.repo_factory.get_provisioning_queue_repo()
        self.webhook_triggers = WebhookTriggers(db)

    async def initiate_provisioning(
        self,
        service_id: int,
        template_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        priority: int = 5,
        scheduled_at: Optional[datetime] = None,
        provisioning_data: Optional[Dict[str, Any]] = None,
    ) -> ServiceProvisioning:
        """Initiate provisioning workflow for a service"""
        logger.info(f"Initiating provisioning for service: {service_id}")

        try:
            # Validate service exists
            service = (
                self.db.query(CustomerService)
                .filter(CustomerService.id == service_id)
                .first()
            )
            if not service:
                raise NotFoundError(f"Customer service {service_id} not found")

            # Get or determine provisioning template
            if template_id:
                template = self.template_repo.get_by_id(template_id)
                if not template or not template.is_active:
                    raise ValidationError("Invalid or inactive provisioning template")
            else:
                template = self.template_repo.get_default_template(service.service_type)
                if not template:
                    raise ValidationError(
                        f"No default provisioning template found for {service.service_type}"
                    )

            # Generate workflow ID
            workflow_id = await self._generate_workflow_id(
                service.service_type, service.customer_id
            )

            # Prepare provisioning data
            provisioning_params = {
                "workflow_id": workflow_id,
                "service_id": service_id,
                "template_id": template.id,
                "status": ProvisioningStatus.PENDING,
                "priority": priority,
                "scheduled_at": scheduled_at,
                "initiated_by_id": admin_id,
                "provisioning_data": provisioning_data or {},
                "created_at": datetime.now(timezone.utc),
            }

            # Create provisioning record
            provisioning = ServiceProvisioning(**provisioning_params)
            provisioning = self.provisioning_repo.create(provisioning)

            # Create provisioning queue tasks
            await self._create_provisioning_tasks(provisioning, template)

            # Start provisioning if not scheduled
            if not scheduled_at or scheduled_at <= datetime.now(timezone.utc):
                await self._start_provisioning(provisioning)

            logger.info(
                f"Provisioning initiated successfully: {provisioning.workflow_id}"
            )
            return provisioning

        except Exception as e:
            logger.error(f"Error initiating provisioning: {str(e)}")
            raise BusinessLogicError(f"Failed to initiate provisioning: {str(e)}")

    async def start_provisioning(self, provisioning_id: int) -> ServiceProvisioning:
        """Start a pending provisioning workflow"""
        logger.info(f"Starting provisioning workflow: {provisioning_id}")

        try:
            provisioning = self.provisioning_repo.get_by_id(provisioning_id)
            if not provisioning:
                raise NotFoundError(
                    f"Provisioning workflow {provisioning_id} not found"
                )

            if provisioning.status != ProvisioningStatus.PENDING:
                raise ValidationError(
                    f"Cannot start provisioning in {provisioning.status} status"
                )

            # Update status to in progress
            provisioning = self.provisioning_repo.update(
                provisioning,
                {
                    "status": ProvisioningStatus.IN_PROGRESS,
                    "started_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Execute provisioning workflow
            await self._execute_provisioning_workflow(provisioning)

            logger.info(f"Provisioning workflow started: {provisioning.workflow_id}")
            return provisioning

        except Exception as e:
            logger.error(f"Error starting provisioning: {str(e)}")
            raise

    async def pause_provisioning(
        self, provisioning_id: int, admin_id: int
    ) -> ServiceProvisioning:
        """Pause a running provisioning workflow"""
        logger.info(f"Pausing provisioning workflow: {provisioning_id}")

        try:
            provisioning = self.provisioning_repo.get_by_id(provisioning_id)
            if not provisioning:
                raise NotFoundError(
                    f"Provisioning workflow {provisioning_id} not found"
                )

            if provisioning.status != ProvisioningStatus.IN_PROGRESS:
                raise ValidationError(
                    "Can only pause in-progress provisioning workflows"
                )

            # Update status to paused
            provisioning = self.provisioning_repo.update(
                provisioning,
                {
                    "status": ProvisioningStatus.PAUSED,
                    "paused_at": datetime.now(timezone.utc),
                    "paused_by_id": admin_id,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Pause active queue tasks
            await self._pause_active_tasks(provisioning)

            logger.info(f"Provisioning workflow paused: {provisioning.workflow_id}")
            return provisioning

        except Exception as e:
            logger.error(f"Error pausing provisioning: {str(e)}")
            raise

    async def resume_provisioning(
        self, provisioning_id: int, admin_id: int
    ) -> ServiceProvisioning:
        """Resume a paused provisioning workflow"""
        logger.info(f"Resuming provisioning workflow: {provisioning_id}")

        try:
            provisioning = self.provisioning_repo.get_by_id(provisioning_id)
            if not provisioning:
                raise NotFoundError(
                    f"Provisioning workflow {provisioning_id} not found"
                )

            if provisioning.status != ProvisioningStatus.PAUSED:
                raise ValidationError("Can only resume paused provisioning workflows")

            # Update status to in progress
            provisioning = self.provisioning_repo.update(
                provisioning,
                {
                    "status": ProvisioningStatus.IN_PROGRESS,
                    "resumed_at": datetime.now(timezone.utc),
                    "resumed_by_id": admin_id,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Resume provisioning execution
            await self._resume_provisioning_execution(provisioning)

            logger.info(f"Provisioning workflow resumed: {provisioning.workflow_id}")
            return provisioning

        except Exception as e:
            logger.error(f"Error resuming provisioning: {str(e)}")
            raise

    async def cancel_provisioning(
        self, provisioning_id: int, admin_id: int, reason: Optional[str] = None
    ) -> ServiceProvisioning:
        """Cancel a provisioning workflow"""
        logger.info(f"Cancelling provisioning workflow: {provisioning_id}")

        try:
            provisioning = self.provisioning_repo.get_by_id(provisioning_id)
            if not provisioning:
                raise NotFoundError(
                    f"Provisioning workflow {provisioning_id} not found"
                )

            if provisioning.status in [
                ProvisioningStatus.COMPLETED,
                ProvisioningStatus.CANCELLED,
            ]:
                raise ValidationError(
                    f"Cannot cancel provisioning in {provisioning.status} status"
                )

            # Perform rollback if necessary
            if provisioning.status == ProvisioningStatus.IN_PROGRESS:
                await self._perform_rollback(provisioning)

            # Update status to cancelled
            provisioning = self.provisioning_repo.update(
                provisioning,
                {
                    "status": ProvisioningStatus.CANCELLED,
                    "cancelled_at": datetime.now(timezone.utc),
                    "cancelled_by_id": admin_id,
                    "cancellation_reason": reason,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Cancel all pending queue tasks
            await self._cancel_pending_tasks(provisioning)

            logger.info(f"Provisioning workflow cancelled: {provisioning.workflow_id}")
            return provisioning

        except Exception as e:
            logger.error(f"Error cancelling provisioning: {str(e)}")
            raise

    async def retry_failed_provisioning(
        self, provisioning_id: int, admin_id: int
    ) -> ServiceProvisioning:
        """Retry a failed provisioning workflow"""
        logger.info(f"Retrying failed provisioning workflow: {provisioning_id}")

        try:
            provisioning = self.provisioning_repo.get_by_id(provisioning_id)
            if not provisioning:
                raise NotFoundError(
                    f"Provisioning workflow {provisioning_id} not found"
                )

            if provisioning.status != ProvisioningStatus.FAILED:
                raise ValidationError("Can only retry failed provisioning workflows")

            if not provisioning.can_retry:
                raise ValidationError("Provisioning workflow is not eligible for retry")

            # Reset provisioning status
            provisioning = self.provisioning_repo.update(
                provisioning,
                {
                    "status": ProvisioningStatus.PENDING,
                    "retry_count": (provisioning.retry_count or 0) + 1,
                    "retried_by_id": admin_id,
                    "retried_at": datetime.now(timezone.utc),
                    "error_message": None,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Reset failed queue tasks
            await self._reset_failed_tasks(provisioning)

            # Start provisioning
            await self._start_provisioning(provisioning)

            logger.info(
                f"Provisioning workflow retry initiated: {provisioning.workflow_id}"
            )
            return provisioning

        except Exception as e:
            logger.error(f"Error retrying provisioning: {str(e)}")
            raise

    async def get_provisioning_status(self, provisioning_id: int) -> Dict[str, Any]:
        """Get detailed provisioning status and progress"""
        logger.info(f"Getting provisioning status: {provisioning_id}")

        try:
            provisioning = self.provisioning_repo.get_by_id(provisioning_id)
            if not provisioning:
                raise NotFoundError(
                    f"Provisioning workflow {provisioning_id} not found"
                )

            # Get queue tasks
            tasks = self.queue_repo.get_tasks_by_provisioning(provisioning_id)

            # Calculate progress
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "completed"])
            failed_tasks = len([t for t in tasks if t.status == "failed"])

            progress_percentage = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )

            status_info = {
                "provisioning_id": provisioning.id,
                "workflow_id": provisioning.workflow_id,
                "status": provisioning.status,
                "progress_percentage": progress_percentage,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "pending_tasks": len([t for t in tasks if t.status == "pending"]),
                "current_step": self._get_current_step(tasks),
                "estimated_completion": self._calculate_estimated_completion(
                    provisioning, tasks
                ),
                "created_at": provisioning.created_at,
                "started_at": provisioning.started_at,
                "updated_at": provisioning.updated_at,
                "error_message": provisioning.error_message,
            }

            logger.info(
                f"Provisioning status retrieved: {progress_percentage}% complete"
            )
            return status_info

        except Exception as e:
            logger.error(f"Error getting provisioning status: {str(e)}")
            raise

    async def get_provisioning_queue(
        self,
        status_filter: Optional[str] = None,
        priority_min: Optional[int] = None,
        limit: int = 50,
    ) -> List[ProvisioningQueue]:
        """Get provisioning queue with filtering"""
        logger.info("Getting provisioning queue")

        try:
            if status_filter == "pending":
                tasks = self.queue_repo.get_pending_tasks(priority_min=priority_min)
            else:
                # Get all tasks with filtering
                tasks = self.queue_repo.get_all(limit=limit)
                if status_filter:
                    tasks = [t for t in tasks if t.status == status_filter]
                if priority_min:
                    tasks = [t for t in tasks if t.priority >= priority_min]

            logger.info(f"Retrieved {len(tasks)} tasks from provisioning queue")
            return tasks

        except Exception as e:
            logger.error(f"Error getting provisioning queue: {str(e)}")
            raise BusinessLogicError(f"Failed to get provisioning queue: {str(e)}")

    async def process_provisioning_queue(
        self, max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Process pending tasks in the provisioning queue"""
        logger.info(f"Processing provisioning queue (max concurrent: {max_concurrent})")

        try:
            # Get pending tasks
            pending_tasks = self.queue_repo.get_pending_tasks()

            if not pending_tasks:
                return {"processed": 0, "message": "No pending tasks in queue"}

            # Process tasks concurrently
            processed_count = 0
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_task(task):
                async with semaphore:
                    try:
                        await self._execute_queue_task(task)
                        return True
                    except Exception as e:
                        logger.error(f"Error processing task {task.id}: {str(e)}")
                        return False

            # Execute tasks
            results = await asyncio.gather(
                *[process_task(task) for task in pending_tasks[:max_concurrent]]
            )
            processed_count = sum(results)

            logger.info(f"Processed {processed_count} tasks from provisioning queue")
            return {
                "processed": processed_count,
                "total_pending": len(pending_tasks),
                "success_rate": processed_count / len(results) * 100 if results else 0,
            }

        except Exception as e:
            logger.error(f"Error processing provisioning queue: {str(e)}")
            raise BusinessLogicError(f"Failed to process provisioning queue: {str(e)}")

    # Private helper methods
    async def _generate_workflow_id(
        self, service_type: ServiceType, customer_id: int
    ) -> str:
        """Generate unique workflow identifier"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        return f"PROV-{service_type.value.upper()}-{customer_id:06d}-{timestamp}"

    async def _create_provisioning_tasks(
        self, provisioning: ServiceProvisioning, template: ProvisioningTemplate
    ):
        """Create provisioning queue tasks based on template"""
        logger.info(
            f"Creating provisioning tasks for workflow: {provisioning.workflow_id}"
        )

        try:
            # Parse template steps
            template_steps = json.loads(template.workflow_steps or "[]")

            for i, step in enumerate(template_steps):
                task_data = {
                    "provisioning_id": provisioning.id,
                    "task_name": step.get("name", f"Step {i+1}"),
                    "task_type": step.get("type", "manual"),
                    "step_order": i + 1,
                    "priority": provisioning.priority,
                    "task_data": step.get("data", {}),
                    "dependencies": step.get("dependencies", []),
                    "required_resources": step.get("required_resources", []),
                    "estimated_duration": step.get(
                        "estimated_duration", 300
                    ),  # 5 minutes default
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc),
                }

                task = ProvisioningQueue(**task_data)
                self.queue_repo.create(task)

            logger.info(f"Created {len(template_steps)} provisioning tasks")

        except Exception as e:
            logger.error(f"Error creating provisioning tasks: {str(e)}")
            raise

    async def _start_provisioning(self, provisioning: ServiceProvisioning):
        """Start provisioning workflow execution"""
        logger.info(f"Starting provisioning workflow: {provisioning.workflow_id}")

        # Update status if still pending
        if provisioning.status == ProvisioningStatus.PENDING:
            provisioning = self.provisioning_repo.update(
                provisioning,
                {
                    "status": ProvisioningStatus.IN_PROGRESS,
                    "started_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

        # Execute workflow
        await self._execute_provisioning_workflow(provisioning)

    async def _execute_provisioning_workflow(self, provisioning: ServiceProvisioning):
        """Execute provisioning workflow"""
        logger.info(f"Executing provisioning workflow: {provisioning.workflow_id}")

        try:
            # Get pending tasks for this provisioning
            tasks = self.queue_repo.get_tasks_by_provisioning(provisioning.id)
            pending_tasks = [t for t in tasks if t.status == "pending"]

            # Execute tasks that have no dependencies or whose dependencies are met
            for task in pending_tasks:
                if await self._can_execute_task(task, tasks):
                    await self._execute_queue_task(task)

        except Exception as e:
            logger.error(f"Error executing provisioning workflow: {str(e)}")
            # Mark provisioning as failed
            self.provisioning_repo.update(
                provisioning,
                {
                    "status": ProvisioningStatus.FAILED,
                    "error_message": str(e),
                    "failed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            raise

    async def _can_execute_task(
        self, task: ProvisioningQueue, all_tasks: List[ProvisioningQueue]
    ) -> bool:
        """Check if task dependencies are satisfied"""
        if not task.dependencies:
            return True

        completed_tasks = [t.task_name for t in all_tasks if t.status == "completed"]
        return all(dep in completed_tasks for dep in task.dependencies)

    async def _execute_queue_task(self, task: ProvisioningQueue):
        """Execute a single queue task"""
        logger.info(f"Executing provisioning task: {task.task_name}")

        try:
            # Update task status to running
            task = self.queue_repo.update(
                task,
                {
                    "status": "running",
                    "started_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Execute task based on type
            if task.task_type == "router_config":
                await self._execute_router_config_task(task)
            elif task.task_type == "radius_user":
                await self._execute_radius_user_task(task)
            elif task.task_type == "ip_assignment":
                await self._execute_ip_assignment_task(task)
            elif task.task_type == "billing_activation":
                await self._execute_billing_activation_task(task)
            else:
                # Default manual task handling
                await self._execute_manual_task(task)

            # Mark task as completed
            task = self.queue_repo.update(
                task,
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Check if all tasks for provisioning are completed
            await self._check_provisioning_completion(task.provisioning_id)

            logger.info(f"Provisioning task completed: {task.task_name}")

        except Exception as e:
            logger.error(f"Error executing task {task.task_name}: {str(e)}")

            # Mark task as failed
            self.queue_repo.update(
                task,
                {
                    "status": "failed",
                    "error_message": str(e),
                    "failed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Mark provisioning as failed
            provisioning = self.provisioning_repo.get_by_id(task.provisioning_id)
            if provisioning:
                self.provisioning_repo.update(
                    provisioning,
                    {
                        "status": ProvisioningStatus.FAILED,
                        "error_message": f"Task '{task.task_name}' failed: {str(e)}",
                        "failed_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )

            raise

    async def _execute_router_config_task(self, task: ProvisioningQueue):
        """Execute router configuration task"""
        logger.info(f"Executing router config task: {task.task_name}")
        # Implementation would configure router settings
        await asyncio.sleep(1)  # Simulate task execution

    async def _execute_radius_user_task(self, task: ProvisioningQueue):
        """Execute RADIUS user creation task"""
        logger.info(f"Executing RADIUS user task: {task.task_name}")
        # Implementation would create RADIUS user
        await asyncio.sleep(1)  # Simulate task execution

    async def _execute_ip_assignment_task(self, task: ProvisioningQueue):
        """Execute IP assignment task"""
        logger.info(f"Executing IP assignment task: {task.task_name}")
        # Implementation would assign IP address
        await asyncio.sleep(1)  # Simulate task execution

    async def _execute_billing_activation_task(self, task: ProvisioningQueue):
        """Execute billing activation task"""
        logger.info(f"Executing billing activation task: {task.task_name}")
        # Implementation would activate billing
        await asyncio.sleep(1)  # Simulate task execution

    async def _execute_manual_task(self, task: ProvisioningQueue):
        """Execute manual task (requires human intervention)"""
        logger.info(f"Manual task requires attention: {task.task_name}")
        # Manual tasks would be handled by operators
        # For now, we'll mark them as completed after a delay
        await asyncio.sleep(2)  # Simulate manual intervention

    async def _check_provisioning_completion(self, provisioning_id: int):
        """Check if all tasks for a provisioning are completed"""
        tasks = self.queue_repo.get_tasks_by_provisioning(provisioning_id)

        if all(task.status in ["completed", "skipped"] for task in tasks):
            # All tasks completed - mark provisioning as completed
            provisioning = self.provisioning_repo.get_by_id(provisioning_id)
            if provisioning and provisioning.status == ProvisioningStatus.IN_PROGRESS:
                self.provisioning_repo.update(
                    provisioning,
                    {
                        "status": ProvisioningStatus.COMPLETED,
                        "completed_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )

                logger.info(
                    f"Provisioning workflow completed: {provisioning.workflow_id}"
                )

    async def _perform_rollback(self, provisioning: ServiceProvisioning):
        """Perform rollback for cancelled/failed provisioning"""
        logger.info(f"Performing rollback for provisioning: {provisioning.workflow_id}")
        # Implementation would reverse completed provisioning steps

    async def _pause_active_tasks(self, provisioning: ServiceProvisioning):
        """Pause active tasks for a provisioning workflow"""
        logger.info(
            f"Pausing active tasks for provisioning: {provisioning.workflow_id}"
        )
        # Implementation would pause running tasks

    async def _resume_provisioning_execution(self, provisioning: ServiceProvisioning):
        """Resume provisioning execution"""
        logger.info(f"Resuming provisioning execution: {provisioning.workflow_id}")
        await self._execute_provisioning_workflow(provisioning)

    async def _cancel_pending_tasks(self, provisioning: ServiceProvisioning):
        """Cancel all pending tasks for a provisioning workflow"""
        tasks = self.queue_repo.get_tasks_by_provisioning(provisioning.id)
        pending_tasks = [t for t in tasks if t.status == "pending"]

        for task in pending_tasks:
            self.queue_repo.update(
                task,
                {
                    "status": "cancelled",
                    "cancelled_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )

    async def _reset_failed_tasks(self, provisioning: ServiceProvisioning):
        """Reset failed tasks for retry"""
        tasks = self.queue_repo.get_tasks_by_provisioning(provisioning.id)
        failed_tasks = [t for t in tasks if t.status == "failed"]

        for task in failed_tasks:
            self.queue_repo.update(
                task,
                {
                    "status": "pending",
                    "error_message": None,
                    "failed_at": None,
                    "started_at": None,
                    "completed_at": None,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

    def _get_current_step(self, tasks: List[ProvisioningQueue]) -> Optional[str]:
        """Get current step name from tasks"""
        running_tasks = [t for t in tasks if t.status == "running"]
        if running_tasks:
            return running_tasks[0].task_name

        pending_tasks = [t for t in tasks if t.status == "pending"]
        if pending_tasks:
            return f"Next: {pending_tasks[0].task_name}"

        return None

    def _calculate_estimated_completion(
        self, provisioning: ServiceProvisioning, tasks: List[ProvisioningQueue]
    ) -> Optional[datetime]:
        """Calculate estimated completion time"""
        pending_tasks = [t for t in tasks if t.status in ["pending", "running"]]
        if not pending_tasks:
            return None

        total_duration = sum(task.estimated_duration or 300 for task in pending_tasks)
        return datetime.now(timezone.utc) + timedelta(seconds=total_duration)


class ProvisioningTemplateService:
    """Service layer for provisioning template operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo_factory = ServiceRepositoryFactory(db)
        self.template_repo = self.repo_factory.get_provisioning_template_repo()

    async def create_provisioning_template(
        self, template_data: Dict[str, Any], admin_id: int
    ) -> ProvisioningTemplate:
        """Create a new provisioning template"""
        logger.info(f"Creating provisioning template: {template_data.get('name')}")

        try:
            # Validate template data
            self._validate_template_data(template_data)

            # Prepare template data
            template_data.update(
                {"created_by_id": admin_id, "created_at": datetime.now(timezone.utc)}
            )

            # Create template
            template = ProvisioningTemplate(**template_data)
            template = self.template_repo.create(template)

            logger.info(f"Provisioning template created: {template.id}")
            return template

        except Exception as e:
            logger.error(f"Error creating provisioning template: {str(e)}")
            raise

    def _validate_template_data(self, template_data: Dict[str, Any]):
        """Validate provisioning template data"""
        required_fields = ["name", "service_type", "workflow_steps"]

        for field in required_fields:
            if field not in template_data or not template_data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")

        # Validate workflow steps JSON
        try:
            if isinstance(template_data["workflow_steps"], str):
                json.loads(template_data["workflow_steps"])
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format for workflow_steps")


# Service factory for provisioning services
class ServiceProvisioningServiceFactory:
    """Factory for creating service provisioning services"""

    @staticmethod
    def create_provisioning_service(db: Session) -> ServiceProvisioningService:
        return ServiceProvisioningService(db)

    @staticmethod
    def create_template_service(db: Session) -> ProvisioningTemplateService:
        return ProvisioningTemplateService(db)

    @staticmethod
    def create_all_services(db: Session) -> Dict[str, Any]:
        """Create all service provisioning services"""
        return {
            "provisioning": ServiceProvisioningService(db),
            "template": ProvisioningTemplateService(db),
        }

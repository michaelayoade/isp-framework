"""
Communications Rule Engine Service

Expanded service layer for communications rule management including:
- Event-driven communication triggers for all system events
- Rule-based notification routing and templating
- Multi-channel communication (email, SMS, webhook, push)
- Dynamic rule evaluation and conditional logic
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers

logger = logging.getLogger(__name__)


class CommunicationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH_NOTIFICATION = "push"
    SLACK = "slack"
    TEAMS = "teams"


class EventType(str, Enum):
    # Customer events
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    CUSTOMER_SUSPENDED = "customer_suspended"
    CUSTOMER_REACTIVATED = "customer_reactivated"

    # Service events
    SERVICE_CREATED = "service_created"
    SERVICE_ACTIVATED = "service_activated"
    SERVICE_SUSPENDED = "service_suspended"
    SERVICE_TERMINATED = "service_terminated"
    SERVICE_UPGRADED = "service_upgraded"
    SERVICE_DOWNGRADED = "service_downgraded"

    # Billing events
    INVOICE_GENERATED = "invoice_generated"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_OVERDUE = "payment_overdue"
    DUNNING_NOTICE = "dunning_notice"

    # Technical events
    SERVICE_OUTAGE = "service_outage"
    SERVICE_RESTORED = "service_restored"
    MAINTENANCE_SCHEDULED = "maintenance_scheduled"
    MAINTENANCE_COMPLETED = "maintenance_completed"

    # Support events
    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_ESCALATED = "ticket_escalated"
    TICKET_RESOLVED = "ticket_resolved"
    SLA_BREACHED = "sla_breached"

    # System events
    QUOTA_EXCEEDED = "quota_exceeded"
    PLUGIN_FAILED = "plugin_failed"
    BACKUP_COMPLETED = "backup_completed"
    SECURITY_ALERT = "security_alert"


class RuleConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"
    REGEX_MATCH = "regex_match"


@dataclass
class RuleCondition:
    field: str
    operator: RuleConditionOperator
    value: Union[str, int, float, List[Any]]


@dataclass
class CommunicationAction:
    channel: CommunicationChannel
    template_id: str
    recipients: List[str]
    delay_minutes: int = 0
    priority: str = "normal"


class CommunicationsRuleEngineService:
    """Service layer for communications rule engine management."""

    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
        self._rule_cache = {}
        self._template_cache = {}

    def process_event(
        self, event_type: EventType, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event through the communications rule engine."""
        try:
            # Get applicable rules for this event type
            applicable_rules = self._get_rules_for_event(event_type)

            triggered_rules = []
            communication_actions = []

            for rule in applicable_rules:
                if self._evaluate_rule_conditions(rule, event_data):
                    triggered_rules.append(rule["id"])

                    # Generate communication actions for this rule
                    actions = self._generate_communication_actions(rule, event_data)
                    communication_actions.extend(actions)

            # Execute communication actions
            execution_results = []
            for action in communication_actions:
                try:
                    result = self._execute_communication_action(action, event_data)
                    execution_results.append(result)
                except Exception as e:
                    logger.error(f"Error executing communication action: {e}")
                    execution_results.append(
                        {
                            "action_id": action.get("id"),
                            "success": False,
                            "error": str(e),
                        }
                    )

            logger.info(
                f"Processed event {event_type}: {len(triggered_rules)} rules triggered, {len(communication_actions)} actions executed"
            )

            return {
                "event_type": event_type,
                "event_data": event_data,
                "triggered_rules": triggered_rules,
                "communication_actions_count": len(communication_actions),
                "successful_actions": len(
                    [r for r in execution_results if r.get("success")]
                ),
                "failed_actions": len(
                    [r for r in execution_results if not r.get("success")]
                ),
                "execution_results": execution_results,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}")
            raise

    def create_communication_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new communication rule."""
        try:
            # Validate rule data
            self._validate_rule_data(rule_data)

            # Create rule record
            rule = self._create_rule_record(rule_data)

            # Clear rule cache
            self._rule_cache.clear()

            logger.info(f"Created communication rule {rule['id']}")

            return rule

        except Exception as e:
            logger.error(f"Error creating communication rule: {e}")
            raise

    def update_communication_rule(
        self, rule_id: int, rule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing communication rule."""
        try:
            # Get existing rule
            existing_rule = self._get_rule_by_id(rule_id)
            if not existing_rule:
                raise NotFoundError(f"Communication rule {rule_id} not found")

            # Validate rule data
            self._validate_rule_data(rule_data)

            # Update rule record
            updated_rule = self._update_rule_record(rule_id, rule_data)

            # Clear rule cache
            self._rule_cache.clear()

            logger.info(f"Updated communication rule {rule_id}")

            return updated_rule

        except Exception as e:
            logger.error(f"Error updating communication rule {rule_id}: {e}")
            raise

    def delete_communication_rule(self, rule_id: int) -> Dict[str, Any]:
        """Delete a communication rule."""
        try:
            # Get existing rule
            existing_rule = self._get_rule_by_id(rule_id)
            if not existing_rule:
                raise NotFoundError(f"Communication rule {rule_id} not found")

            # Delete rule record
            self._delete_rule_record(rule_id)

            # Clear rule cache
            self._rule_cache.clear()

            logger.info(f"Deleted communication rule {rule_id}")

            return {
                "rule_id": rule_id,
                "deleted": True,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error deleting communication rule {rule_id}: {e}")
            raise

    def list_communication_rules(
        self, event_type: Optional[EventType] = None, active_only: bool = True
    ) -> Dict[str, Any]:
        """List communication rules with optional filtering."""
        try:
            rules = self._get_rules_list(event_type, active_only)

            return {
                "rules": rules,
                "total_count": len(rules),
                "filters": {"event_type": event_type, "active_only": active_only},
            }

        except Exception as e:
            logger.error(f"Error listing communication rules: {e}")
            raise

    def test_rule_conditions(
        self, rule_id: int, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test rule conditions against sample data."""
        try:
            # Get rule
            rule = self._get_rule_by_id(rule_id)
            if not rule:
                raise NotFoundError(f"Communication rule {rule_id} not found")

            # Evaluate conditions
            evaluation_result = self._evaluate_rule_conditions(rule, test_data)

            # Get detailed condition results
            condition_results = []
            for condition in rule.get("conditions", []):
                condition_result = self._evaluate_single_condition(condition, test_data)
                condition_results.append(
                    {
                        "condition": condition,
                        "result": condition_result,
                        "explanation": self._explain_condition_result(
                            condition, test_data, condition_result
                        ),
                    }
                )

            return {
                "rule_id": rule_id,
                "rule_name": rule["name"],
                "overall_result": evaluation_result,
                "condition_results": condition_results,
                "test_data": test_data,
                "tested_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error testing rule conditions: {e}")
            raise

    def get_communication_templates(
        self, channel: Optional[CommunicationChannel] = None
    ) -> Dict[str, Any]:
        """Get available communication templates."""
        try:
            templates = self._get_templates_list(channel)

            return {
                "templates": templates,
                "total_count": len(templates),
                "channel_filter": channel,
            }

        except Exception as e:
            logger.error(f"Error retrieving communication templates: {e}")
            raise

    def create_communication_template(
        self, template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new communication template."""
        try:
            # Validate template data
            self._validate_template_data(template_data)

            # Create template record
            template = self._create_template_record(template_data)

            # Clear template cache
            self._template_cache.clear()

            logger.info(f"Created communication template {template['id']}")

            return template

        except Exception as e:
            logger.error(f"Error creating communication template: {e}")
            raise

    def _get_rules_for_event(self, event_type: EventType) -> List[Dict[str, Any]]:
        """Get all active rules that apply to a specific event type."""
        # Check cache first
        cache_key = f"rules_{event_type}"
        if cache_key in self._rule_cache:
            return self._rule_cache[cache_key]

        # Placeholder - implement when rule repository is available
        # This would query the communication_rules table
        rules = [
            {
                "id": 1,
                "name": "Customer Welcome Email",
                "event_type": EventType.CUSTOMER_CREATED,
                "conditions": [
                    {
                        "field": "customer.status",
                        "operator": RuleConditionOperator.EQUALS,
                        "value": "active",
                    }
                ],
                "actions": [
                    {
                        "channel": CommunicationChannel.EMAIL,
                        "template_id": "customer_welcome",
                        "recipients": ["customer.email"],
                        "delay_minutes": 0,
                        "priority": "normal",
                    }
                ],
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Service Activation Notification",
                "event_type": EventType.SERVICE_ACTIVATED,
                "conditions": [],  # No conditions - always trigger
                "actions": [
                    {
                        "channel": CommunicationChannel.EMAIL,
                        "template_id": "service_activated",
                        "recipients": ["customer.email"],
                        "delay_minutes": 5,
                        "priority": "normal",
                    },
                    {
                        "channel": CommunicationChannel.SMS,
                        "template_id": "service_activated_sms",
                        "recipients": ["customer.phone"],
                        "delay_minutes": 0,
                        "priority": "high",
                    },
                ],
                "is_active": True,
            },
        ]

        # Filter by event type
        applicable_rules = [
            rule
            for rule in rules
            if rule["event_type"] == event_type and rule["is_active"]
        ]

        # Cache the result
        self._rule_cache[cache_key] = applicable_rules

        return applicable_rules

    def _evaluate_rule_conditions(
        self, rule: Dict[str, Any], event_data: Dict[str, Any]
    ) -> bool:
        """Evaluate all conditions for a rule against event data."""
        conditions = rule.get("conditions", [])

        # If no conditions, rule always applies
        if not conditions:
            return True

        # Evaluate all conditions (AND logic)
        for condition in conditions:
            if not self._evaluate_single_condition(condition, event_data):
                return False

        return True

    def _evaluate_single_condition(
        self, condition: Dict[str, Any], event_data: Dict[str, Any]
    ) -> bool:
        """Evaluate a single condition against event data."""
        field = condition["field"]
        operator = RuleConditionOperator(condition["operator"])
        expected_value = condition["value"]

        # Get actual value from event data using dot notation
        actual_value = self._get_nested_value(event_data, field)

        # Evaluate based on operator
        if operator == RuleConditionOperator.EQUALS:
            return actual_value == expected_value
        elif operator == RuleConditionOperator.NOT_EQUALS:
            return actual_value != expected_value
        elif operator == RuleConditionOperator.CONTAINS:
            return str(expected_value) in str(actual_value) if actual_value else False
        elif operator == RuleConditionOperator.NOT_CONTAINS:
            return (
                str(expected_value) not in str(actual_value) if actual_value else True
            )
        elif operator == RuleConditionOperator.GREATER_THAN:
            return (
                float(actual_value) > float(expected_value)
                if actual_value is not None
                else False
            )
        elif operator == RuleConditionOperator.LESS_THAN:
            return (
                float(actual_value) < float(expected_value)
                if actual_value is not None
                else False
            )
        elif operator == RuleConditionOperator.IN:
            return (
                actual_value in expected_value
                if isinstance(expected_value, list)
                else False
            )
        elif operator == RuleConditionOperator.NOT_IN:
            return (
                actual_value not in expected_value
                if isinstance(expected_value, list)
                else True
            )
        elif operator == RuleConditionOperator.REGEX_MATCH:
            return (
                bool(re.match(str(expected_value), str(actual_value)))
                if actual_value
                else False
            )
        else:
            return False

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = field_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _generate_communication_actions(
        self, rule: Dict[str, Any], event_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate communication actions from a rule."""
        actions = []

        for action_config in rule.get("actions", []):
            # Resolve recipients from event data
            recipients = self._resolve_recipients(
                action_config["recipients"], event_data
            )

            action = {
                "id": f"{rule['id']}_{action_config['channel']}_{len(actions)}",
                "rule_id": rule["id"],
                "channel": action_config["channel"],
                "template_id": action_config["template_id"],
                "recipients": recipients,
                "delay_minutes": action_config.get("delay_minutes", 0),
                "priority": action_config.get("priority", "normal"),
                "event_data": event_data,
            }

            actions.append(action)

        return actions

    def _resolve_recipients(
        self, recipient_patterns: List[str], event_data: Dict[str, Any]
    ) -> List[str]:
        """Resolve recipient patterns to actual addresses."""
        recipients = []

        for pattern in recipient_patterns:
            if (
                pattern.startswith("customer.")
                or pattern.startswith("reseller.")
                or pattern.startswith("admin.")
            ):
                # Dynamic recipient from event data
                recipient = self._get_nested_value(event_data, pattern)
                if recipient:
                    recipients.append(recipient)
            else:
                # Static recipient
                recipients.append(pattern)

        return recipients

    def _execute_communication_action(
        self, action: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a communication action."""
        try:
            channel = CommunicationChannel(action["channel"])
            template_id = action["template_id"]
            recipients = action["recipients"]

            # Get template
            template = self._get_template(template_id, channel)
            if not template:
                raise NotFoundError(
                    f"Template {template_id} not found for channel {channel}"
                )

            # Render template with event data
            rendered_content = self._render_template(template, event_data)

            # Send communication based on channel
            if channel == CommunicationChannel.EMAIL:
                result = self._send_email(recipients, rendered_content)
            elif channel == CommunicationChannel.SMS:
                result = self._send_sms(recipients, rendered_content)
            elif channel == CommunicationChannel.WEBHOOK:
                result = self._send_webhook(recipients, rendered_content, event_data)
            elif channel == CommunicationChannel.PUSH_NOTIFICATION:
                result = self._send_push_notification(recipients, rendered_content)
            else:
                raise ValidationError(f"Unsupported communication channel: {channel}")

            return {
                "action_id": action["id"],
                "channel": channel,
                "recipients": recipients,
                "success": result.get("success", False),
                "message_id": result.get("message_id"),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            return {
                "action_id": action["id"],
                "success": False,
                "error": str(e),
                "failed_at": datetime.now(timezone.utc).isoformat(),
            }

    def _get_template(
        self, template_id: str, channel: CommunicationChannel
    ) -> Optional[Dict[str, Any]]:
        """Get communication template by ID and channel."""
        # Check cache first
        cache_key = f"template_{template_id}_{channel}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Placeholder - implement when template repository is available
        templates = {
            "customer_welcome": {
                "id": "customer_welcome",
                "channel": CommunicationChannel.EMAIL,
                "subject": "Welcome to {{company_name}}!",
                "body": "Dear {{customer.name}}, welcome to our service!",
                "variables": ["company_name", "customer.name", "customer.email"],
            },
            "service_activated": {
                "id": "service_activated",
                "channel": CommunicationChannel.EMAIL,
                "subject": "Service Activated - {{service.name}}",
                "body": "Your {{service.name}} service has been activated.",
                "variables": ["service.name", "service.type", "customer.name"],
            },
        }

        template = templates.get(template_id)
        if template and template["channel"] == channel:
            self._template_cache[cache_key] = template
            return template

        return None

    def _render_template(
        self, template: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Render template with event data."""
        rendered = {
            "subject": template.get("subject", ""),
            "body": template.get("body", ""),
            "template_id": template["id"],
        }

        # Simple template variable replacement
        for key, content in rendered.items():
            if isinstance(content, str):
                # Replace variables like {{variable.path}}
                import re

                variables = re.findall(r"\{\{([^}]+)\}\}", content)
                for var in variables:
                    value = self._get_nested_value(event_data, var.strip())
                    if value is not None:
                        content = content.replace(f"{{{{{var}}}}}", str(value))
                rendered[key] = content

        return rendered

    def _send_email(
        self, recipients: List[str], content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email communication."""
        # Mock email sending
        return {
            "success": True,
            "message_id": f"email_{datetime.now().timestamp()}",
            "recipients_sent": len(recipients),
        }

    def _send_sms(
        self, recipients: List[str], content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send SMS communication."""
        # Mock SMS sending
        return {
            "success": True,
            "message_id": f"sms_{datetime.now().timestamp()}",
            "recipients_sent": len(recipients),
        }

    def _send_webhook(
        self, recipients: List[str], content: Dict[str, Any], event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send webhook communication."""
        # Mock webhook sending
        return {
            "success": True,
            "message_id": f"webhook_{datetime.now().timestamp()}",
            "endpoints_called": len(recipients),
        }

    def _send_push_notification(
        self, recipients: List[str], content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send push notification."""
        # Mock push notification sending
        return {
            "success": True,
            "message_id": f"push_{datetime.now().timestamp()}",
            "devices_sent": len(recipients),
        }

    def _validate_rule_data(self, rule_data: Dict[str, Any]):
        """Validate communication rule data."""
        required_fields = ["name", "event_type", "actions"]
        for field in required_fields:
            if field not in rule_data:
                raise ValidationError(f"Missing required field: {field}")

    def _validate_template_data(self, template_data: Dict[str, Any]):
        """Validate communication template data."""
        required_fields = ["id", "channel", "body"]
        for field in required_fields:
            if field not in template_data:
                raise ValidationError(f"Missing required field: {field}")

    def _create_rule_record(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create communication rule record in database."""
        # Placeholder - implement when rule repository is available
        return {
            "id": 1,
            "name": rule_data["name"],
            "event_type": rule_data["event_type"],
            "conditions": rule_data.get("conditions", []),
            "actions": rule_data["actions"],
            "is_active": rule_data.get("is_active", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _update_rule_record(
        self, rule_id: int, rule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update communication rule record in database."""
        # Placeholder - implement when rule repository is available
        return {
            "id": rule_id,
            "name": rule_data["name"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _delete_rule_record(self, rule_id: int):
        """Delete communication rule record from database."""
        # Placeholder - implement when rule repository is available
        pass

    def _get_rule_by_id(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """Get communication rule by ID."""
        # Placeholder - implement when rule repository is available
        return {
            "id": rule_id,
            "name": "Test Rule",
            "event_type": EventType.CUSTOMER_CREATED,
            "conditions": [],
            "actions": [],
            "is_active": True,
        }

    def _get_rules_list(
        self, event_type: Optional[EventType], active_only: bool
    ) -> List[Dict[str, Any]]:
        """Get list of communication rules."""
        # Placeholder - implement when rule repository is available
        return []

    def _get_templates_list(
        self, channel: Optional[CommunicationChannel]
    ) -> List[Dict[str, Any]]:
        """Get list of communication templates."""
        # Placeholder - implement when template repository is available
        return []

    def _create_template_record(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create communication template record in database."""
        # Placeholder - implement when template repository is available
        return {
            "id": template_data["id"],
            "channel": template_data["channel"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _explain_condition_result(
        self, condition: Dict[str, Any], test_data: Dict[str, Any], result: bool
    ) -> str:
        """Generate explanation for condition evaluation result."""
        field = condition["field"]
        operator = condition["operator"]
        expected = condition["value"]
        actual = self._get_nested_value(test_data, field)

        return f"Field '{field}' has value '{actual}', expected {operator} '{expected}': {'PASS' if result else 'FAIL'}"

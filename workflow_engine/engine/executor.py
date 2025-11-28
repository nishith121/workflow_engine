"""
Workflow Execution Engine
Handles the execution of BPMN workflows in Frappe
"""

import frappe
from frappe import _
from frappe.utils import now, add_to_date, get_datetime
from typing import Dict, List, Optional, Any
import json
import re

from workflow_engine.engine.parser import BPMNParser


class WorkflowExecutor:
    """Main workflow execution engine"""

    def __init__(self, workflow_instance_name: str):
        """
        Initialize executor with workflow instance

        Args:
            workflow_instance_name: Name of the Workflow Instance document
        """
        self.instance = frappe.get_doc("Workflow Instance", workflow_instance_name)
        self.definition = frappe.get_doc("Workflow Definition", self.instance.workflow_definition)
        self.parser = BPMNParser(self.definition.bpmn_xml)
        self.context = ExecutionContext(self.instance)

    def start(self):
        """Start workflow execution from the start event"""
        # Get start event
        start_event = self.parser.get_start_event()

        if not start_event:
            self.instance.fail_workflow("No start event found in workflow definition")
            return

        # Update instance status
        self.instance.status = "Running"
        self.instance.current_node_id = start_event['id']
        self.instance.current_node_type = start_event['type']
        self.instance.save(ignore_permissions=True)
        frappe.db.commit()

        # Log start
        self.instance.add_log(
            node_id=start_event['id'],
            node_type=start_event['type'],
            message="Workflow started",
            status="Success"
        )

        # Execute next nodes
        self.move_to_next_nodes(start_event['id'])

    def move_to_next_nodes(self, current_node_id: str):
        """
        Move workflow to the next node(s)

        Args:
            current_node_id: ID of the current node
        """
        try:
            # Get outgoing flows
            outgoing_flows = self.parser.get_outgoing_flows(current_node_id)

            if not outgoing_flows:
                frappe.log_error(f"No outgoing flows from node {current_node_id}")
                return

            # Execute each outgoing flow
            for flow in outgoing_flows:
                # Check flow condition if exists
                if flow.get('condition'):
                    if not self.evaluate_condition(flow['condition']):
                        continue

                # Get target node
                target_node_id = flow['targetRef']
                target_node = self.parser.get_element_by_id(target_node_id)

                if not target_node:
                    frappe.log_error(f"Target node {target_node_id} not found")
                    continue

                # Execute target node
                self.execute_node(target_node)

        except Exception as e:
            frappe.log_error(f"Error moving to next nodes: {str(e)}", "Workflow Execution Error")
            self.instance.fail_workflow(str(e))

    def execute_node(self, node: Dict[str, Any]):
        """
        Execute a workflow node based on its type

        Args:
            node: Node dictionary from parser
        """
        node_type = node['type']
        node_id = node['id']

        # Update current node
        self.instance.current_node_id = node_id
        self.instance.current_node_type = node_type
        self.instance.save(ignore_permissions=True)
        frappe.db.commit()

        # Log execution
        self.instance.add_log(
            node_id=node_id,
            node_type=node_type,
            message=f"Executing {node_type}: {node.get('name', node_id)}",
            status="Info"
        )

        # Execute based on type
        if node_type == 'endEvent':
            self.handle_end_event(node)
        elif node_type == 'userTask':
            self.handle_user_task(node)
        elif node_type == 'scriptTask':
            self.handle_script_task(node)
        elif node_type == 'serviceTask':
            self.handle_service_task(node)
        elif node_type == 'exclusiveGateway':
            self.handle_exclusive_gateway(node)
        elif node_type == 'parallelGateway':
            self.handle_parallel_gateway(node)
        elif node_type == 'intermediateCatchEvent':
            self.handle_timer_event(node)
        else:
            # Unknown node type - just move forward
            self.move_to_next_nodes(node_id)

    def handle_end_event(self, node: Dict[str, Any]):
        """Handle end event - complete the workflow"""
        self.instance.complete_workflow()

        self.instance.add_log(
            node_id=node['id'],
            node_type=node['type'],
            message=f"Workflow ended: {node.get('name', 'End')}",
            status="Success"
        )

    def handle_user_task(self, node: Dict[str, Any]):
        """
        Handle user task - create a Workflow Task

        Args:
            node: User task node
        """
        # Create workflow task
        task = frappe.get_doc({
            'doctype': 'Workflow Task',
            'workflow_instance': self.instance.name,
            'node_id': node['id'],
            'node_name': node.get('name', 'User Task'),
            'task_description': node.get('documentation', ''),
            'status': 'Open'
        })

        # Set assignee
        if node.get('assignee'):
            task.assigned_to = self.context.resolve_variable(node['assignee'])
        elif node.get('candidateGroups'):
            task.assigned_role = node['candidateGroups']

        # Set due date
        if node.get('dueDate'):
            task.due_date = self.calculate_due_date(node['dueDate'])

        task.insert(ignore_permissions=True)
        frappe.db.commit()

        # Update instance to waiting state
        self.instance.status = "Waiting"
        self.instance.save(ignore_permissions=True)

        self.instance.add_log(
            node_id=node['id'],
            node_type=node['type'],
            message=f"User task created: {task.name}",
            status="Success",
            details={'task_id': task.name}
        )

    def handle_task_completion(self, task_name: str, action: str, form_data: Optional[Dict] = None):
        """
        Handle user task completion and continue workflow

        Args:
            task_name: Name of the completed task
            action: Action taken (Approve/Reject/etc)
            form_data: Optional form data from task
        """
        task = frappe.get_doc("Workflow Task", task_name)

        # Store action result in context
        self.context.set_variable(f"task_{task.node_id}_action", action)
        if form_data:
            for key, value in form_data.items():
                self.context.set_variable(f"task_{task.node_id}_{key}", value)

        # Log completion
        self.instance.add_log(
            node_id=task.node_id,
            node_type='userTask',
            message=f"User task completed with action: {action}",
            status="Success",
            details={'action': action, 'form_data': form_data}
        )

        # Update instance status
        self.instance.status = "Running"
        self.instance.save(ignore_permissions=True)
        frappe.db.commit()

        # Continue execution
        self.move_to_next_nodes(task.node_id)

    def handle_task_rejection(self, task_name: str):
        """
        Handle user task rejection

        Args:
            task_name: Name of the rejected task
        """
        task = frappe.get_doc("Workflow Task", task_name)

        # Log rejection
        self.instance.add_log(
            node_id=task.node_id,
            node_type='userTask',
            message="User task rejected",
            status="Warning"
        )

        # For now, fail the workflow on rejection
        # In production, you might want to handle this differently
        self.instance.fail_workflow("Workflow rejected by user")

    def handle_script_task(self, node: Dict[str, Any]):
        """
        Handle script task - execute Python code

        Args:
            node: Script task node
        """
        script = node.get('script', '')

        if not script:
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message="No script defined for script task",
                status="Warning"
            )
            self.move_to_next_nodes(node['id'])
            return

        try:
            # Create execution context
            exec_globals = {
                'frappe': frappe,
                'context': self.context,
                'instance': self.instance,
                'doc': self.instance.get_reference_doc(),
                '_': _
            }

            # Execute script
            exec(script, exec_globals)

            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message="Script executed successfully",
                status="Success"
            )

            # Move to next nodes
            self.move_to_next_nodes(node['id'])

        except Exception as e:
            error_msg = f"Script execution failed: {str(e)}"
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message=error_msg,
                status="Error"
            )
            self.instance.fail_workflow(error_msg)

    def handle_service_task(self, node: Dict[str, Any]):
        """
        Handle service task - call a Python method or API

        Args:
            node: Service task node
        """
        implementation = node.get('implementation', '')

        if not implementation:
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message="No implementation defined for service task",
                status="Warning"
            )
            self.move_to_next_nodes(node['id'])
            return

        try:
            # Parse method path (e.g., "module.function" or "DocType.method")
            result = self.call_method(implementation)

            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message="Service task executed successfully",
                status="Success",
                details={'result': result}
            )

            # Store result in context
            self.context.set_variable(f"service_{node['id']}_result", result)

            # Move to next nodes
            self.move_to_next_nodes(node['id'])

        except Exception as e:
            error_msg = f"Service task execution failed: {str(e)}"
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message=error_msg,
                status="Error"
            )
            self.instance.fail_workflow(error_msg)

    def handle_exclusive_gateway(self, node: Dict[str, Any]):
        """
        Handle exclusive gateway (XOR) - evaluate conditions and take one path

        Args:
            node: Gateway node
        """
        outgoing_flows = self.parser.get_outgoing_flows(node['id'])

        # Evaluate each flow's condition
        selected_flow = None
        default_flow = node.get('default')

        for flow in outgoing_flows:
            if flow['id'] == default_flow:
                continue

            if flow.get('condition'):
                if self.evaluate_condition(flow['condition']):
                    selected_flow = flow
                    break
            else:
                # No condition means always true
                selected_flow = flow
                break

        # If no flow selected, use default
        if not selected_flow and default_flow:
            for flow in outgoing_flows:
                if flow['id'] == default_flow:
                    selected_flow = flow
                    break

        if selected_flow:
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message=f"Gateway evaluated, taking path: {selected_flow.get('name', selected_flow['id'])}",
                status="Success"
            )

            # Execute target node
            target_node = self.parser.get_element_by_id(selected_flow['targetRef'])
            if target_node:
                self.execute_node(target_node)
        else:
            error_msg = "No valid path found in exclusive gateway"
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message=error_msg,
                status="Error"
            )
            self.instance.fail_workflow(error_msg)

    def handle_parallel_gateway(self, node: Dict[str, Any]):
        """
        Handle parallel gateway (AND) - execute all paths in parallel

        Args:
            node: Gateway node
        """
        outgoing_flows = self.parser.get_outgoing_flows(node['id'])

        self.instance.add_log(
            node_id=node['id'],
            node_type=node['type'],
            message=f"Parallel gateway executing {len(outgoing_flows)} paths",
            status="Success"
        )

        # Execute all outgoing paths
        for flow in outgoing_flows:
            target_node = self.parser.get_element_by_id(flow['targetRef'])
            if target_node:
                self.execute_node(target_node)

    def handle_timer_event(self, node: Dict[str, Any]):
        """
        Handle timer event - schedule execution after a delay

        Args:
            node: Timer event node
        """
        duration = node.get('timeDuration')
        date = node.get('timeDate')

        if duration:
            # Schedule execution after duration
            scheduled_time = self.parse_duration(duration)

            frappe.enqueue(
                'workflow_engine.engine.executor.execute_timer_event',
                queue='long',
                timeout=None,
                is_async=True,
                at_front=False,
                now=False,
                enqueue_after_commit=True,
                scheduled_time=scheduled_time,
                instance_name=self.instance.name,
                node_id=node['id']
            )

            self.instance.status = "Waiting"
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message=f"Timer scheduled for {scheduled_time}",
                status="Info"
            )

        elif date:
            # Schedule execution at specific date
            scheduled_time = get_datetime(date)

            frappe.enqueue(
                'workflow_engine.engine.executor.execute_timer_event',
                queue='long',
                timeout=None,
                is_async=True,
                at_front=False,
                now=False,
                enqueue_after_commit=True,
                scheduled_time=scheduled_time,
                instance_name=self.instance.name,
                node_id=node['id']
            )

            self.instance.status = "Waiting"
            self.instance.add_log(
                node_id=node['id'],
                node_type=node['type'],
                message=f"Timer scheduled for {scheduled_time}",
                status="Info"
            )
        else:
            # No timer defined, just continue
            self.move_to_next_nodes(node['id'])

    def evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate a condition expression

        Args:
            condition: Condition expression (Python expression)

        Returns:
            True if condition is met, False otherwise
        """
        try:
            # Create evaluation context
            eval_globals = {
                'context': self.context,
                'instance': self.instance,
                'doc': self.instance.get_reference_doc(),
            }

            # Evaluate condition
            result = eval(condition, eval_globals)
            return bool(result)

        except Exception as e:
            frappe.log_error(f"Error evaluating condition '{condition}': {str(e)}")
            return False

    def call_method(self, method_path: str) -> Any:
        """
        Call a Python method

        Args:
            method_path: Dotted path to method (e.g., "module.function")

        Returns:
            Method return value
        """
        return frappe.call(method_path, instance=self.instance.name)

    def calculate_due_date(self, due_date_expr: str):
        """
        Calculate due date from expression

        Args:
            due_date_expr: Due date expression (e.g., "3d", "2h", "2023-12-31")

        Returns:
            Calculated datetime
        """
        # Check if it's a duration (e.g., "3d", "2h")
        match = re.match(r'(\d+)([hdwmy])', due_date_expr.lower())
        if match:
            value = int(match.group(1))
            unit = match.group(2)

            unit_map = {
                'h': 'hours',
                'd': 'days',
                'w': 'weeks',
                'm': 'months',
                'y': 'years'
            }

            return add_to_date(now(), **{unit_map[unit]: value})

        # Otherwise, parse as datetime
        return get_datetime(due_date_expr)

    def parse_duration(self, duration: str):
        """
        Parse ISO 8601 duration or simple duration format

        Args:
            duration: Duration string (e.g., "PT1H", "3d")

        Returns:
            Calculated datetime
        """
        # Simple format (e.g., "3d", "2h")
        match = re.match(r'(\d+)([hdwmy])', duration.lower())
        if match:
            return self.calculate_due_date(duration)

        # ISO 8601 format (e.g., "PT1H", "P3D")
        # For simplicity, we'll handle basic cases
        if duration.startswith('PT'):
            # Time duration
            duration = duration[2:]
            hours = 0
            minutes = 0

            if 'H' in duration:
                hours = int(duration.split('H')[0])
                duration = duration.split('H')[1]

            if 'M' in duration:
                minutes = int(duration.split('M')[0])

            return add_to_date(now(), hours=hours, minutes=minutes)

        elif duration.startswith('P'):
            # Date duration
            duration = duration[1:]
            days = 0
            months = 0
            years = 0

            if 'Y' in duration:
                years = int(duration.split('Y')[0])
                duration = duration.split('Y')[1]

            if 'M' in duration:
                months = int(duration.split('M')[0])
                duration = duration.split('M')[1]

            if 'D' in duration:
                days = int(duration.split('D')[0])

            return add_to_date(now(), years=years, months=months, days=days)

        return now()


class ExecutionContext:
    """Execution context for workflow variables and data"""

    def __init__(self, instance):
        self.instance = instance

    def get_variable(self, key: str, default=None):
        """Get workflow variable"""
        return self.instance.get_variable(key, default)

    def set_variable(self, key: str, value, var_type: str = "String"):
        """Set workflow variable"""
        self.instance.set_variable(key, value, var_type)
        self.instance.save(ignore_permissions=True)

    def resolve_variable(self, expression: str) -> Any:
        """
        Resolve variable expression

        Args:
            expression: Variable expression (e.g., "${user}", "john@example.com")

        Returns:
            Resolved value
        """
        # Check if it's a variable reference
        if expression.startswith('${') and expression.endswith('}'):
            var_name = expression[2:-1]
            return self.get_variable(var_name)

        # Return as-is
        return expression


def execute_timer_event(instance_name: str, node_id: str):
    """
    Execute timer event (called by scheduler)

    Args:
        instance_name: Workflow instance name
        node_id: Timer event node ID
    """
    executor = WorkflowExecutor(instance_name)

    executor.instance.add_log(
        node_id=node_id,
        node_type='intermediateCatchEvent',
        message="Timer event triggered",
        status="Success"
    )

    executor.instance.status = "Running"
    executor.instance.save(ignore_permissions=True)
    frappe.db.commit()

    # Continue execution
    executor.move_to_next_nodes(node_id)

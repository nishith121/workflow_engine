"""
API endpoints for Workflow Execution
"""

import frappe
from frappe import _
import json


@frappe.whitelist()
def start_workflow(workflow_definition, reference_doctype, reference_name):
    """
    Start a new workflow instance

    Args:
        workflow_definition: Name of Workflow Definition
        reference_doctype: Reference DocType
        reference_name: Reference Document name

    Returns:
        Created Workflow Instance
    """
    from workflow_engine.engine.executor import WorkflowExecutor

    # Create workflow instance
    instance = frappe.get_doc({
        'doctype': 'Workflow Instance',
        'workflow_definition': workflow_definition,
        'reference_doctype': reference_doctype,
        'reference_name': reference_name,
        'status': 'Pending'
    })

    instance.insert(ignore_permissions=True)
    frappe.db.commit()

    # Start execution
    executor = WorkflowExecutor(instance.name)
    executor.start()

    return instance.as_dict()


@frappe.whitelist()
def complete_task(task_name, action, comments=None, form_data=None):
    """
    Complete a workflow task

    Args:
        task_name: Workflow Task name
        action: Action taken
        comments: Optional comments
        form_data: Optional form data (JSON string)

    Returns:
        Updated task
    """
    if not frappe.has_permission("Workflow Task", "write", task_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    task = frappe.get_doc("Workflow Task", task_name)

    # Parse form data if provided
    form_data_dict = None
    if form_data:
        if isinstance(form_data, str):
            form_data_dict = json.loads(form_data)
        else:
            form_data_dict = form_data

    # Complete task
    task.complete_task(action, comments, form_data_dict)

    return task.as_dict()


@frappe.whitelist()
def reject_task(task_name, comments=None):
    """
    Reject a workflow task

    Args:
        task_name: Workflow Task name
        comments: Optional comments

    Returns:
        Updated task
    """
    if not frappe.has_permission("Workflow Task", "write", task_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    task = frappe.get_doc("Workflow Task", task_name)
    task.reject_task(comments)

    return task.as_dict()


@frappe.whitelist()
def get_my_tasks(status=None):
    """
    Get tasks assigned to current user

    Args:
        status: Optional status filter

    Returns:
        List of tasks
    """
    filters = {
        'assigned_to': frappe.session.user
    }

    if status:
        filters['status'] = status

    tasks = frappe.get_all(
        'Workflow Task',
        filters=filters,
        fields=['name', 'workflow_instance', 'node_name', 'status', 'priority',
                'due_date', 'reference_doctype', 'reference_name', 'assigned_on'],
        order_by='due_date asc, priority desc'
    )

    return tasks


@frappe.whitelist()
def get_workflow_instances(reference_doctype=None, reference_name=None, status=None):
    """
    Get workflow instances

    Args:
        reference_doctype: Filter by reference doctype
        reference_name: Filter by reference document
        status: Filter by status

    Returns:
        List of workflow instances
    """
    filters = {}

    if reference_doctype:
        filters['reference_doctype'] = reference_doctype

    if reference_name:
        filters['reference_name'] = reference_name

    if status:
        filters['status'] = status

    instances = frappe.get_all(
        'Workflow Instance',
        filters=filters,
        fields=['name', 'workflow_definition', 'reference_doctype', 'reference_name',
                'status', 'current_node_id', 'started_on', 'completed_on'],
        order_by='started_on desc'
    )

    return instances


@frappe.whitelist()
def restart_workflow(instance_name):
    """
    Restart a failed workflow

    Args:
        instance_name: Workflow Instance name

    Returns:
        Updated instance
    """
    if not frappe.has_permission("Workflow Instance", "write", instance_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    instance = frappe.get_doc("Workflow Instance", instance_name)

    if instance.status not in ['Failed', 'Cancelled']:
        frappe.throw(_("Only failed or cancelled workflows can be restarted"))

    instance.restart_workflow()

    return instance.as_dict()


@frappe.whitelist()
def cancel_workflow(instance_name):
    """
    Cancel a running workflow

    Args:
        instance_name: Workflow Instance name

    Returns:
        Updated instance
    """
    if not frappe.has_permission("Workflow Instance", "write", instance_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    instance = frappe.get_doc("Workflow Instance", instance_name)

    if instance.status in ['Completed', 'Cancelled']:
        frappe.throw(_("Cannot cancel completed or already cancelled workflow"))

    instance.status = "Cancelled"
    instance.save(ignore_permissions=True)

    instance.add_log(
        node_id="cancel",
        node_type="system",
        message=f"Workflow cancelled by {frappe.session.user}",
        status="Info"
    )

    return instance.as_dict()


@frappe.whitelist()
def get_workflow_variables(instance_name):
    """
    Get workflow variables for an instance

    Args:
        instance_name: Workflow Instance name

    Returns:
        Dictionary of variables
    """
    if not frappe.has_permission("Workflow Instance", "read", instance_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    instance = frappe.get_doc("Workflow Instance", instance_name)

    variables = {}
    for var in instance.workflow_variables:
        variables[var.key] = instance.parse_variable_value(var.value, var.type)

    return variables


@frappe.whitelist()
def set_workflow_variable(instance_name, key, value, var_type="String"):
    """
    Set a workflow variable

    Args:
        instance_name: Workflow Instance name
        key: Variable key
        value: Variable value
        var_type: Variable type

    Returns:
        Success message
    """
    if not frappe.has_permission("Workflow Instance", "write", instance_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    instance = frappe.get_doc("Workflow Instance", instance_name)
    instance.set_variable(key, value, var_type)
    instance.save(ignore_permissions=True)

    return {"success": True, "message": "Variable updated successfully"}

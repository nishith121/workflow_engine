"""
Scheduled tasks for workflow engine
"""

import frappe
from frappe.utils import now_datetime, add_days


def execute_pending_timers():
    """
    Execute pending timer events
    Called every 5 minutes by scheduler
    """
    # This is handled by enqueue in the executor
    # This function is here for any cleanup or monitoring
    pass


def check_task_due_dates():
    """
    Check for overdue tasks and send reminders
    Called hourly
    """
    from frappe.utils import get_datetime

    # Get tasks that are overdue
    overdue_tasks = frappe.get_all(
        "Workflow Task",
        filters={
            "status": ["in", ["Open", "In Progress"]],
            "due_date": ["<", now_datetime()]
        },
        fields=["name", "assigned_to", "node_name", "due_date", "workflow_instance"]
    )

    for task in overdue_tasks:
        if not task.assigned_to:
            continue

        # Send reminder email
        frappe.sendmail(
            recipients=[task.assigned_to],
            subject=f"Reminder: Overdue Workflow Task - {task.node_name}",
            message=f"""
                <p>This is a reminder that the following workflow task is overdue:</p>
                <p><strong>Task:</strong> {task.node_name}</p>
                <p><strong>Due Date:</strong> {task.due_date}</p>
                <p><a href="{frappe.utils.get_url_to_form('Workflow Task', task.name)}">View Task</a></p>
            """,
            now=True
        )


def cleanup_completed_instances():
    """
    Archive or cleanup old completed workflow instances
    Called daily
    """
    # Get completed instances older than 90 days
    cutoff_date = add_days(now_datetime(), -90)

    old_instances = frappe.get_all(
        "Workflow Instance",
        filters={
            "status": "Completed",
            "completed_on": ["<", cutoff_date]
        },
        fields=["name"]
    )

    # For now, just log the count
    # In production, you might want to archive these to a separate table
    if old_instances:
        frappe.log_error(
            f"Found {len(old_instances)} completed workflow instances older than 90 days",
            "Workflow Cleanup"
        )

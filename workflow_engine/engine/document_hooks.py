"""
Document hooks for automatic workflow triggering
"""

import frappe
from frappe import _


def on_document_submit(doc, method):
    """
    Triggered when a document is submitted
    Check if there's an active workflow for this DocType and start it
    """
    check_and_start_workflow(doc, 'on_submit')


def on_document_update(doc, method):
    """
    Triggered when a document is updated
    Check if there's an active workflow for this DocType and start it
    """
    # Only trigger on first save (when doc is new)
    if doc.is_new():
        check_and_start_workflow(doc, 'on_update')


def on_document_cancel(doc, method):
    """
    Triggered when a document is cancelled
    Cancel any running workflows for this document
    """
    # Get running workflows for this document
    instances = frappe.get_all(
        "Workflow Instance",
        filters={
            "reference_doctype": doc.doctype,
            "reference_name": doc.name,
            "status": ["in", ["Pending", "Running", "Waiting"]]
        }
    )

    # Cancel all running instances
    for instance in instances:
        instance_doc = frappe.get_doc("Workflow Instance", instance.name)
        instance_doc.status = "Cancelled"
        instance_doc.save(ignore_permissions=True)

        instance_doc.add_log(
            node_id="cancel",
            node_type="system",
            message=f"Workflow cancelled due to document cancellation",
            status="Info"
        )


def check_and_start_workflow(doc, trigger_event):
    """
    Check if there's an active workflow for this DocType and start it

    Args:
        doc: Document object
        trigger_event: Event that triggered this (on_submit, on_update, etc.)
    """
    # Check if there's an active workflow for this DocType
    workflows = frappe.get_all(
        "Workflow Definition",
        filters={
            "linked_doctype": doc.doctype,
            "is_active": 1
        },
        fields=["name", "workflow_config"]
    )

    if not workflows:
        return

    for workflow in workflows:
        # Check workflow config for trigger event
        should_trigger = True

        if workflow.workflow_config:
            import json
            try:
                config = json.loads(workflow.workflow_config)
                trigger_on = config.get('trigger_on', 'on_submit')

                if trigger_on != trigger_event:
                    should_trigger = False

                # Check additional conditions if specified
                if should_trigger and config.get('conditions'):
                    should_trigger = eval_conditions(doc, config['conditions'])

            except Exception as e:
                frappe.log_error(f"Error parsing workflow config: {str(e)}")
                continue

        if should_trigger:
            start_workflow_for_document(doc, workflow.name)


def start_workflow_for_document(doc, workflow_definition):
    """
    Start a workflow instance for a document

    Args:
        doc: Document object
        workflow_definition: Workflow Definition name
    """
    from workflow_engine.engine.executor import WorkflowExecutor

    # Check if workflow is already running for this document
    existing = frappe.db.exists({
        "doctype": "Workflow Instance",
        "workflow_definition": workflow_definition,
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "status": ["in", ["Pending", "Running", "Waiting"]]
    })

    if existing:
        # Workflow already running, don't start another
        return

    try:
        # Create workflow instance
        instance = frappe.get_doc({
            'doctype': 'Workflow Instance',
            'workflow_definition': workflow_definition,
            'reference_doctype': doc.doctype,
            'reference_name': doc.name,
            'status': 'Pending'
        })

        instance.insert(ignore_permissions=True)
        frappe.db.commit()

        # Start execution
        executor = WorkflowExecutor(instance.name)
        executor.start()

        frappe.msgprint(_(f"Workflow '{workflow_definition}' started for {doc.doctype} {doc.name}"))

    except Exception as e:
        frappe.log_error(f"Error starting workflow: {str(e)}", "Workflow Start Error")


def eval_conditions(doc, conditions):
    """
    Evaluate workflow trigger conditions

    Args:
        doc: Document object
        conditions: Conditions dictionary or expression string

    Returns:
        True if conditions are met, False otherwise
    """
    try:
        if isinstance(conditions, str):
            # Expression string
            return eval(conditions, {'doc': doc, 'frappe': frappe})
        elif isinstance(conditions, dict):
            # Dictionary of field: value conditions
            for field, expected_value in conditions.items():
                actual_value = doc.get(field)
                if actual_value != expected_value:
                    return False
            return True
        else:
            return True

    except Exception as e:
        frappe.log_error(f"Error evaluating conditions: {str(e)}")
        return False

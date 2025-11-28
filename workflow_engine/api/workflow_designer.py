"""
API endpoints for Workflow Designer
"""

import frappe
import html
from frappe import _


@frappe.whitelist()
def get_workflow_list():
    """Get list of all workflows"""
    workflows = frappe.get_all(
        "Workflow Definition",
        fields=["name", "workflow_name", "linked_doctype", "is_active", "version", "modified"],
        order_by="modified desc"
    )

    return workflows


@frappe.whitelist()
def get_workflow(name):
    """
    Get workflow definition by name

    Args:
        name: Workflow Definition name
    """
    if not frappe.has_permission("Workflow Definition", "read", name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    workflow = frappe.get_doc("Workflow Definition", name)
    workflow_dict = workflow.as_dict()
    
    # Unescape HTML entities in BPMN XML
    if workflow_dict.get('bpmn_xml'):
        workflow_dict['bpmn_xml'] = html.unescape(workflow_dict['bpmn_xml'])
    
    return workflow_dict


@frappe.whitelist()
def save_workflow(name=None, workflow_name=None, description=None, linked_doctype=None,
                  is_active=0, bpmn_xml=None, workflow_config=None):
    """
    Save workflow definition

    Args:
        name: Workflow Definition name (for updates)
        workflow_name: Workflow name
        description: Description
        linked_doctype: Linked DocType
        is_active: Is active flag
        bpmn_xml: BPMN XML content
        workflow_config: JSON configuration
    """
    if name:
        # Update existing workflow
        if not frappe.has_permission("Workflow Definition", "write", name):
            frappe.throw(_("Not permitted"), frappe.PermissionError)

        doc = frappe.get_doc("Workflow Definition", name)
    else:
        # Create new workflow
        if not frappe.has_permission("Workflow Definition", "create"):
            frappe.throw(_("Not permitted"), frappe.PermissionError)

        doc = frappe.new_doc("Workflow Definition")

    # Update fields
    if workflow_name:
        doc.workflow_name = workflow_name
    if description is not None:
        doc.description = description
    if linked_doctype:
        doc.linked_doctype = linked_doctype
    if is_active is not None:
        doc.is_active = int(is_active)
    if bpmn_xml:
        doc.bpmn_xml = bpmn_xml
    if workflow_config is not None:
        doc.workflow_config = workflow_config

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def delete_workflow(name):
    """
    Delete workflow definition

    Args:
        name: Workflow Definition name
    """
    if not frappe.has_permission("Workflow Definition", "delete", name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    frappe.delete_doc("Workflow Definition", name, ignore_permissions=True)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def validate_bpmn(bpmn_xml):
    """
    Validate BPMN XML

    Args:
        bpmn_xml: BPMN XML string

    Returns:
        Validation result
    """
    from workflow_engine.engine.parser import BPMNParser

    try:
        parser = BPMNParser(bpmn_xml)
        is_valid, errors = parser.validate()

        return {
            "valid": is_valid,
            "errors": errors
        }

    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)]
        }

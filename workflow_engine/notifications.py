"""
Notification configuration for Workflow Engine
"""

import frappe


def get_notification_config():
    """Return notification configuration for Workflow Engine"""
    return {
        "for_doctype": {
            "Workflow Task": {
                "status": "status",
                "conditions": ["status in ('Open', 'In Progress')"]
            }
        },
        "for_module_doctypes": {
            "Workflow Engine": "green"
        },
        "for_other_doctypes": {}
    }

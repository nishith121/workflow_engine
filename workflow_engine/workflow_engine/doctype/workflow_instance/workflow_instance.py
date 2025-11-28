import frappe
from frappe.model.document import Document
import json
from datetime import datetime


class WorkflowInstance(Document):
    def before_insert(self):
        """Initialize workflow instance"""
        self.started_on = frappe.utils.now()
        self.started_by = frappe.session.user
        self.status = "Pending"

    def get_variable(self, key, default=None):
        """Get workflow variable value"""
        for var in self.workflow_variables:
            if var.key == key:
                return self.parse_variable_value(var.value, var.type)
        return default

    def set_variable(self, key, value, var_type="String"):
        """Set workflow variable value"""
        # Check if variable exists
        for var in self.workflow_variables:
            if var.key == key:
                var.value = str(value)
                var.type = var_type
                return

        # Add new variable
        self.append("workflow_variables", {
            "key": key,
            "value": str(value),
            "type": var_type
        })

    def parse_variable_value(self, value, var_type):
        """Parse variable value based on type"""
        if var_type == "Int":
            return int(value)
        elif var_type == "Float":
            return float(value)
        elif var_type == "Boolean":
            return value.lower() in ['true', '1', 'yes']
        elif var_type == "JSON":
            return json.loads(value)
        else:
            return value

    def add_log(self, node_id, node_type, message, status="Success", details=None):
        """Add execution log entry"""
        self.append("workflow_logs", {
            "node_id": node_id,
            "node_type": node_type,
            "message": message,
            "status": status,
            "details": json.dumps(details) if details else None,
            "timestamp": frappe.utils.now(),
            "user": frappe.session.user
        })

    def complete_workflow(self):
        """Mark workflow as completed"""
        self.status = "Completed"
        self.completed_on = frappe.utils.now()
        self.completed_by = frappe.session.user
        self.current_node_id = None
        self.current_node_type = None
        self.save(ignore_permissions=True)

        # Add completion log
        self.add_log(
            node_id="end",
            node_type="endEvent",
            message="Workflow completed successfully",
            status="Success"
        )

    def fail_workflow(self, error_message):
        """Mark workflow as failed"""
        self.status = "Failed"
        self.error_message = error_message
        self.save(ignore_permissions=True)

        # Add error log
        self.add_log(
            node_id=self.current_node_id or "unknown",
            node_type=self.current_node_type or "unknown",
            message=f"Workflow failed: {error_message}",
            status="Error"
        )

    def get_reference_doc(self):
        """Get the reference document"""
        if self.reference_doctype and self.reference_name:
            return frappe.get_doc(self.reference_doctype, self.reference_name)
        return None

    def restart_workflow(self):
        """Restart the workflow from the beginning"""
        from workflow_engine.engine.executor import WorkflowExecutor

        # Reset instance
        self.status = "Running"
        self.current_node_id = None
        self.current_node_type = None
        self.error_message = None
        self.retry_count = (self.retry_count or 0) + 1
        self.save(ignore_permissions=True)

        # Add restart log
        self.add_log(
            node_id="restart",
            node_type="system",
            message=f"Workflow restarted (attempt {self.retry_count})",
            status="Info"
        )

        # Execute from start
        executor = WorkflowExecutor(self.name)
        executor.start()

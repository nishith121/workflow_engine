import frappe
from frappe.model.document import Document
from frappe import _


class WorkflowTask(Document):
    def before_insert(self):
        """Set assigned_on timestamp"""
        self.assigned_on = frappe.utils.now()

    def after_insert(self):
        """Create ToDo and send notification after task creation"""
        self.create_todo()
        self.send_notification()

    def validate(self):
        """Validate task assignment"""
        if not self.assigned_to and not self.assigned_role:
            frappe.throw(_("Either Assigned To or Assigned Role must be specified"))

    def create_todo(self):
        """Create a ToDo for the assigned user"""
        if not self.assigned_to:
            # If role is assigned, create ToDo for all users with that role
            if self.assigned_role:
                users = frappe.get_all("Has Role",
                    filters={"role": self.assigned_role, "parenttype": "User"},
                    fields=["parent"]
                )
                for user_row in users:
                    self._create_todo_for_user(user_row.parent)
        else:
            self._create_todo_for_user(self.assigned_to)

    def _create_todo_for_user(self, user):
        """Create ToDo for a specific user"""
        if frappe.db.exists("ToDo", {
            "reference_type": "Workflow Task",
            "reference_name": self.name,
            "allocated_to": user
        }):
            return

        todo = frappe.get_doc({
            "doctype": "ToDo",
            "allocated_to": user,
            "description": self.task_description or f"Workflow Task: {self.node_name}",
            "reference_type": "Workflow Task",
            "reference_name": self.name,
            "priority": self.priority,
            "status": "Open"
        })

        if self.due_date:
            todo.date = self.due_date

        todo.insert(ignore_permissions=True)

    def send_notification(self):
        """Send email notification to assigned user(s)"""
        recipients = []

        if self.assigned_to:
            recipients.append(self.assigned_to)
        elif self.assigned_role:
            users = frappe.get_all("Has Role",
                filters={"role": self.assigned_role, "parenttype": "User"},
                fields=["parent"]
            )
            recipients = [u.parent for u in users]

        if not recipients:
            return

        # Get workflow instance
        instance = frappe.get_doc("Workflow Instance", self.workflow_instance)

        # Get reference document link
        ref_link = frappe.utils.get_url_to_form(
            instance.reference_doctype,
            instance.reference_name
        )

        # Send email
        for recipient in recipients:
            frappe.sendmail(
                recipients=[recipient],
                subject=f"New Workflow Task: {self.node_name or 'Task'}",
                message=f"""
                    <p>A new workflow task has been assigned to you.</p>
                    <p><strong>Task:</strong> {self.node_name or 'Workflow Task'}</p>
                    <p><strong>Description:</strong> {self.task_description or 'N/A'}</p>
                    <p><strong>Priority:</strong> {self.priority}</p>
                    <p><strong>Due Date:</strong> {self.due_date or 'Not set'}</p>
                    <p><strong>Reference Document:</strong> <a href="{ref_link}">{instance.reference_name}</a></p>
                    <p><a href="{frappe.utils.get_url_to_form('Workflow Task', self.name)}">View Task</a></p>
                """,
                now=True
            )

    def complete_task(self, action, comments=None, form_data=None):
        """Complete the workflow task"""
        from workflow_engine.engine.executor import WorkflowExecutor

        self.status = "Completed"
        self.action_taken = action
        self.completed_on = frappe.utils.now()
        self.completed_by = frappe.session.user

        if comments:
            self.comments = comments

        if form_data:
            import json
            self.form_data = json.dumps(form_data)

        self.save(ignore_permissions=True)

        # Close associated ToDos
        todos = frappe.get_all("ToDo", filters={
            "reference_type": "Workflow Task",
            "reference_name": self.name,
            "status": ["!=", "Closed"]
        })

        for todo in todos:
            todo_doc = frappe.get_doc("ToDo", todo.name)
            todo_doc.status = "Closed"
            todo_doc.save(ignore_permissions=True)

        # Continue workflow execution
        executor = WorkflowExecutor(self.workflow_instance)
        executor.handle_task_completion(self.name, action, form_data)

        return True

    def reject_task(self, comments=None):
        """Reject the workflow task"""
        self.status = "Rejected"
        self.action_taken = "Reject"
        self.completed_on = frappe.utils.now()
        self.completed_by = frappe.session.user

        if comments:
            self.comments = comments

        self.save(ignore_permissions=True)

        # Close associated ToDos
        todos = frappe.get_all("ToDo", filters={
            "reference_type": "Workflow Task",
            "reference_name": self.name,
            "status": ["!=", "Closed"]
        })

        for todo in todos:
            todo_doc = frappe.get_doc("ToDo", todo.name)
            todo_doc.status = "Closed"
            todo_doc.save(ignore_permissions=True)

        # Handle rejection in workflow
        from workflow_engine.engine.executor import WorkflowExecutor
        executor = WorkflowExecutor(self.workflow_instance)
        executor.handle_task_rejection(self.name)

        return True

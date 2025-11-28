# Workflow Engine - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [BPMN Elements Support](#bpmn-elements-support)
6. [Workflow Designer](#workflow-designer)
7. [Workflow Execution](#workflow-execution)
8. [API Reference](#api-reference)
9. [Integration Guide](#integration-guide)
10. [Examples](#examples)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Workflow Engine is an enterprise-grade, K2-style workflow automation system built for Frappe Framework. It provides a visual BPMN.js designer and a powerful Python-based execution engine.

### Key Features

- **Visual Designer**: BPMN.js-based drag-and-drop workflow designer
- **Full BPMN Support**: User Tasks, Script Tasks, Service Tasks, Gateways, Events
- **Python Runtime**: 100% Python execution engine running in Frappe
- **Frappe Integration**: Native integration with ToDo, Notifications, Assignments
- **Enterprise Ready**: Scalable, extensible, production-ready
- **Role-Based Access**: Frappe's permission system integration
- **Event Hooks**: Automatic workflow triggering on document events
- **REST API**: Complete API for external integrations

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Designer (BPMN.js)              │
│                     ↓                                        │
│                Workflow Definition (DocType)                │
│                     ↓                                        │
│              BPMN Parser (Python/lxml)                      │
│                     ↓                                        │
│            Workflow Executor (Python Engine)                │
│                     ↓                                        │
│     ┌──────────────┴──────────────┐                        │
│     ↓                              ↓                        │
│ Workflow Instance            Workflow Task                  │
│     ↓                              ↓                        │
│ Variables & Logs             ToDo & Notifications           │
└─────────────────────────────────────────────────────────────┘
```

### DocTypes

#### 1. Workflow Definition
Stores BPMN workflow definitions

**Fields:**
- `workflow_name` - Unique workflow name
- `linked_doctype` - Target DocType for workflow
- `bpmn_xml` - BPMN 2.0 XML content
- `is_active` - Activation status
- `version` - Version number
- `workflow_config` - JSON configuration
- `start_event_id`, `end_event_id` - Metadata

#### 2. Workflow Instance
Runtime instance of a workflow

**Fields:**
- `workflow_definition` - Link to definition
- `reference_doctype`, `reference_name` - Linked document
- `status` - Current status (Pending/Running/Waiting/Completed/Failed)
- `current_node_id` - Current execution node
- `workflow_variables` - Child table of variables
- `workflow_logs` - Execution logs
- `started_on`, `completed_on` - Timeline

#### 3. Workflow Task
User tasks requiring human action

**Fields:**
- `workflow_instance` - Parent instance
- `node_id`, `node_name` - BPMN node reference
- `assigned_to`, `assigned_role` - Assignment
- `status` - Task status
- `action_taken` - Approve/Reject/Custom
- `due_date` - Deadline
- `comments`, `form_data` - User input

#### 4. Workflow Log (Child Table)
Execution audit trail

#### 5. Workflow Variable (Child Table)
Runtime variables storage

---

## Installation

### Step 1: Get the App

```bash
cd /path/to/frappe-bench
bench get-app workflow_engine /path/to/workflow_engine
```

### Step 2: Install on Site

```bash
bench --site [your-site] install-app workflow_engine
```

### Step 3: Migrate

```bash
bench --site [your-site] migrate
```

### Step 4: Create Role

Create a new Role called "Workflow Manager" for users who will design workflows.

---

## Quick Start

### Creating Your First Workflow

#### 1. Open Workflow Designer

Navigate to: **Desk → Workflow Engine → Workflow Designer**

#### 2. Create New Workflow

1. Click "New Workflow"
2. Design your workflow using BPMN.js elements:
   - Drag Start Event from palette
   - Add User Tasks, Gateways, etc.
   - Connect with Sequence Flows
   - Add End Event

#### 3. Configure Workflow Properties

1. Click "Save"
2. Fill in:
   - Workflow Name: "Leave Approval"
   - Linked DocType: "Leave Application"
   - Description: "Two-level leave approval"
   - Is Active: ✓

#### 4. Configure Nodes

Click on each node to configure:

**User Task:**
- Name: "Manager Approval"
- Assignee: `${doc.reports_to}` (dynamic)
- Candidate Groups: "Manager" (role-based)
- Due Date: "3d" (3 days from now)

**Gateway:**
- Conditions on outgoing flows:
  ```python
  context.get_variable('task_ManagerApproval_action') == 'Approve'
  ```

#### 5. Save and Activate

Click "Save" → Enable "Is Active"

---

## BPMN Elements Support

### Events

#### Start Event
- Triggers workflow execution
- One per workflow
- No configuration needed

#### End Event
- Terminates workflow
- Multiple end events allowed
- Marks workflow as completed

#### Timer Event (Intermediate)
- Delays execution
- Configuration:
  - `timeDuration`: "PT1H" (ISO 8601) or "3d" (simple format)
  - `timeDate`: "2025-12-31 10:00:00"

### Tasks

#### User Task
Creates a Workflow Task for human interaction

**Configuration:**
```xml
<bpmn:userTask id="Task1" name="Review Document" assignee="${doc.owner}">
  <bpmn:documentation>Please review and approve</bpmn:documentation>
</bpmn:userTask>
```

**Attributes:**
- `assignee` - User email or variable
- `candidateGroups` - Role name
- `dueDate` - "3d", "2025-12-31", etc.
- `documentation` - Task instructions

#### Script Task
Executes Python code

**Configuration:**
```xml
<bpmn:scriptTask id="Script1" name="Update Status" scriptFormat="python">
  <bpmn:script>
doc = instance.get_reference_doc()
doc.workflow_state = "Approved"
doc.save()
frappe.db.commit()
  </bpmn:script>
</bpmn:scriptTask>
```

**Available Variables:**
- `frappe` - Frappe module
- `context` - ExecutionContext object
- `instance` - Workflow Instance document
- `doc` - Reference document

#### Service Task
Calls a Python method or API

**Configuration:**
```xml
<bpmn:serviceTask id="Service1" name="Send Email" implementation="myapp.api.send_approval_email">
</bpmn:serviceTask>
```

### Gateways

#### Exclusive Gateway (XOR)
Takes one path based on conditions

**Example:**
```xml
<bpmn:exclusiveGateway id="Gateway1" name="Decision">
  <bpmn:incoming>Flow1</bpmn:incoming>
  <bpmn:outgoing>FlowApproved</bpmn:outgoing>
  <bpmn:outgoing>FlowRejected</bpmn:outgoing>
</bpmn:exclusiveGateway>

<bpmn:sequenceFlow id="FlowApproved" sourceRef="Gateway1" targetRef="NextTask">
  <bpmn:conditionExpression>
    context.get_variable('action') == 'Approve'
  </bpmn:conditionExpression>
</bpmn:sequenceFlow>
```

#### Parallel Gateway (AND)
Executes all paths simultaneously

**Use Case:** Send for approval to multiple people at once

---

## Workflow Designer

### Interface Overview

**Header:**
- New Workflow - Create blank workflow
- Load - Open existing workflow
- Save - Save changes
- Export - Download BPMN XML
- Import - Upload BPMN XML

**Sidebar:**
- Workflow Info - Current workflow details
- Properties Panel - Selected element properties

**Canvas:**
- BPMN.js Modeler - Visual designer
- Drag elements from palette
- Connect with arrows
- Double-click to edit names

### Best Practices

1. **Clear Naming**: Use descriptive names for tasks and gateways
2. **Documentation**: Add documentation to user tasks
3. **Error Handling**: Always have paths for both approval and rejection
4. **Testing**: Test with inactive workflows first
5. **Version Control**: Export workflows before major changes

---

## Workflow Execution

### Automatic Triggering

Configure in Workflow Definition → Workflow Config:

```json
{
  "trigger_on": "on_submit",
  "conditions": {
    "status": "Pending"
  }
}
```

**Trigger Options:**
- `on_submit` - When document is submitted
- `on_update` - When document is saved (first time only)

### Manual Triggering

```python
from workflow_engine.api.workflow_execution import start_workflow

start_workflow(
    workflow_definition="Leave Approval",
    reference_doctype="Leave Application",
    reference_name="HR-LAP-2025-00001"
)
```

### Task Completion

```python
from workflow_engine.api.workflow_execution import complete_task

complete_task(
    task_name="WFT-Leave Approval-0001",
    action="Approve",
    comments="Approved by manager",
    form_data={"approved_days": 5}
)
```

### Variables

**Setting Variables:**
```python
instance.set_variable("approved_amount", 1000, "Float")
instance.set_variable("approver_name", "John Doe", "String")
```

**Getting Variables:**
```python
amount = instance.get_variable("approved_amount")  # Returns 1000
```

**Using in Conditions:**
```python
context.get_variable('approved_amount') > 5000
```

---

## API Reference

### Workflow Designer API

#### Get Workflow List
```javascript
GET /api/method/workflow_engine.api.workflow_designer.get_workflow_list
```

#### Save Workflow
```javascript
POST /api/method/workflow_engine.api.workflow_designer.save_workflow
{
  "workflow_name": "My Workflow",
  "linked_doctype": "Sales Order",
  "bpmn_xml": "<bpmn:definitions>...</bpmn:definitions>",
  "is_active": 1
}
```

### Workflow Execution API

#### Start Workflow
```javascript
POST /api/method/workflow_engine.api.workflow_execution.start_workflow
{
  "workflow_definition": "Leave Approval",
  "reference_doctype": "Leave Application",
  "reference_name": "HR-LAP-2025-00001"
}
```

#### Complete Task
```javascript
POST /api/method/workflow_engine.api.workflow_execution.complete_task
{
  "task_name": "WFT-Leave Approval-0001",
  "action": "Approve",
  "comments": "Looks good"
}
```

#### Get My Tasks
```javascript
GET /api/method/workflow_engine.api.workflow_execution.get_my_tasks?status=Open
```

---

## Integration Guide

### Triggering Workflows from DocType

Add to your custom DocType's `.py` file:

```python
def on_submit(self):
    # Auto-trigger workflow
    from workflow_engine.engine.document_hooks import start_workflow_for_document
    start_workflow_for_document(self, "My Workflow")
```

### Adding Workflow Button

In your DocType's `.js` file:

```javascript
frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Start Approval'), function() {
                workflow_engine.start_workflow(
                    'Sales Order Approval',
                    'Sales Order',
                    frm.doc.name,
                    function() {
                        frm.reload_doc();
                    }
                );
            });
        }
    }
});
```

---

## Examples

### Example 1: Simple Leave Approval

**Flow:**
1. Start → Manager Approval → End

**BPMN:** See `fixtures/leave_request_workflow.xml`

### Example 2: Multi-Level Purchase Order Approval

**Flow:**
1. Start
2. Amount Check (Gateway)
   - If < $1000 → Manager → End
   - If >= $1000 → Manager → Director → CFO → End

**Script Task for Email:**
```xml
<bpmn:scriptTask id="SendEmail" scriptFormat="python">
  <bpmn:script>
doc = instance.get_reference_doc()
frappe.sendmail(
    recipients=[doc.owner],
    subject="Purchase Order Approved",
    message=f"Your PO {doc.name} has been approved"
)
  </bpmn:script>
</bpmn:scriptTask>
```

### Example 3: Parallel Approvals

**Flow:**
Start → Parallel Gateway → [Finance Approval + Legal Approval] → Parallel Gateway (Join) → End

---

## Troubleshooting

### Workflow Not Starting

**Check:**
1. Is workflow active? (`is_active = 1`)
2. Does `linked_doctype` match document type?
3. Are trigger conditions met?
4. Check Error Log for exceptions

### Task Not Assigned

**Check:**
1. User exists: `assigned_to` must be valid user email
2. Role exists: `candidateGroups` must be valid role
3. Check Workflow Log for errors

### Gateway Not Working

**Check:**
1. Condition syntax: Must be valid Python expression
2. Variable exists: Use `context.get_variable()` not direct access
3. At least one flow must be true (add default flow)

### Script Task Failing

**Check:**
1. Python syntax errors
2. Variable availability
3. Permission issues (use `ignore_permissions=True`)
4. Check Workflow Instance logs

---

## Database Schema

### Workflow Instance Table

```sql
CREATE TABLE `tabWorkflow Instance` (
  `name` VARCHAR(140) PRIMARY KEY,
  `workflow_definition` VARCHAR(140),
  `reference_doctype` VARCHAR(140),
  `reference_name` VARCHAR(140),
  `status` VARCHAR(50),
  `current_node_id` VARCHAR(140),
  `started_on` DATETIME,
  `completed_on` DATETIME,
  INDEX idx_reference (reference_doctype, reference_name),
  INDEX idx_status (status)
);
```

---

## Performance Optimization

### Best Practices

1. **Use Indexes**: Reference documents are indexed
2. **Async Execution**: Long-running tasks use background jobs
3. **Cleanup**: Old workflows auto-archived after 90 days
4. **Caching**: BPMN parsing is cached per instance

### Monitoring

**Check Active Workflows:**
```python
active_count = frappe.db.count('Workflow Instance', {
    'status': ['in', ['Running', 'Waiting']]
})
```

**Check Overdue Tasks:**
```python
overdue = frappe.db.count('Workflow Task', {
    'status': 'Open',
    'due_date': ['<', frappe.utils.now()]
})
```

---

## Security

### Permissions

- Workflow Definition: System Manager, Workflow Manager
- Workflow Instance: All (read), System Manager (write)
- Workflow Task: Owner + Assigned User (write)

### Best Practices

1. Use role-based task assignment
2. Validate user permissions in script tasks
3. Sanitize form data inputs
4. Use `ignore_permissions=True` carefully

---

## Support & Contributing

### Reporting Issues

Create an issue at: https://github.com/frappe/workflow_engine/issues

### Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit pull request

---

## License

MIT License - See LICENSE file

---

## Changelog

### Version 1.0.0 (2025-01-26)

- Initial release
- BPMN.js designer integration
- Full BPMN 2.0 support
- Python execution engine
- Frappe integration
- REST API
- Unit tests

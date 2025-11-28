# Workflow Engine - Technical Architecture

## System Overview

The Workflow Engine is built as a native Frappe application that provides enterprise-grade workflow automation using BPMN 2.0 standards. The system is composed of three main layers:

1. **Presentation Layer** - BPMN.js Designer
2. **Business Logic Layer** - Python Execution Engine
3. **Data Layer** - Frappe DocTypes

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐         ┌─────────────────┐                 │
│  │  BPMN.js Modeler │◄───────►│  Frappe Desk    │                 │
│  │  (JavaScript)    │         │  Page           │                 │
│  └────────┬─────────┘         └────────┬────────┘                 │
│           │                            │                           │
│           └────────────┬───────────────┘                           │
│                        │                                           │
└────────────────────────┼───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          API LAYER (REST)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────┐      ┌──────────────────┐                 │
│  │ Designer API       │      │ Execution API    │                 │
│  │ - save_workflow    │      │ - start_workflow │                 │
│  │ - get_workflow     │      │ - complete_task  │                 │
│  │ - validate_bpmn    │      │ - get_my_tasks   │                 │
│  └────────────────────┘      └──────────────────┘                 │
│                                                                     │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐        │
│  │ BPMN Parser  │───►│   Executor   │───►│ Node Handlers │        │
│  │ (lxml)       │    │   Engine     │    │ - User Task   │        │
│  └──────────────┘    └──────────────┘    │ - Script Task │        │
│                                           │ - Gateway     │        │
│  ┌──────────────┐    ┌──────────────┐    │ - etc.        │        │
│  │Document Hooks│    │  Scheduler   │    └───────────────┘        │
│  │- on_submit   │    │- Timers      │                             │
│  │- on_update   │    │- Reminders   │                             │
│  └──────────────┘    └──────────────┘                             │
│                                                                     │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │    Workflow      │  │    Workflow     │  │    Workflow     │   │
│  │   Definition     │  │    Instance     │  │     Task        │   │
│  │                  │  │                 │  │                 │   │
│  │ - bpmn_xml       │  │ - status        │  │ - assigned_to   │   │
│  │ - linked_doctype │  │ - variables     │  │ - action_taken  │   │
│  │ - is_active      │  │ - logs          │  │ - due_date      │   │
│  └──────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                     │
│  ┌──────────────────┐  ┌─────────────────┐                        │
│  │  Workflow Log    │  │Workflow Variable│                        │
│  │  (Child Table)   │  │  (Child Table)  │                        │
│  └──────────────────┘  └─────────────────┘                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. BPMN Parser (`engine/parser.py`)

**Responsibility:** Parse and extract information from BPMN 2.0 XML

**Key Classes:**
- `BPMNParser` - Main parser class

**Methods:**
- `get_start_event()` - Extract start event
- `get_end_events()` - Extract end events
- `get_element_by_id()` - Get any element by ID
- `get_outgoing_flows()` - Get sequence flows from node
- `get_user_tasks()` - Extract all user tasks
- `get_script_tasks()` - Extract all script tasks
- `get_service_tasks()` - Extract all service tasks
- `get_exclusive_gateways()` - Extract XOR gateways
- `get_parallel_gateways()` - Extract AND gateways
- `validate()` - Validate BPMN structure

**Technologies:**
- `lxml` - XML parsing
- XPath queries for element selection

### 2. Workflow Executor (`engine/executor.py`)

**Responsibility:** Execute workflows and manage state transitions

**Key Classes:**
- `WorkflowExecutor` - Main execution engine
- `ExecutionContext` - Variable and context management

**Execution Flow:**
```
start()
  ├─> Get start event from parser
  ├─> Update instance status to "Running"
  ├─> Add log entry
  └─> move_to_next_nodes(start_event_id)
       ├─> Get outgoing flows
       ├─> Evaluate flow conditions
       ├─> For each valid flow:
       │    ├─> Get target node
       │    └─> execute_node(target_node)
       │         ├─> Update current node
       │         ├─> Add log entry
       │         └─> Route to handler based on node type
       │              ├─> handle_user_task()
       │              ├─> handle_script_task()
       │              ├─> handle_service_task()
       │              ├─> handle_exclusive_gateway()
       │              ├─> handle_parallel_gateway()
       │              ├─> handle_timer_event()
       │              └─> handle_end_event()
       └─> Continue until end event or waiting state
```

**Node Handlers:**

#### User Task Handler
```python
def handle_user_task(node):
    1. Create Workflow Task document
    2. Assign to user or role
    3. Calculate due date
    4. Set instance status to "Waiting"
    5. Create ToDo
    6. Send email notification
```

#### Script Task Handler
```python
def handle_script_task(node):
    1. Extract Python script from node
    2. Create execution context
    3. Execute script with available variables
    4. Log result
    5. Move to next nodes
```

#### Service Task Handler
```python
def handle_service_task(node):
    1. Extract method path
    2. Call method using frappe.call()
    3. Store result in context
    4. Log execution
    5. Move to next nodes
```

#### Gateway Handlers
```python
def handle_exclusive_gateway(node):
    1. Get all outgoing flows
    2. Evaluate each flow's condition
    3. Select first matching flow (or default)
    4. Execute target node

def handle_parallel_gateway(node):
    1. Get all outgoing flows
    2. Execute ALL target nodes in parallel
    3. Create separate execution branches
```

### 3. Document Hooks (`engine/document_hooks.py`)

**Responsibility:** Automatically trigger workflows on document events

**Hooks:**
- `on_document_submit()` - Triggered when document submitted
- `on_document_update()` - Triggered when document saved
- `on_document_cancel()` - Triggered when document cancelled

**Logic:**
```python
on_document_submit(doc):
  ├─> Find active workflows for doc.doctype
  ├─> For each workflow:
  │    ├─> Check workflow_config.trigger_on == "on_submit"
  │    ├─> Evaluate additional conditions
  │    ├─> Check if workflow already running
  │    └─> If all checks pass:
  │         ├─> Create Workflow Instance
  │         ├─> Start execution
  │         └─> Show notification
  └─> Return
```

### 4. Scheduler (`engine/scheduler.py`)

**Responsibility:** Background tasks and monitoring

**Scheduled Tasks:**

| Frequency | Task | Description |
|-----------|------|-------------|
| All (every 5 min) | `execute_pending_timers()` | Process timer events |
| Hourly | `check_task_due_dates()` | Send overdue reminders |
| Daily | `cleanup_completed_instances()` | Archive old workflows |

### 5. API Endpoints

#### Designer API (`api/workflow_designer.py`)

```python
@frappe.whitelist()
def save_workflow(name, workflow_name, bpmn_xml, ...):
    """Save or update workflow definition"""
    - Create/Update Workflow Definition
    - Parse and validate BPMN XML
    - Extract metadata
    - Return saved document

@frappe.whitelist()
def get_workflow(name):
    """Get workflow definition"""
    - Check permissions
    - Return workflow as dict

@frappe.whitelist()
def get_workflow_list():
    """List all workflows"""
    - Return all workflows with metadata
```

#### Execution API (`api/workflow_execution.py`)

```python
@frappe.whitelist()
def start_workflow(workflow_definition, reference_doctype, reference_name):
    """Start new workflow instance"""
    - Create Workflow Instance
    - Initialize WorkflowExecutor
    - Start execution
    - Return instance

@frappe.whitelist()
def complete_task(task_name, action, comments, form_data):
    """Complete user task"""
    - Get Workflow Task
    - Update task with action/comments
    - Store form data in variables
    - Close ToDos
    - Continue workflow execution

@frappe.whitelist()
def get_my_tasks(status):
    """Get tasks for current user"""
    - Query tasks assigned to user
    - Filter by status
    - Return task list
```

---

## Data Model

### Workflow Definition

```python
{
    "workflow_name": "Leave Approval",        # Unique name
    "linked_doctype": "Leave Application",    # Target DocType
    "bpmn_xml": "<bpmn:definitions>...",      # BPMN 2.0 XML
    "is_active": 1,                           # Active flag
    "version": "1.0",                         # Version number
    "workflow_config": {                      # JSON config
        "trigger_on": "on_submit",
        "conditions": {}
    },
    "start_event_id": "StartEvent_1",         # Metadata
    "end_event_id": "EndEvent_1"
}
```

### Workflow Instance

```python
{
    "workflow_definition": "Leave Approval",
    "reference_doctype": "Leave Application",
    "reference_name": "HR-LAP-2025-00001",
    "status": "Running",                      # Pending/Running/Waiting/Completed/Failed
    "current_node_id": "Task_ManagerApproval",
    "current_node_type": "userTask",
    "started_on": "2025-01-26 10:00:00",
    "started_by": "user@example.com",
    "workflow_variables": [                   # Child table
        {"key": "manager_action", "value": "Approve", "type": "String"}
    ],
    "workflow_logs": [                        # Child table
        {"node_id": "Start", "message": "Workflow started", "status": "Success"}
    ]
}
```

### Workflow Task

```python
{
    "workflow_instance": "WFI-Leave Approval-0001",
    "node_id": "Task_ManagerApproval",
    "node_name": "Manager Approval",
    "assigned_to": "manager@example.com",
    "assigned_role": null,
    "status": "Open",                         # Open/In Progress/Completed/Rejected
    "priority": "Medium",
    "due_date": "2025-01-29 10:00:00",
    "action_taken": null,                     # Approve/Reject/Custom
    "comments": null,
    "form_data": null                         # JSON string
}
```

---

## Execution State Machine

```
┌─────────┐
│ Pending │ (Initial state when instance created)
└────┬────┘
     │ executor.start()
     ▼
┌─────────┐
│ Running │ (Executing nodes)
└────┬────┘
     │
     ├──► User Task encountered ──► ┌─────────┐
     │                               │ Waiting │ (Waiting for user action)
     │                               └────┬────┘
     │                                    │ task.complete_task()
     │                                    ▼
     │                               ┌─────────┐
     │                               │ Running │
     │                               └────┬────┘
     │                                    │
     ├────────────────────────────────────┘
     │
     ├──► End Event reached ──────► ┌───────────┐
     │                               │ Completed │
     │                               └───────────┘
     │
     ├──► Error occurred ──────────► ┌────────┐
     │                                │ Failed │
     │                                └────────┘
     │
     └──► Manually cancelled ──────► ┌───────────┐
                                      │ Cancelled │
                                      └───────────┘
```

---

## Security Model

### Permission Levels

**Workflow Definition:**
- Create/Write: System Manager, Workflow Manager
- Read: All
- Execute: Automatic based on linked DocType

**Workflow Instance:**
- Create: System (automatic)
- Write: System Manager
- Read: All (filtered by reference document permissions)

**Workflow Task:**
- Create: System (automatic)
- Write: Assigned user, System Manager
- Read: Assigned user, System Manager

### Script Execution Security

**Script Tasks run with:**
- System permissions (ignore_permissions=True internally)
- Access to frappe module
- Access to instance and doc objects
- Sandboxed environment (no file I/O, no imports)

**Best Practices:**
- Validate user input in script tasks
- Use role-based task assignment
- Audit workflow logs regularly
- Test workflows in development first

---

## Performance Considerations

### Caching Strategy

1. **BPMN Parsing:** Parser instance created per executor (lifetime: single execution)
2. **Workflow Definition:** Loaded once per instance
3. **Variable Access:** In-memory access via instance object

### Database Queries

**Optimized Queries:**
- Indexes on: `reference_doctype + reference_name`
- Indexes on: `status`
- Indexes on: `assigned_to`

**Query Patterns:**
```python
# Good: Uses index
instances = frappe.get_all('Workflow Instance',
    filters={'reference_doctype': 'Sales Order', 'reference_name': 'SO-001'})

# Good: Uses index
tasks = frappe.get_all('Workflow Task',
    filters={'assigned_to': user, 'status': 'Open'})
```

### Async Processing

**Background Jobs:**
- Timer events use Frappe queue
- Long-running scripts should use `frappe.enqueue()`
- Email notifications sent asynchronously

---

## Error Handling

### Error Levels

1. **Parsing Errors:** Caught during workflow save, displayed to user
2. **Validation Errors:** Caught during execution, workflow fails gracefully
3. **Runtime Errors:** Logged, workflow status set to "Failed", user notified

### Error Recovery

```python
try:
    executor.execute_node(node)
except Exception as e:
    # Log error
    instance.add_log(
        node_id=node['id'],
        message=f"Error: {str(e)}",
        status="Error"
    )
    # Fail workflow
    instance.fail_workflow(str(e))
    # Notify user
    frappe.log_error(str(e), "Workflow Execution Error")
```

### Retry Logic

- Failed workflows can be manually restarted
- Retry count tracked in instance
- Variables and logs preserved across retries

---

## Extension Points

### Custom Node Types

Add new node handlers:

```python
# In executor.py
def execute_node(self, node):
    node_type = node['type']

    # Add your custom handler
    if node_type == 'myCustomTask':
        self.handle_custom_task(node)
    # ... existing handlers

def handle_custom_task(self, node):
    # Your implementation
    pass
```

### Custom Variables

Add computed variables:

```python
class ExecutionContext:
    def get_variable(self, key, default=None):
        # Check for computed variables
        if key == 'current_user':
            return frappe.session.user
        elif key == 'today':
            return frappe.utils.today()

        # Fall back to stored variables
        return self.instance.get_variable(key, default)
```

### Custom Triggers

Add new trigger events:

```python
# In hooks.py
doc_events = {
    "Sales Order": {
        "on_update_after_submit": "workflow_engine.custom.on_so_update"
    }
}

# In custom.py
def on_so_update(doc, method):
    if doc.grand_total > 10000:
        start_workflow_for_document(doc, "High Value SO Approval")
```

---

## Testing Strategy

### Unit Tests

Test each component in isolation:

```python
class TestBPMNParser(unittest.TestCase):
    def test_parse_start_event(self):
        parser = BPMNParser(xml)
        start = parser.get_start_event()
        self.assertEqual(start['id'], 'StartEvent_1')
```

### Integration Tests

Test full workflow execution:

```python
class TestWorkflowExecution(unittest.TestCase):
    def test_complete_workflow(self):
        instance = create_instance()
        executor = WorkflowExecutor(instance.name)
        executor.start()
        # ... assert expected behavior
```

### End-to-End Tests

Test through API:

```python
def test_api_workflow():
    response = frappe.client.post(
        'workflow_engine.api.workflow_execution.start_workflow',
        {'workflow_definition': 'Test', ...}
    )
    self.assertEqual(response['status'], 'Running')
```

---

## Monitoring and Observability

### Metrics to Track

1. **Workflow Metrics:**
   - Active instance count
   - Average completion time
   - Failure rate
   - Most used workflows

2. **Task Metrics:**
   - Pending task count
   - Overdue task count
   - Average task completion time

3. **Performance Metrics:**
   - Execution time per node type
   - Database query count
   - Queue length

### Logging

All executions logged in Workflow Log child table:

```python
{
    "node_id": "Task_1",
    "node_type": "userTask",
    "message": "User task created",
    "status": "Success",
    "timestamp": "2025-01-26 10:00:00",
    "user": "admin@example.com",
    "details": "{}"  # JSON
}
```

---

## Deployment Architecture

### Development
```
Local Frappe Bench
├─> MariaDB (localhost)
├─> Redis (localhost)
└─> Single worker process
```

### Production
```
Load Balancer
├─> Web Server 1 (Nginx + Gunicorn)
├─> Web Server 2 (Nginx + Gunicorn)
│
├─> Background Worker 1 (RQ)
├─> Background Worker 2 (RQ)
│
├─> MariaDB Cluster
│   ├─> Master
│   └─> Replica
│
└─> Redis Cluster
    ├─> Master
    └─> Replica
```

---

## Future Enhancements

1. **Workflow Versioning:** Support multiple versions of same workflow
2. **Subprocess Support:** Nested workflows
3. **Message Events:** Inter-workflow communication
4. **Boundary Events:** Error/timeout handling
5. **Visual Analytics:** Workflow performance dashboards
6. **Form Builder:** Custom form designer for user tasks
7. **Approval Matrix:** Dynamic approval routing
8. **SLA Management:** Automatic escalation

---

This architecture provides a solid foundation for enterprise workflow automation while remaining flexible and extensible for future requirements.

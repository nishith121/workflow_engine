# Workflow Engine - Setup Guide

## Complete Installation and Configuration Guide

### Prerequisites

- Frappe Framework v14 or v15
- Python 3.10+
- MariaDB 10.6+
- Node.js 18+
- Bench CLI

---

## Step-by-Step Installation

### 1. Install the App

```bash
# Navigate to your bench directory
cd /path/to/frappe-bench

# Get the app
bench get-app workflow_engine /path/to/workflow_engine

# Install on your site
bench --site [your-site-name] install-app workflow_engine

# Run migrations
bench --site [your-site-name] migrate

# Build assets
bench build --app workflow_engine

# Restart bench
bench restart
```

### 2. Create Required Roles

```bash
# Open bench console
bench --site [your-site-name] console

# Create Workflow Manager role
frappe.get_doc({
    'doctype': 'Role',
    'role_name': 'Workflow Manager',
    'desk_access': 1
}).insert()

frappe.db.commit()
```

### 3. Assign Permissions

Go to **Role Permission Manager** and set:

**Workflow Definition:**
- System Manager: All permissions
- Workflow Manager: Create, Read, Write, Export

**Workflow Instance:**
- System Manager: All permissions
- All: Read

**Workflow Task:**
- System Manager: All permissions
- All: Read (own records), Write (assigned records)

### 4. Verify Installation

```bash
# Check if doctypes are created
bench --site [your-site-name] console

frappe.db.get_all('DocType', filters={'module': 'Workflow Engine'}, fields=['name'])
```

Expected output:
- Workflow Definition
- Workflow Instance
- Workflow Task
- Workflow Log
- Workflow Variable

---

## Configuration

### 1. Enable Workflow Engine Features

Add to `site_config.json`:

```json
{
  "workflow_engine": {
    "enabled": true,
    "auto_trigger": true,
    "cleanup_days": 90,
    "task_reminder_hours": [24, 48, 72]
  }
}
```

### 2. Configure Email Notifications

Ensure email is configured in your site:

```bash
bench --site [your-site-name] set-config mail_server "smtp.gmail.com"
bench --site [your-site-name] set-config mail_port 587
bench --site [your-site-name] set-config use_tls 1
bench --site [your-site-name] set-config mail_login "your-email@gmail.com"
bench --site [your-site-name] set-config mail_password "your-app-password"
```

### 3. Set Up Scheduler

Ensure scheduler is enabled:

```bash
# Enable scheduler
bench --site [your-site-name] enable-scheduler

# Verify scheduler events
bench --site [your-site-name] console

from workflow_engine.hooks import scheduler_events
print(scheduler_events)
```

---

## Creating Your First Workflow

### Example: Leave Request Workflow

#### 1. Create Leave Application DocType (if not exists)

```python
# In bench console
doc = frappe.get_doc({
    'doctype': 'DocType',
    'module': 'HR',
    'name': 'Leave Application',
    'fields': [
        {'fieldname': 'employee', 'fieldtype': 'Link', 'options': 'User', 'label': 'Employee'},
        {'fieldname': 'from_date', 'fieldtype': 'Date', 'label': 'From Date'},
        {'fieldname': 'to_date', 'fieldtype': 'Date', 'label': 'To Date'},
        {'fieldname': 'reason', 'fieldtype': 'Text', 'label': 'Reason'},
        {'fieldname': 'manager', 'fieldtype': 'Link', 'options': 'User', 'label': 'Manager'},
        {'fieldname': 'workflow_state', 'fieldtype': 'Data', 'label': 'Status', 'read_only': 1}
    ],
    'permissions': [{'role': 'All', 'read': 1, 'write': 1, 'create': 1}]
})
doc.insert()
frappe.db.commit()
```

#### 2. Open Workflow Designer

1. Navigate to: **Workflow Engine → Workflow Designer**
2. Click **New Workflow**

#### 3. Design the Workflow

**Add Elements:**

1. **Start Event** (already present)

2. **User Task - "Manager Approval"**
   - Drag User Task from palette
   - Name: "Manager Approval"
   - Click to select → Properties panel:
     - Assignee: `${doc.manager}`
     - Documentation: "Please review and approve this leave request"

3. **Exclusive Gateway - "Decision"**
   - Drag Exclusive Gateway
   - Name: "Manager Decision"

4. **Script Task - "Update Approved"**
   - Drag Script Task
   - Name: "Update Leave Status - Approved"
   - Script:
     ```python
     doc = instance.get_reference_doc()
     doc.workflow_state = "Approved"
     doc.save()
     frappe.db.commit()
     ```

5. **Script Task - "Update Rejected"**
   - Drag Script Task
   - Name: "Update Leave Status - Rejected"
   - Script:
     ```python
     doc = instance.get_reference_doc()
     doc.workflow_state = "Rejected"
     doc.save()
     frappe.db.commit()
     ```

6. **End Events**
   - Add two End Events: "Approved" and "Rejected"

**Connect Elements:**

1. Start → Manager Approval
2. Manager Approval → Decision Gateway
3. Decision Gateway → Update Approved (label: "Approved")
   - Condition: `context.get_variable('task_ManagerApproval_action') == 'Approve'`
4. Decision Gateway → Update Rejected (label: "Rejected")
   - Condition: `context.get_variable('task_ManagerApproval_action') == 'Reject'`
5. Update Approved → End (Approved)
6. Update Rejected → End (Rejected)

#### 4. Save Workflow

1. Click **Save**
2. Fill in properties:
   - Workflow Name: `Leave Request Approval`
   - Linked DocType: `Leave Application`
   - Description: `Manager approval for leave requests`
   - Is Active: ✓ (check)
   - Workflow Config:
     ```json
     {
       "trigger_on": "on_submit"
     }
     ```
3. Click **Save**

#### 5. Test the Workflow

```python
# Create a test leave application
leave = frappe.get_doc({
    'doctype': 'Leave Application',
    'employee': 'employee@example.com',
    'manager': 'manager@example.com',
    'from_date': '2025-02-01',
    'to_date': '2025-02-05',
    'reason': 'Vacation'
})
leave.insert()
leave.submit()  # This triggers the workflow

# Check workflow instance
instances = frappe.get_all('Workflow Instance',
    filters={'reference_name': leave.name},
    fields=['name', 'status', 'current_node_id']
)
print(instances)

# Check created task
tasks = frappe.get_all('Workflow Task',
    filters={'workflow_instance': instances[0].name},
    fields=['name', 'node_name', 'assigned_to', 'status']
)
print(tasks)
```

---

## Testing

### Run Unit Tests

```bash
# Run all workflow engine tests
bench --site [your-site-name] run-tests --app workflow_engine

# Run specific test
bench --site [your-site-name] run-tests --app workflow_engine --module workflow_engine.tests.test_workflow_engine
```

### Manual Testing Checklist

- [ ] Can open Workflow Designer
- [ ] Can create new workflow
- [ ] Can save workflow
- [ ] Can load existing workflow
- [ ] Can export/import BPMN XML
- [ ] Workflow triggers on document submit
- [ ] User task creates ToDo
- [ ] User receives email notification
- [ ] Task completion continues workflow
- [ ] Gateway evaluates conditions correctly
- [ ] Script task executes successfully
- [ ] Workflow completes at end event
- [ ] Workflow logs are created

---

## Troubleshooting Installation

### Issue: BPMN.js not loading

**Solution:**
```bash
# Clear cache
bench --site [your-site-name] clear-cache

# Rebuild
bench build --app workflow_engine

# Hard reload browser (Ctrl + Shift + R)
```

### Issue: Import error for lxml

**Solution:**
```bash
# Install lxml
pip install lxml

# Or in bench
bench pip install lxml
```

### Issue: Workflow not auto-triggering

**Check:**
1. Is workflow active?
2. Is `trigger_on` set correctly in config?
3. Are document hooks enabled in hooks.py?
4. Check Error Log

```python
# Verify hooks
frappe.get_hooks('doc_events')
```

### Issue: Tasks not creating ToDos

**Check:**
1. Assigned user exists
2. User has email address
3. Email settings configured
4. Check Workflow Task creation in logs

---

## Production Deployment

### 1. Enable Production Mode

```bash
bench --site [your-site-name] set-config developer_mode 0
bench --site [your-site-name] set-config server_script_enabled 0  # Optional security
```

### 2. Set Up Supervisor (Production)

```bash
# Generate supervisor config
bench setup supervisor

# Enable and start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 3. Set Up Nginx

```bash
# Generate nginx config
bench setup nginx

# Enable and restart
sudo ln -s /path/to/frappe-bench/config/nginx.conf /etc/nginx/sites-enabled/[site-name]
sudo service nginx reload
```

### 4. Enable SSL

```bash
bench setup lets-encrypt [site-name]
```

### 5. Monitor Workflows

Create custom report or dashboard:

```python
# Count active workflows
active = frappe.db.count('Workflow Instance', {'status': ['in', ['Running', 'Waiting']]})

# Count pending tasks
pending = frappe.db.count('Workflow Task', {'status': 'Open'})

# Average completion time
avg_time = frappe.db.sql("""
    SELECT AVG(TIMESTAMPDIFF(HOUR, started_on, completed_on)) as avg_hours
    FROM `tabWorkflow Instance`
    WHERE status = 'Completed'
    AND completed_on > DATE_SUB(NOW(), INTERVAL 30 DAY)
""")[0][0]
```

---

## Backup and Maintenance

### Backup Workflows

```bash
# Export all workflow definitions
bench --site [your-site-name] console

workflows = frappe.get_all('Workflow Definition', fields=['name', 'bpmn_xml'])
for wf in workflows:
    with open(f'/tmp/{wf.name}.bpmn', 'w') as f:
        f.write(frappe.get_doc('Workflow Definition', wf.name).bpmn_xml)
```

### Cleanup Old Instances

```bash
# Run cleanup manually
bench --site [your-site-name] console

from workflow_engine.engine.scheduler import cleanup_completed_instances
cleanup_completed_instances()
```

### Monitor Performance

```sql
-- Slowest workflows
SELECT
    workflow_definition,
    AVG(TIMESTAMPDIFF(MINUTE, started_on, completed_on)) as avg_minutes,
    COUNT(*) as count
FROM `tabWorkflow Instance`
WHERE status = 'Completed'
GROUP BY workflow_definition
ORDER BY avg_minutes DESC;

-- Most active workflows
SELECT
    workflow_definition,
    COUNT(*) as instance_count
FROM `tabWorkflow Instance`
WHERE started_on > DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY workflow_definition
ORDER BY instance_count DESC;
```

---

## Next Steps

1. Read [DOCUMENTATION.md](DOCUMENTATION.md) for detailed usage
2. Explore example workflows in `fixtures/`
3. Customize for your use cases
4. Set up monitoring and alerts
5. Train users on workflow designer

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/frappe/workflow_engine/issues
- Frappe Forum: https://discuss.frappe.io
- Documentation: DOCUMENTATION.md

---

## License

MIT License

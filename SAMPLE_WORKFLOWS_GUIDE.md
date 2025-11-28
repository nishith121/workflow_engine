# Sample Workflows Guide

I've created **4 sample workflows** that demonstrate different BPMN patterns and features. You can now load these in the Workflow Designer to explore and learn!

## How to View Sample Workflows

1. **Open Workflow Designer**: Navigate to `http://frappe3.localhost:8003/app/workflow-designer`
2. **Click "Load" button** in the toolbar
3. **Select a workflow** from the list to load it into the designer

---

## Sample Workflows Created

### 1. **Purchase Order Approval** (Simple Linear Flow)
**DocType:** ToDo  
**Pattern:** Linear Sequential Tasks  

**Flow:**
```
Start → Review PO → Approve PO → Send Email → End
```

**Demonstrates:**
- ✅ User Tasks (Review, Approve)
- ✅ Script Task (Send Email)
- ✅ Simple sequential flow

**Use Case:** Basic approval workflow where tasks must be completed in order.

---

### 2. **Task Assignment with Conditional Approval** (Exclusive Gateway)
**DocType:** ToDo  
**Pattern:** Conditional Branching  

**Flow:**
```
Start → Duration Check
         ├─ Short (≤3 days) → Manager Approval ─┐
         └─ Long (>3 days) → HR Approval ────────┤
                                                  ↓
                                          Update Calendar → End
```

**Demonstrates:**
- ✅ Exclusive Gateway (Decision point)
- ✅ Conditional flows with labels
- ✅ Converging paths

**Use Case:** Different approval paths based on conditions (e.g., amount, duration, etc.)

---

### 3. **User Onboarding Process** (Parallel Gateway)
**DocType:** User  
**Pattern:** Parallel Execution  

**Flow:**
```
Start → Split
         ├─ HR Setup ────┐
         └─ IT Setup ────┤
                         ↓
                    Join → Manager Welcome → Send Email → End
```

**Demonstrates:**
- ✅ Parallel Gateway (Fork/Join)
- ✅ Concurrent task execution
- ✅ Synchronization point

**Use Case:** Multiple tasks that can happen simultaneously and must all complete before proceeding.

---

### 4. **Document Processing Workflow** (Complex Multi-Gateway)
**DocType:** ToDo  
**Pattern:** Combined Patterns  

**Flow:**
```
Start → Review → Credit Check
                  ├─ Good Credit ──┐
                  └─ Needs Review → Credit Review ─┤
                                                    ↓
                                              Merge → Parallel Split
                                                      ├─ Check Inventory ─┐
                                                      └─ Arrange Shipping ─┤
                                                                           ↓
                                                                   Parallel Join → Create Invoice → Send Notification → End
```

**Demonstrates:**
- ✅ Exclusive Gateway (conditional)
- ✅ Parallel Gateway (concurrent tasks)
- ✅ Multiple merge points
- ✅ Complex flow patterns
- ✅ User Tasks AND Script Tasks

**Use Case:** Real-world business process with both conditional logic and parallel processing.

---

## Understanding BPMN Elements

### **Start Event** (Green circle)
- Triggers when workflow is initiated
- Only one per workflow

### **End Event** (Red circle with thick border)
- Marks successful completion
- Can have multiple end events

### **User Task** (Rectangle with person icon)
- Assigned to a specific user/role
- Creates a ToDo in Frappe
- Requires human action

### **Script Task** (Rectangle with script icon)
- Automated task
- Executed by the workflow engine
- No human intervention needed

### **Exclusive Gateway** (Diamond with X)
- **Decision point** - only ONE path is taken
- Based on conditions
- Example: "If amount > 10000, go to Manager, else go to Accounts"

### **Parallel Gateway** (Diamond with +)
- **Fork**: Starts multiple paths simultaneously
- **Join**: Waits for all paths to complete
- All paths execute concurrently

### **Sequence Flow** (Arrows)
- Connects elements
- Defines the flow direction
- Can have labels (conditions)

---

## How to Explore in the Designer

### **View the Canvas:**
1. Load a workflow using the "Load" button
2. The BPMN diagram will appear on the canvas
3. Use mouse wheel to zoom in/out
4. Click and drag to pan around

### **Inspect Elements:**
1. Click on any element (task, gateway, event)
2. View properties in the right sidebar
3. See element ID, type, and name

### **Modify a Workflow:**
1. Load an existing workflow
2. Use the palette on the left to add new elements:
   - Drag elements onto the canvas
   - Connect them using the connector tool
3. Click "Save" to save your modified version

### **Create New Workflow:**
1. Click "New Workflow" button
2. Design your flow using drag-and-drop
3. Click "Save" and fill in:
   - Workflow Name
   - Description
   - Linked DocType
   - Active status

---

## Tips for Learning

1. **Start Simple**: Load "Purchase Order Approval" first to understand the basics
2. **Study Patterns**: Load "Task Assignment" to see how gateways work
3. **Explore Parallel**: Load "User Onboarding" to understand concurrent execution
4. **Master Complex**: Load "Document Processing" to see everything together

5. **Experiment**: 
   - Try modifying the samples
   - Add new tasks
   - Change connections
   - Save as new versions

6. **Export/Import**:
   - Export workflows as `.bpmn` files
   - Share with team members
   - Import to restore or migrate

---

## Next Steps

### Test Execution
- These are sample *definitions* only (not active)
- To actually run them, you would need to:
  1. Activate the workflow (`is_active = 1`)
  2. Create a document of the linked DocType
  3. The workflow will auto-trigger based on document events

### Customize for Your Use Case
- Use these as templates
- Modify to match your business processes
- Add custom script tasks with your logic
- Assign to your actual roles/users

---

## Quick Reference: BPMN Patterns

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Sequential** | Tasks must happen in order | Approval chain |
| **Exclusive Gateway** | Only one path based on condition | Priority-based routing |
| **Parallel Gateway** | Multiple tasks can happen together | Department tasks |
| **Complex** | Real-world process with both | Order processing |

---

## Need Help?

- **Load a sample** and study the flow
- **Click elements** to see properties
- **Try modifications** - nothing will break!
- **Export** your experiments to save them

Enjoy exploring your K2/Nintex-style workflow designer! 🎉

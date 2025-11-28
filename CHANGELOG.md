# Changelog

All notable changes to the Workflow Engine project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-28

### Added
- **BPMN 2.0 Workflow Designer**
  - Visual drag-and-drop workflow designer powered by BPMN.js
  - Support for all major BPMN elements (Events, Tasks, Gateways, Flows)
  - Interactive canvas with zoom, pan, and element manipulation
  - Properties panel for element inspection
  - Real-time workflow visualization

- **Complete DocType Structure**
  - Workflow Definition: Store and manage workflow metadata and BPMN XML
  - Workflow Instance: Track workflow execution state and history
  - Workflow Task: Manage user tasks with assignments and completion tracking
  - Workflow Log: Comprehensive audit trail of all workflow activities
  - Workflow Variable: Store and retrieve workflow-scoped variables

- **Python-Based Execution Engine**
  - BPMN Parser with XML validation and structure extraction
  - Workflow Executor supporting:
    - Start/End Events
    - User Tasks (with Frappe ToDo integration)
    - Script Tasks (Python code execution)
    - Service Tasks (API calls)
    - Exclusive Gateways (conditional branching)
    - Parallel Gateways (concurrent execution)
    - Timer Events (scheduled execution)
  - Automatic navigation and flow control
  - Comprehensive error handling and rollback

- **REST API Endpoints**
  - `/api/method/workflow_engine.api.workflow_instance.start_workflow` - Start workflow execution
  - `/api/method/workflow_engine.api.workflow_instance.complete_task` - Complete user tasks
  - `/api/method/workflow_engine.api.workflow_instance.get_instance_details` - Get instance info
  - `/api/method/workflow_engine.api.workflow_designer.get_workflow_list` - List all workflows
  - `/api/method/workflow_engine.api.workflow_designer.get_workflow` - Get workflow definition
  - `/api/method/workflow_engine.api.workflow_designer.save_workflow` - Save workflow
  - `/api/method/workflow_engine.api.workflow_designer.validate_bpmn` - Validate BPMN XML

- **Workflow Designer Features**
  - Import/Export workflows as .bpmn XML files
  - Load and edit existing workflows
  - Save workflows with metadata (name, description, linked DocType)
  - Interactive help guide with comprehensive documentation
  - Sample workflows for learning and reference
  - Toolbar with New, Load, Save, Export, Import, Help actions

- **Frappe Integration**
  - Auto-trigger workflows on document events (on_submit, on_cancel, on_update)
  - DocType linking for workflow definitions
  - User/Role-based task assignment
  - Email notifications for task assignments
  - Background job execution with frappe.enqueue
  - Permission system integration

- **Sample Workflows**
  - Purchase Order Approval (linear workflow)
  - Task Assignment with Conditional Approval (exclusive gateway)
  - User Onboarding Process (parallel gateway)
  - Document Processing Workflow (complex multi-gateway)

- **Documentation**
  - Comprehensive README with quick start guide
  - ARCHITECTURE.md explaining system design
  - DOCUMENTATION.md with detailed API and usage docs
  - SETUP_GUIDE.md for installation and configuration
  - PROJECT_SUMMARY.md with feature overview
  - SAMPLE_WORKFLOWS_GUIDE.md for learning workflows
  - In-app interactive help guide

- **Testing**
  - Unit tests for all major components
  - Test coverage for BPMN Parser, Workflow Executor, and Task handling
  - Sample workflow execution tests
  - Automated test suite with proper teardown

### Technical Details
- **Frontend**: BPMN.js 11.5.0, jQuery, Bootstrap, ES5 JavaScript for compatibility
- **Backend**: Python 3.11+, Frappe Framework, lxml for XML parsing
- **Standards**: BPMN 2.0 compliant
- **License**: MIT

### Fixed
- HTML entity escaping in BPMN XML (workflow loading issue)
- ES6 syntax compatibility issues in Frappe environment
- Build system parsing errors with special characters in HTML
- LinkExistsError during test cleanup
- XMLSyntaxError with HTML-escaped XML content
- User task assignment validation errors

### Security
- Permission checks on all API endpoints
- User/Role-based access control
- Input validation for BPMN XML
- SQL injection prevention through Frappe ORM
- XSS protection in workflow designer

---

## Future Roadmap

### Planned for 2.0.0
- Visual workflow debugging and step-through execution
- Advanced BPMN features (sub-processes, message events, boundary events)
- Workflow versioning and migration tools
- Performance dashboard and analytics
- Multi-language support
- Advanced conditional expressions (like K2's SmartObjects)
- Integration with external systems (REST, SOAP, databases)
- Workflow templates marketplace

---

For more information, see [README.md](README.md) and [DOCUMENTATION.md](DOCUMENTATION.md).

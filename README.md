# Workflow Engine

Enterprise-grade K2-style Workflow Automation Engine for Frappe Framework

## Features

- **BPMN.js Designer**: Visual workflow designer with drag-and-drop interface
- **Python Runtime**: 100% Python-based execution engine
- **Full BPMN Support**: User Tasks, Script Tasks, Service Tasks, Gateways, Events
- **Frappe Integration**: Native integration with Frappe's permission, notification, and assignment systems
- **Enterprise-Ready**: Scalable, extensible, and production-ready

## Installation

```bash
bench get-app workflow_engine
bench --site [site-name] install-app workflow_engine
```

## Architecture

### Core Components

1. **Workflow Definition** - Stores BPMN XML definitions
2. **Workflow Instance** - Runtime instances of workflows
3. **Workflow Task** - User tasks requiring human interaction
4. **Workflow Engine** - Python-based BPMN execution engine

### Supported BPMN Elements

- Start Event / End Event
- User Task
- Script Task
- Service Task
- Exclusive Gateway (XOR)
- Parallel Gateway (AND)
- Timer Events

## Quick Start

1. Navigate to Workflow Designer
2. Create a new workflow definition
3. Design your workflow using BPMN.js
4. Link it to a DocType
5. Save and activate

## Documentation

For detailed documentation, visit the [Wiki](https://github.com/frappe/workflow_engine/wiki)

## License

MIT

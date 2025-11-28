#!/usr/bin/env python3
"""
Workflow Engine Installation Verification Script

Run this script after installation to verify all components are working correctly.

Usage:
    bench --site [site-name] execute workflow_engine.verify_installation.verify_all
"""

import frappe
from frappe import _


def verify_all():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("WORKFLOW ENGINE INSTALLATION VERIFICATION")
    print("="*70 + "\n")

    checks = [
        ("DocTypes", verify_doctypes),
        ("BPMN Parser", verify_parser),
        ("Workflow Executor", verify_executor),
        ("API Endpoints", verify_api),
        ("Page Access", verify_page),
        ("Permissions", verify_permissions),
        ("Scheduler", verify_scheduler),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        try:
            check_func()
            print("✓ PASS")
            results.append((name, True, None))
        except Exception as e:
            print(f"✗ FAIL: {str(e)}")
            results.append((name, False, str(e)))

    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70 + "\n")

    passed = sum(1 for _, status, _ in results if status)
    total = len(results)

    for name, status, error in results:
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"{name:.<50} {status_str}")
        if error:
            print(f"  Error: {error}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! Workflow Engine is ready to use.")
        return True
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please review the errors above.")
        return False


def verify_doctypes():
    """Verify all required DocTypes exist"""
    required_doctypes = [
        "Workflow Definition",
        "Workflow Instance",
        "Workflow Task",
        "Workflow Log",
        "Workflow Variable"
    ]

    for doctype in required_doctypes:
        if not frappe.db.exists("DocType", doctype):
            raise Exception(f"DocType '{doctype}' not found")


def verify_parser():
    """Verify BPMN parser is working"""
    from workflow_engine.engine.parser import BPMNParser

    # Test XML
    test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_1">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_1" name="End">
      <bpmn:incoming>Flow_1</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="EndEvent_1" />
  </bpmn:process>
</bpmn:definitions>'''

    parser = BPMNParser(test_xml)
    start = parser.get_start_event()

    if not start or start['id'] != 'StartEvent_1':
        raise Exception("Parser failed to extract start event")


def verify_executor():
    """Verify workflow executor can be instantiated"""
    from workflow_engine.engine.executor import WorkflowExecutor

    # Just verify import and class structure
    if not hasattr(WorkflowExecutor, 'start'):
        raise Exception("Executor missing 'start' method")


def verify_api():
    """Verify API endpoints are accessible"""
    api_methods = [
        'workflow_engine.api.workflow_designer.get_workflow_list',
        'workflow_engine.api.workflow_execution.get_my_tasks',
    ]

    for method in api_methods:
        if not frappe.get_attr(method):
            raise Exception(f"API method '{method}' not found")


def verify_page():
    """Verify Workflow Designer page exists"""
    if not frappe.db.exists("Page", "workflow_designer"):
        raise Exception("Workflow Designer page not found")


def verify_permissions():
    """Verify basic permissions are set"""
    # Check if System Manager has permissions on Workflow Definition
    perms = frappe.get_all("DocPerm",
        filters={
            "parent": "Workflow Definition",
            "role": "System Manager"
        }
    )

    if not perms:
        raise Exception("System Manager permissions not set on Workflow Definition")


def verify_scheduler():
    """Verify scheduler tasks are registered"""
    from workflow_engine.hooks import scheduler_events

    if not scheduler_events:
        raise Exception("No scheduler events registered")

    if 'hourly' not in scheduler_events:
        raise Exception("Hourly scheduler events not registered")


def create_test_workflow():
    """Create a test workflow for verification"""
    print("\nCreating test workflow...")

    test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  id="Definitions_Test"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Test" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_1" name="End">
      <bpmn:incoming>Flow_1</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="EndEvent_1" />
  </bpmn:process>
</bpmn:definitions>'''

    if frappe.db.exists("Workflow Definition", "Test Workflow Verification"):
        print("Test workflow already exists, skipping...")
        return

    workflow = frappe.get_doc({
        "doctype": "Workflow Definition",
        "workflow_name": "Test Workflow Verification",
        "linked_doctype": "ToDo",
        "bpmn_xml": test_xml,
        "is_active": 0,
        "description": "Test workflow for verification"
    })

    workflow.insert(ignore_permissions=True)
    frappe.db.commit()

    print(f"✓ Test workflow created: {workflow.name}")


def test_workflow_execution():
    """Test a complete workflow execution"""
    print("\nTesting workflow execution...")

    # Create test ToDo
    todo = frappe.get_doc({
        "doctype": "ToDo",
        "description": "Test ToDo for Workflow Verification"
    })
    todo.insert(ignore_permissions=True)

    # Create test workflow instance
    if not frappe.db.exists("Workflow Definition", "Test Workflow Verification"):
        create_test_workflow()

    instance = frappe.get_doc({
        "doctype": "Workflow Instance",
        "workflow_definition": "Test Workflow Verification",
        "reference_doctype": "ToDo",
        "reference_name": todo.name
    })
    instance.insert(ignore_permissions=True)
    frappe.db.commit()

    # Execute workflow
    from workflow_engine.engine.executor import WorkflowExecutor

    executor = WorkflowExecutor(instance.name)
    executor.start()

    # Verify completion
    instance.reload()

    if instance.status != "Completed":
        raise Exception(f"Workflow did not complete. Status: {instance.status}")

    print(f"✓ Workflow execution successful: {instance.name}")

    # Cleanup
    frappe.delete_doc("Workflow Instance", instance.name, ignore_permissions=True)
    frappe.delete_doc("ToDo", todo.name, ignore_permissions=True)
    frappe.db.commit()

    print("✓ Cleanup completed")


if __name__ == "__main__":
    # For direct execution
    frappe.init(site='site_name')
    frappe.connect()
    verify_all()

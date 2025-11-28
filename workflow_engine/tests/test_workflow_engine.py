"""
Unit tests for Workflow Engine
"""

import frappe
import unittest
from workflow_engine.engine.parser import BPMNParser
from workflow_engine.engine.executor import WorkflowExecutor


class TestWorkflowEngine(unittest.TestCase):
    """Test cases for the workflow engine"""

    def setUp(self):
        """Set up test data"""
        frappe.set_user("Administrator")

        # Create test workflow definition
        self.create_test_workflow()

    def tearDown(self):
        """Clean up test data"""
        # Delete test records
        frappe.db.sql("DELETE FROM `tabWorkflow Log`")
        frappe.db.sql("DELETE FROM `tabWorkflow Variable`")
        frappe.db.sql("DELETE FROM `tabWorkflow Task`")
        frappe.db.sql("DELETE FROM `tabWorkflow Instance`")
        frappe.db.sql("DELETE FROM `tabWorkflow Definition` WHERE name = 'Test Leave Workflow'")
        frappe.db.sql("DELETE FROM `tabWorkflow Definition` WHERE name = 'Test Complex Workflow'")
        frappe.db.commit()

    def create_test_workflow(self):
        """Create a test workflow definition"""
        bpmn_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  id="Definitions_Test"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Test" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>

    <bpmn:userTask id="Task_1" name="Test Task" assignee="Administrator">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:userTask>

    <bpmn:endEvent id="EndEvent_1" name="End">
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>

    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </bpmn:process>
</bpmn:definitions>'''

        if not frappe.db.exists("Workflow Definition", "Test Leave Workflow"):
            workflow = frappe.get_doc({
                "doctype": "Workflow Definition",
                "workflow_name": "Test Leave Workflow",
                "linked_doctype": "ToDo",
                "bpmn_xml": bpmn_xml,
                "is_active": 0
            })
            workflow.insert(ignore_permissions=True)
            frappe.db.commit()

    def test_bpmn_parser(self):
        """Test BPMN XML parsing"""
        workflow = frappe.get_doc("Workflow Definition", "Test Leave Workflow")
        parser = BPMNParser(workflow.bpmn_xml)

        # Test getting start event
        start_event = parser.get_start_event()
        self.assertIsNotNone(start_event)
        self.assertEqual(start_event['id'], 'StartEvent_1')

        # Test getting end events
        end_events = parser.get_end_events()
        self.assertEqual(len(end_events), 1)
        self.assertEqual(end_events[0]['id'], 'EndEvent_1')

        # Test getting user tasks
        user_tasks = parser.get_user_tasks()
        self.assertEqual(len(user_tasks), 1)
        self.assertEqual(user_tasks[0]['id'], 'Task_1')

    def test_workflow_instance_creation(self):
        """Test creating a workflow instance"""
        # Create a test ToDo
        todo = frappe.get_doc({
            "doctype": "ToDo",
            "description": "Test Todo for Workflow"
        })
        todo.insert(ignore_permissions=True)

        # Create workflow instance
        instance = frappe.get_doc({
            "doctype": "Workflow Instance",
            "workflow_definition": "Test Leave Workflow",
            "reference_doctype": "ToDo",
            "reference_name": todo.name
        })
        instance.insert(ignore_permissions=True)

        # Verify instance
        self.assertEqual(instance.status, "Pending")
        self.assertIsNotNone(instance.started_on)
        self.assertEqual(instance.started_by, "Administrator")


    def test_workflow_execution(self):
        """Test workflow execution flow"""
        # Create a test ToDo
        todo = frappe.get_doc({
            "doctype": "ToDo",
            "description": "Test Todo for Workflow Execution"
        })
        todo.insert(ignore_permissions=True)

        # Create workflow instance
        instance = frappe.get_doc({
            "doctype": "Workflow Instance",
            "workflow_definition": "Test Leave Workflow",
            "reference_doctype": "ToDo",
            "reference_name": todo.name
        })
        instance.insert(ignore_permissions=True)
        frappe.db.commit()

        # Start workflow execution
        executor = WorkflowExecutor(instance.name)
        executor.start()

        # Reload instance
        instance.reload()

        # Verify workflow started
        if instance.status == "Failed":
            print("\nWorkflow Failed. Logs:")
            for log in instance.workflow_logs:
                print(f"{log.node_id}: {log.message} ({log.status})")
        
        self.assertEqual(instance.status, "Waiting")  # Waiting on user task
        self.assertIsNotNone(instance.current_node_id)

        # Verify user task was created
        tasks = frappe.get_all("Workflow Task", filters={"workflow_instance": instance.name})
        self.assertEqual(len(tasks), 1)

        # Complete the task
        task = frappe.get_doc("Workflow Task", tasks[0].name)
        task.complete_task("Approve", "Test approval")

        # Reload instance
        instance.reload()

        # Verify workflow completed
        self.assertEqual(instance.status, "Completed")
        self.assertIsNotNone(instance.completed_on)


    def test_workflow_variables(self):
        """Test workflow variable management"""
        # Create a test instance
        todo = frappe.get_doc({
            "doctype": "ToDo",
            "description": "Test Todo for Variables"
        })
        todo.insert(ignore_permissions=True)

        instance = frappe.get_doc({
            "doctype": "Workflow Instance",
            "workflow_definition": "Test Leave Workflow",
            "reference_doctype": "ToDo",
            "reference_name": todo.name
        })
        instance.insert(ignore_permissions=True)

        # Set variables
        instance.set_variable("test_string", "Hello World", "String")
        instance.set_variable("test_int", 42, "Int")
        instance.set_variable("test_bool", True, "Boolean")

        instance.save(ignore_permissions=True)
        instance.reload()

        # Get variables
        self.assertEqual(instance.get_variable("test_string"), "Hello World")
        self.assertEqual(instance.get_variable("test_int"), 42)
        self.assertEqual(instance.get_variable("test_bool"), True)
        self.assertIsNone(instance.get_variable("nonexistent"))


    def test_complex_workflow_with_gateway(self):
        """Test complex workflow with exclusive gateway"""
        # Create complex workflow with gateway
        bpmn_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  id="Definitions_Complex"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Complex" isExecutable="true">
    <bpmn:startEvent id="Start" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>

    <bpmn:userTask id="Task_1" name="Review" assignee="Administrator">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:userTask>

    <bpmn:exclusiveGateway id="Gateway_1" name="Decision">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_Approved</bpmn:outgoing>
      <bpmn:outgoing>Flow_Rejected</bpmn:outgoing>
    </bpmn:exclusiveGateway>

    <bpmn:endEvent id="End_Approved" name="Approved">
      <bpmn:incoming>Flow_Approved</bpmn:incoming>
    </bpmn:endEvent>

    <bpmn:endEvent id="End_Rejected" name="Rejected">
      <bpmn:incoming>Flow_Rejected</bpmn:incoming>
    </bpmn:endEvent>

    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="Gateway_1" />
    <bpmn:sequenceFlow id="Flow_Approved" sourceRef="Gateway_1" targetRef="End_Approved">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">context.get_variable('task_Task_1_action') == 'Approve'</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="Flow_Rejected" sourceRef="Gateway_1" targetRef="End_Rejected">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">context.get_variable('task_Task_1_action') == 'Reject'</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
  </bpmn:process>
</bpmn:definitions>'''

        # Create workflow definition
        if frappe.db.exists("Workflow Definition", "Test Complex Workflow"):
            frappe.delete_doc("Workflow Definition", "Test Complex Workflow")

        workflow = frappe.get_doc({
            "doctype": "Workflow Definition",
            "workflow_name": "Test Complex Workflow",
            "linked_doctype": "ToDo",
            "bpmn_xml": bpmn_xml,
            "is_active": 0
        })
        workflow.insert(ignore_permissions=True)
        frappe.db.commit()

        # Create and execute workflow
        todo = frappe.get_doc({
            "doctype": "ToDo",
            "description": "Test Complex Workflow"
        })
        todo.insert(ignore_permissions=True)

        instance = frappe.get_doc({
            "doctype": "Workflow Instance",
            "workflow_definition": "Test Complex Workflow",
            "reference_doctype": "ToDo",
            "reference_name": todo.name
        })
        instance.insert(ignore_permissions=True)
        frappe.db.commit()

        # Start workflow
        executor = WorkflowExecutor(instance.name)
        executor.start()
        
        # Reload instance
        instance.reload()
        if instance.status == "Failed":
            print("\nComplex Workflow Failed. Logs:")
            for log in instance.workflow_logs:
                print(f"{log.node_id}: {log.message} ({log.status})")

        # Get task and approve
        tasks = frappe.get_all("Workflow Task", filters={"workflow_instance": instance.name})
        task = frappe.get_doc("Workflow Task", tasks[0].name)
        task.complete_task("Approve")

        # Reload and verify
        instance.reload()
        self.assertEqual(instance.status, "Completed")


def run_tests():
    """Run all workflow engine tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWorkflowEngine)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == "__main__":
    run_tests()

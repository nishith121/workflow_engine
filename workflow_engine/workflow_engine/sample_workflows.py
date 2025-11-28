import frappe

def create_sample_workflows():
    """Create sample workflows for demonstration purposes"""
    
    samples = [
        {
            "workflow_name": "Purchase Order Approval",
            "description": "Simple linear approval workflow for purchase orders",
            "linked_doctype": "ToDo",
            "is_active": 0,
            "bpmn_xml": get_po_approval_workflow()
        },
        {
            "workflow_name": "Task Assignment with Conditional Approval",
            "description": "Conditional approval based on priority",
            "linked_doctype": "ToDo",
            "is_active": 0,
            "bpmn_xml": get_leave_approval_workflow()
        },
        {
            "workflow_name": "User Onboarding Process",
            "description": "Parallel tasks for different departments",
            "linked_doctype": "User",
            "is_active": 0,
            "bpmn_xml": get_onboarding_workflow()
        },
        {
            "workflow_name": "Document Processing Workflow",
            "description": "Complex workflow with multiple gateways and paths",
            "linked_doctype": "ToDo",
            "is_active": 0,
            "bpmn_xml": get_sales_order_workflow()
        }
    ]
    
    for sample in samples:
        # Check if workflow already exists
        if frappe.db.exists("Workflow Definition", {"workflow_name": sample["workflow_name"]}):
            print(f"Workflow '{sample['workflow_name']}' already exists, skipping...")
            continue
        
        # Create new workflow definition
        doc = frappe.get_doc({
            "doctype": "Workflow Definition",
            "workflow_name": sample["workflow_name"],
            "description": sample["description"],
            "linked_doctype": sample["linked_doctype"],
            "is_active": sample["is_active"],
            "bpmn_xml": sample["bpmn_xml"],
            "version": 1
        })
        doc.insert(ignore_permissions=True)
        print(f"Created sample workflow: {sample['workflow_name']}")
    
    frappe.db.commit()
    print("\nAll sample workflows created successfully!")


def get_po_approval_workflow():
    """Simple linear approval workflow"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_PO_Approval"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_PO_Approval" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="PO Created">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:userTask id="Task_Review" name="Review Purchase Order" assignee="Accounts Manager">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:userTask id="Task_Approve" name="Approve Purchase Order" assignee="Purchase Manager">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:scriptTask id="Task_Send_Email" name="Send Confirmation Email">
      <bpmn:incoming>Flow_3</bpmn:incoming>
      <bpmn:outgoing>Flow_4</bpmn:outgoing>
    </bpmn:scriptTask>
    
    <bpmn:endEvent id="EndEvent_1" name="PO Approved">
      <bpmn:incoming>Flow_4</bpmn:incoming>
    </bpmn:endEvent>
    
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_Review" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Review" targetRef="Task_Approve" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_Approve" targetRef="Task_Send_Email" />
    <bpmn:sequenceFlow id="Flow_4" sourceRef="Task_Send_Email" targetRef="EndEvent_1" />
  </bpmn:process>
  
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_PO_Approval">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="152" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Review_di" bpmnElement="Task_Review">
        <dc:Bounds x="240" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Approve_di" bpmnElement="Task_Approve">
        <dc:Bounds x="390" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Send_Email_di" bpmnElement="Task_Send_Email">
        <dc:Bounds x="540" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="692" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="188" y="120" />
        <di:waypoint x="240" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="340" y="120" />
        <di:waypoint x="390" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_3_di" bpmnElement="Flow_3">
        <di:waypoint x="490" y="120" />
        <di:waypoint x="540" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_4_di" bpmnElement="Flow_4">
        <di:waypoint x="640" y="120" />
        <di:waypoint x="692" y="120" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>'''


def get_leave_approval_workflow():
    """Workflow with conditional gateway"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_Leave"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Leave" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Leave Applied">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:exclusiveGateway id="Gateway_Duration" name="Duration Check">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_Short</bpmn:outgoing>
      <bpmn:outgoing>Flow_Long</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    
    <bpmn:userTask id="Task_Manager_Approval" name="Manager Approval" assignee="Reports To">
      <bpmn:incoming>Flow_Short</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:userTask id="Task_HR_Approval" name="HR Approval" assignee="HR Manager">
      <bpmn:incoming>Flow_Long</bpmn:incoming>
      <bpmn:outgoing>Flow_4</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:exclusiveGateway id="Gateway_Merge">
      <bpmn:incoming>Flow_3</bpmn:incoming>
      <bpmn:incoming>Flow_4</bpmn:incoming>
      <bpmn:outgoing>Flow_5</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    
    <bpmn:scriptTask id="Task_Update_Calendar" name="Update Leave Calendar">
      <bpmn:incoming>Flow_5</bpmn:incoming>
      <bpmn:outgoing>Flow_6</bpmn:outgoing>
    </bpmn:scriptTask>
    
    <bpmn:endEvent id="EndEvent_1" name="Leave Approved">
      <bpmn:incoming>Flow_6</bpmn:incoming>
    </bpmn:endEvent>
    
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Gateway_Duration" />
    <bpmn:sequenceFlow id="Flow_Short" name="&lt;= 3 days" sourceRef="Gateway_Duration" targetRef="Task_Manager_Approval" />
    <bpmn:sequenceFlow id="Flow_Long" name="&gt; 3 days" sourceRef="Gateway_Duration" targetRef="Task_HR_Approval" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_Manager_Approval" targetRef="Gateway_Merge" />
    <bpmn:sequenceFlow id="Flow_4" sourceRef="Task_HR_Approval" targetRef="Gateway_Merge" />
    <bpmn:sequenceFlow id="Flow_5" sourceRef="Gateway_Merge" targetRef="Task_Update_Calendar" />
    <bpmn:sequenceFlow id="Flow_6" sourceRef="Task_Update_Calendar" targetRef="EndEvent_1" />
  </bpmn:process>
  
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_Leave">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="152" y="152" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Duration_di" bpmnElement="Gateway_Duration" isMarkerVisible="true">
        <dc:Bounds x="245" y="145" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Manager_Approval_di" bpmnElement="Task_Manager_Approval">
        <dc:Bounds x="360" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_HR_Approval_di" bpmnElement="Task_HR_Approval">
        <dc:Bounds x="360" y="210" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Merge_di" bpmnElement="Gateway_Merge" isMarkerVisible="true">
        <dc:Bounds x="525" y="145" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Update_Calendar_di" bpmnElement="Task_Update_Calendar">
        <dc:Bounds x="640" y="130" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="792" y="152" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="188" y="170" />
        <di:waypoint x="245" y="170" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_Short_di" bpmnElement="Flow_Short">
        <di:waypoint x="270" y="145" />
        <di:waypoint x="270" y="120" />
        <di:waypoint x="360" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_Long_di" bpmnElement="Flow_Long">
        <di:waypoint x="270" y="195" />
        <di:waypoint x="270" y="250" />
        <di:waypoint x="360" y="250" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_3_di" bpmnElement="Flow_3">
        <di:waypoint x="460" y="120" />
        <di:waypoint x="550" y="120" />
        <di:waypoint x="550" y="145" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_4_di" bpmnElement="Flow_4">
        <di:waypoint x="460" y="250" />
        <di:waypoint x="550" y="250" />
        <di:waypoint x="550" y="195" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_5_di" bpmnElement="Flow_5">
        <di:waypoint x="575" y="170" />
        <di:waypoint x="640" y="170" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_6_di" bpmnElement="Flow_6">
        <di:waypoint x="740" y="170" />
        <di:waypoint x="792" y="170" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>'''


def get_onboarding_workflow():
    """Workflow with parallel gateway"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_Onboarding"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Onboarding" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="New Employee Joined">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:parallelGateway id="Gateway_Split">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_HR</bpmn:outgoing>
      <bpmn:outgoing>Flow_IT</bpmn:outgoing>
    </bpmn:parallelGateway>
    
    <bpmn:userTask id="Task_HR_Setup" name="HR Onboarding Setup" assignee="HR Manager">
      <bpmn:incoming>Flow_HR</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:userTask id="Task_IT_Setup" name="IT Account Setup" assignee="System Manager">
      <bpmn:incoming>Flow_IT</bpmn:incoming>
      <bpmn:outgoing>Flow_4</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:parallelGateway id="Gateway_Join">
      <bpmn:incoming>Flow_3</bpmn:incoming>
      <bpmn:incoming>Flow_4</bpmn:incoming>
      <bpmn:outgoing>Flow_5</bpmn:outgoing>
    </bpmn:parallelGateway>
    
    <bpmn:userTask id="Task_Manager_Welcome" name="Manager Welcome Meeting" assignee="Reports To">
      <bpmn:incoming>Flow_5</bpmn:incoming>
      <bpmn:outgoing>Flow_6</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:scriptTask id="Task_Send_Welcome" name="Send Welcome Email">
      <bpmn:incoming>Flow_6</bpmn:incoming>
      <bpmn:outgoing>Flow_7</bpmn:outgoing>
    </bpmn:scriptTask>
    
    <bpmn:endEvent id="EndEvent_1" name="Onboarding Complete">
      <bpmn:incoming>Flow_7</bpmn:incoming>
    </bpmn:endEvent>
    
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Gateway_Split" />
    <bpmn:sequenceFlow id="Flow_HR" sourceRef="Gateway_Split" targetRef="Task_HR_Setup" />
    <bpmn:sequenceFlow id="Flow_IT" sourceRef="Gateway_Split" targetRef="Task_IT_Setup" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_HR_Setup" targetRef="Gateway_Join" />
    <bpmn:sequenceFlow id="Flow_4" sourceRef="Task_IT_Setup" targetRef="Gateway_Join" />
    <bpmn:sequenceFlow id="Flow_5" sourceRef="Gateway_Join" targetRef="Task_Manager_Welcome" />
    <bpmn:sequenceFlow id="Flow_6" sourceRef="Task_Manager_Welcome" targetRef="Task_Send_Welcome" />
    <bpmn:sequenceFlow id="Flow_7" sourceRef="Task_Send_Welcome" targetRef="EndEvent_1" />
  </bpmn:process>
  
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_Onboarding">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="152" y="152" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Split_di" bpmnElement="Gateway_Split">
        <dc:Bounds x="245" y="145" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_HR_Setup_di" bpmnElement="Task_HR_Setup">
        <dc:Bounds x="360" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_IT_Setup_di" bpmnElement="Task_IT_Setup">
        <dc:Bounds x="360" y="210" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Join_di" bpmnElement="Gateway_Join">
        <dc:Bounds x="525" y="145" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Manager_Welcome_di" bpmnElement="Task_Manager_Welcome">
        <dc:Bounds x="640" y="130" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Send_Welcome_di" bpmnElement="Task_Send_Welcome">
        <dc:Bounds x="800" y="130" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="962" y="152" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="188" y="170" />
        <di:waypoint x="245" y="170" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_HR_di" bpmnElement="Flow_HR">
        <di:waypoint x="270" y="145" />
        <di:waypoint x="270" y="120" />
        <di:waypoint x="360" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_IT_di" bpmnElement="Flow_IT">
        <di:waypoint x="270" y="195" />
        <di:waypoint x="270" y="250" />
        <di:waypoint x="360" y="250" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_3_di" bpmnElement="Flow_3">
        <di:waypoint x="460" y="120" />
        <di:waypoint x="550" y="120" />
        <di:waypoint x="550" y="145" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_4_di" bpmnElement="Flow_4">
        <di:waypoint x="460" y="250" />
        <di:waypoint x="550" y="250" />
        <di:waypoint x="550" y="195" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_5_di" bpmnElement="Flow_5">
        <di:waypoint x="575" y="170" />
        <di:waypoint x="640" y="170" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_6_di" bpmnElement="Flow_6">
        <di:waypoint x="740" y="170" />
        <di:waypoint x="800" y="170" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_7_di" bpmnElement="Flow_7">
        <di:waypoint x="900" y="170" />
        <di:waypoint x="962" y="170" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>'''


def get_sales_order_workflow():
    """Complex workflow with multiple features"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_Sales"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_Sales" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Sales Order Created">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:userTask id="Task_Review_Order" name="Review Order Details" assignee="Sales Manager">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:exclusiveGateway id="Gateway_Credit_Check" name="Credit Check">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_Approved</bpmn:outgoing>
      <bpmn:outgoing>Flow_Review</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    
    <bpmn:userTask id="Task_Credit_Review" name="Credit Review" assignee="Accounts Manager">
      <bpmn:incoming>Flow_Review</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:exclusiveGateway id="Gateway_Merge">
      <bpmn:incoming>Flow_Approved</bpmn:incoming>
      <bpmn:incoming>Flow_3</bpmn:incoming>
      <bpmn:outgoing>Flow_4</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    
    <bpmn:parallelGateway id="Gateway_Parallel_Split">
      <bpmn:incoming>Flow_4</bpmn:incoming>
      <bpmn:outgoing>Flow_Inventory</bpmn:outgoing>
      <bpmn:outgoing>Flow_Shipping</bpmn:outgoing>
    </bpmn:parallelGateway>
    
    <bpmn:userTask id="Task_Check_Inventory" name="Check Inventory" assignee="Stock Manager">
      <bpmn:incoming>Flow_Inventory</bpmn:incoming>
      <bpmn:outgoing>Flow_5</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:userTask id="Task_Arrange_Shipping" name="Arrange Shipping" assignee="Logistics Manager">
      <bpmn:incoming>Flow_Shipping</bpmn:incoming>
      <bpmn:outgoing>Flow_6</bpmn:outgoing>
    </bpmn:userTask>
    
    <bpmn:parallelGateway id="Gateway_Parallel_Join">
      <bpmn:incoming>Flow_5</bpmn:incoming>
      <bpmn:incoming>Flow_6</bpmn:incoming>
      <bpmn:outgoing>Flow_7</bpmn:outgoing>
    </bpmn:parallelGateway>
    
    <bpmn:scriptTask id="Task_Create_Invoice" name="Create Sales Invoice">
      <bpmn:incoming>Flow_7</bpmn:incoming>
      <bpmn:outgoing>Flow_8</bpmn:outgoing>
    </bpmn:scriptTask>
    
    <bpmn:scriptTask id="Task_Send_Notification" name="Send Customer Notification">
      <bpmn:incoming>Flow_8</bpmn:incoming>
      <bpmn:outgoing>Flow_9</bpmn:outgoing>
    </bpmn:scriptTask>
    
    <bpmn:endEvent id="EndEvent_1" name="Order Processed">
      <bpmn:incoming>Flow_9</bpmn:incoming>
    </bpmn:endEvent>
    
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_Review_Order" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Review_Order" targetRef="Gateway_Credit_Check" />
    <bpmn:sequenceFlow id="Flow_Approved" name="Good Credit" sourceRef="Gateway_Credit_Check" targetRef="Gateway_Merge" />
    <bpmn:sequenceFlow id="Flow_Review" name="Needs Review" sourceRef="Gateway_Credit_Check" targetRef="Task_Credit_Review" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_Credit_Review" targetRef="Gateway_Merge" />
    <bpmn:sequenceFlow id="Flow_4" sourceRef="Gateway_Merge" targetRef="Gateway_Parallel_Split" />
    <bpmn:sequenceFlow id="Flow_Inventory" sourceRef="Gateway_Parallel_Split" targetRef="Task_Check_Inventory" />
    <bpmn:sequenceFlow id="Flow_Shipping" sourceRef="Gateway_Parallel_Split" targetRef="Task_Arrange_Shipping" />
    <bpmn:sequenceFlow id="Flow_5" sourceRef="Task_Check_Inventory" targetRef="Gateway_Parallel_Join" />
    <bpmn:sequenceFlow id="Flow_6" sourceRef="Task_Arrange_Shipping" targetRef="Gateway_Parallel_Join" />
    <bpmn:sequenceFlow id="Flow_7" sourceRef="Gateway_Parallel_Join" targetRef="Task_Create_Invoice" />
    <bpmn:sequenceFlow id="Flow_8" sourceRef="Task_Create_Invoice" targetRef="Task_Send_Notification" />
    <bpmn:sequenceFlow id="Flow_9" sourceRef="Task_Send_Notification" targetRef="EndEvent_1" />
  </bpmn:process>
  
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_Sales">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="152" y="212" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Review_Order_di" bpmnElement="Task_Review_Order">
        <dc:Bounds x="240" y="190" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Credit_Check_di" bpmnElement="Gateway_Credit_Check" isMarkerVisible="true">
        <dc:Bounds x="395" y="205" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Credit_Review_di" bpmnElement="Task_Credit_Review">
        <dc:Bounds x="500" y="290" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Merge_di" bpmnElement="Gateway_Merge" isMarkerVisible="true">
        <dc:Bounds x="655" y="205" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Parallel_Split_di" bpmnElement="Gateway_Parallel_Split">
        <dc:Bounds x="765" y="205" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Check_Inventory_di" bpmnElement="Task_Check_Inventory">
        <dc:Bounds x="880" y="120" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Arrange_Shipping_di" bpmnElement="Task_Arrange_Shipping">
        <dc:Bounds x="880" y="280" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_Parallel_Join_di" bpmnElement="Gateway_Parallel_Join">
        <dc:Bounds x="1045" y="205" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Create_Invoice_di" bpmnElement="Task_Create_Invoice">
        <dc:Bounds x="1160" y="190" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_Send_Notification_di" bpmnElement="Task_Send_Notification">
        <dc:Bounds x="1320" y="190" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="1482" y="212" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="188" y="230" />
        <di:waypoint x="240" y="230" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="340" y="230" />
        <di:waypoint x="395" y="230" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_Approved_di" bpmnElement="Flow_Approved">
        <di:waypoint x="445" y="230" />
        <di:waypoint x="655" y="230" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_Review_di" bpmnElement="Flow_Review">
        <di:waypoint x="420" y="255" />
        <di:waypoint x="420" y="330" />
        <di:waypoint x="500" y="330" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_3_di" bpmnElement="Flow_3">
        <di:waypoint x="600" y="330" />
        <di:waypoint x="680" y="330" />
        <di:waypoint x="680" y="255" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_4_di" bpmnElement="Flow_4">
        <di:waypoint x="705" y="230" />
        <di:waypoint x="765" y="230" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_Inventory_di" bpmnElement="Flow_Inventory">
        <di:waypoint x="790" y="205" />
        <di:waypoint x="790" y="160" />
        <di:waypoint x="880" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_Shipping_di" bpmnElement="Flow_Shipping">
        <di:waypoint x="790" y="255" />
        <di:waypoint x="790" y="320" />
        <di:waypoint x="880" y="320" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_5_di" bpmnElement="Flow_5">
        <di:waypoint x="980" y="160" />
        <di:waypoint x="1070" y="160" />
        <di:waypoint x="1070" y="205" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_6_di" bpmnElement="Flow_6">
        <di:waypoint x="980" y="320" />
        <di:waypoint x="1070" y="320" />
        <di:waypoint x="1070" y="255" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_7_di" bpmnElement="Flow_7">
        <di:waypoint x="1095" y="230" />
        <di:waypoint x="1160" y="230" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_8_di" bpmnElement="Flow_8">
        <di:waypoint x="1260" y="230" />
        <di:waypoint x="1320" y="230" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_9_di" bpmnElement="Flow_9">
        <di:waypoint x="1420" y="230" />
        <di:waypoint x="1482" y="230" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>'''

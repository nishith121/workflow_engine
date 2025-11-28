import frappe
from frappe.model.document import Document
from lxml import etree


class WorkflowDefinition(Document):
    def before_save(self):
        """Parse BPMN XML and extract metadata before saving"""
        self.parse_bpmn_xml()
        self.last_modified_by = frappe.session.user

    def before_insert(self):
        """Set created_by on first save"""
        self.created_by = frappe.session.user

    def parse_bpmn_xml(self):
        """Parse BPMN XML and extract start/end events"""
        if not self.bpmn_xml:
            return

        try:
            # Parse XML
            root = etree.fromstring(self.bpmn_xml.encode('utf-8'))

            # Define BPMN namespace
            namespaces = {
                'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
                'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
                'dc': 'http://www.omg.org/spec/DD/20100524/DC',
                'di': 'http://www.omg.org/spec/DD/20100524/DI'
            }

            # Find start event
            start_events = root.xpath('//bpmn:startEvent', namespaces=namespaces)
            if start_events:
                self.start_event_id = start_events[0].get('id')

            # Find end event
            end_events = root.xpath('//bpmn:endEvent', namespaces=namespaces)
            if end_events:
                self.end_event_id = end_events[0].get('id')

        except Exception as e:
            frappe.throw(f"Invalid BPMN XML: {str(e)}")

    def validate(self):
        """Validate workflow definition"""
        # Ensure only one active version per doctype
        if self.is_active:
            existing_active = frappe.db.exists({
                'doctype': 'Workflow Definition',
                'linked_doctype': self.linked_doctype,
                'is_active': 1,
                'name': ['!=', self.name]
            })

            if existing_active:
                frappe.throw(f"An active workflow already exists for {self.linked_doctype}. Please deactivate it first.")

        # Validate BPMN XML
        if self.bpmn_xml:
            try:
                etree.fromstring(self.bpmn_xml.encode('utf-8'))
            except Exception as e:
                frappe.throw(f"Invalid BPMN XML: {str(e)}")

        # Validate JSON config
        if self.workflow_config:
            try:
                import json
                json.loads(self.workflow_config)
            except Exception as e:
                frappe.throw(f"Invalid JSON configuration: {str(e)}")

    def get_node_by_id(self, node_id):
        """Get BPMN node by ID"""
        if not self.bpmn_xml:
            return None

        try:
            root = etree.fromstring(self.bpmn_xml.encode('utf-8'))
            namespaces = {
                'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
            }

            # Find node with matching ID
            nodes = root.xpath(f'//*[@id="{node_id}"]', namespaces=namespaces)
            if nodes:
                return nodes[0]

        except Exception as e:
            frappe.log_error(f"Error getting node {node_id}: {str(e)}")

        return None

    def get_outgoing_flows(self, node_id):
        """Get outgoing sequence flows from a node"""
        node = self.get_node_by_id(node_id)
        if node is None:
            return []

        outgoing_flows = []
        namespaces = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
        }

        # Get outgoing flow references
        outgoing_refs = node.xpath('./bpmn:outgoing', namespaces=namespaces)

        # Get the actual flow elements
        root = etree.fromstring(self.bpmn_xml.encode('utf-8'))
        for ref in outgoing_refs:
            flow_id = ref.text
            flows = root.xpath(f'//bpmn:sequenceFlow[@id="{flow_id}"]', namespaces=namespaces)
            if flows:
                outgoing_flows.append({
                    'id': flows[0].get('id'),
                    'sourceRef': flows[0].get('sourceRef'),
                    'targetRef': flows[0].get('targetRef'),
                    'name': flows[0].get('name', ''),
                    'condition': flows[0].xpath('./bpmn:conditionExpression', namespaces=namespaces)
                })

        return outgoing_flows

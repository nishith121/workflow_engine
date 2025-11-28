"""
BPMN XML Parser
Parses BPMN 2.0 XML and extracts workflow elements
"""

import frappe
from lxml import etree
from typing import Dict, List, Optional, Any
import html


class BPMNParser:
    """Parser for BPMN 2.0 XML documents"""

    BPMN_NAMESPACE = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
    NAMESPACES = {
        'bpmn': BPMN_NAMESPACE,
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
        'dc': 'http://www.omg.org/spec/DD/20100524/DC',
        'di': 'http://www.omg.org/spec/DD/20100524/DI'
    }

    def __init__(self, bpmn_xml: str):
        """
        Initialize parser with BPMN XML string

        Args:
            bpmn_xml: BPMN 2.0 XML string
        """
        self.bpmn_xml = html.unescape(bpmn_xml) if bpmn_xml else ""
        self.root = None
        self.process = None
        self.parse()

    def parse(self):
        """Parse BPMN XML"""
        try:
            self.root = etree.fromstring(self.bpmn_xml.encode('utf-8'))

            # Get the process element
            processes = self.root.xpath('//bpmn:process', namespaces=self.NAMESPACES)
            if processes:
                self.process = processes[0]
            else:
                frappe.throw("No process found in BPMN XML")

        except Exception as e:
            frappe.throw(f"Error parsing BPMN XML: {str(e)}")

    def get_start_event(self) -> Optional[Dict[str, Any]]:
        """Get the start event of the workflow"""
        if not self.process:
            return None

        start_events = self.process.xpath('./bpmn:startEvent', namespaces=self.NAMESPACES)
        if start_events:
            return self._parse_element(start_events[0])

        return None

    def get_end_events(self) -> List[Dict[str, Any]]:
        """Get all end events of the workflow"""
        if not self.process:
            return []

        end_events = self.process.xpath('./bpmn:endEvent', namespaces=self.NAMESPACES)
        return [self._parse_element(e) for e in end_events]

    def get_element_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow element by ID

        Args:
            element_id: ID of the element

        Returns:
            Dictionary containing element details
        """
        if not self.root:
            return None

        elements = self.root.xpath(f'//*[@id="{element_id}"]', namespaces=self.NAMESPACES)
        if elements:
            return self._parse_element(elements[0])

        return None

    def get_outgoing_flows(self, element_id: str) -> List[Dict[str, Any]]:
        """
        Get outgoing sequence flows from an element

        Args:
            element_id: ID of the source element

        Returns:
            List of sequence flow dictionaries
        """
        element = self.get_element_by_id(element_id)
        if not element or 'outgoing' not in element:
            return []

        flows = []
        for flow_id in element['outgoing']:
            flow = self.get_sequence_flow(flow_id)
            if flow:
                flows.append(flow)

        return flows

    def get_sequence_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sequence flow by ID

        Args:
            flow_id: ID of the sequence flow

        Returns:
            Dictionary containing flow details
        """
        if not self.process:
            return None

        flows = self.process.xpath(f'./bpmn:sequenceFlow[@id="{flow_id}"]', namespaces=self.NAMESPACES)
        if flows:
            flow = flows[0]

            # Get condition expression if exists
            condition = None
            condition_expr = flow.xpath('./bpmn:conditionExpression', namespaces=self.NAMESPACES)
            if condition_expr:
                condition = condition_expr[0].text

            return {
                'id': flow.get('id'),
                'name': flow.get('name', ''),
                'sourceRef': flow.get('sourceRef'),
                'targetRef': flow.get('targetRef'),
                'condition': condition
            }

        return None

    def get_user_tasks(self) -> List[Dict[str, Any]]:
        """Get all user tasks in the workflow"""
        if not self.process:
            return []

        tasks = self.process.xpath('./bpmn:userTask', namespaces=self.NAMESPACES)
        return [self._parse_element(t) for t in tasks]

    def get_script_tasks(self) -> List[Dict[str, Any]]:
        """Get all script tasks in the workflow"""
        if not self.process:
            return []

        tasks = self.process.xpath('./bpmn:scriptTask', namespaces=self.NAMESPACES)
        return [self._parse_element(t) for t in tasks]

    def get_service_tasks(self) -> List[Dict[str, Any]]:
        """Get all service tasks in the workflow"""
        if not self.process:
            return []

        tasks = self.process.xpath('./bpmn:serviceTask', namespaces=self.NAMESPACES)
        return [self._parse_element(t) for t in tasks]

    def get_exclusive_gateways(self) -> List[Dict[str, Any]]:
        """Get all exclusive gateways (XOR)"""
        if not self.process:
            return []

        gateways = self.process.xpath('./bpmn:exclusiveGateway', namespaces=self.NAMESPACES)
        return [self._parse_element(g) for g in gateways]

    def get_parallel_gateways(self) -> List[Dict[str, Any]]:
        """Get all parallel gateways (AND)"""
        if not self.process:
            return []

        gateways = self.process.xpath('./bpmn:parallelGateway', namespaces=self.NAMESPACES)
        return [self._parse_element(g) for g in gateways]

    def get_timer_events(self) -> List[Dict[str, Any]]:
        """Get all timer events"""
        if not self.process:
            return []

        # Intermediate timer events
        timer_events = self.process.xpath('./bpmn:intermediateCatchEvent[bpmn:timerEventDefinition]',
                                          namespaces=self.NAMESPACES)

        return [self._parse_element(t) for t in timer_events]

    def _parse_element(self, element) -> Dict[str, Any]:
        """
        Parse a BPMN element into a dictionary

        Args:
            element: lxml element object

        Returns:
            Dictionary containing element details
        """
        # Get basic attributes
        result = {
            'id': element.get('id'),
            'name': element.get('name', ''),
            'type': self._get_element_type(element),
        }

        # Get incoming flows
        incoming = element.xpath('./bpmn:incoming', namespaces=self.NAMESPACES)
        result['incoming'] = [i.text for i in incoming]

        # Get outgoing flows
        outgoing = element.xpath('./bpmn:outgoing', namespaces=self.NAMESPACES)
        result['outgoing'] = [o.text for o in outgoing]

        # Parse type-specific attributes
        if result['type'] == 'userTask':
            result.update(self._parse_user_task(element))
        elif result['type'] == 'scriptTask':
            result.update(self._parse_script_task(element))
        elif result['type'] == 'serviceTask':
            result.update(self._parse_service_task(element))
        elif result['type'] in ['exclusiveGateway', 'parallelGateway']:
            result.update(self._parse_gateway(element))
        elif 'timerEventDefinition' in etree.tostring(element, encoding='unicode'):
            result.update(self._parse_timer_event(element))

        return result

    def _get_element_type(self, element) -> str:
        """Get the type of BPMN element"""
        tag = element.tag
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _parse_user_task(self, element) -> Dict[str, Any]:
        """Parse user task specific attributes"""
        result = {}

        # Check for assignee
        assignee = element.get('{http://activiti.org/bpmn}assignee') or element.get('assignee')
        if assignee:
            result['assignee'] = assignee

        # Check for candidate groups/roles
        candidate_groups = element.get('{http://activiti.org/bpmn}candidateGroups') or element.get('candidateGroups')
        if candidate_groups:
            result['candidateGroups'] = candidate_groups

        # Check for due date
        due_date = element.get('{http://activiti.org/bpmn}dueDate') or element.get('dueDate')
        if due_date:
            result['dueDate'] = due_date

        # Get documentation
        documentation = element.xpath('./bpmn:documentation', namespaces=self.NAMESPACES)
        if documentation:
            result['documentation'] = documentation[0].text

        return result

    def _parse_script_task(self, element) -> Dict[str, Any]:
        """Parse script task specific attributes"""
        result = {}

        # Get script format
        script_format = element.get('scriptFormat')
        if script_format:
            result['scriptFormat'] = script_format

        # Get script content
        script = element.xpath('./bpmn:script', namespaces=self.NAMESPACES)
        if script:
            result['script'] = script[0].text

        return result

    def _parse_service_task(self, element) -> Dict[str, Any]:
        """Parse service task specific attributes"""
        result = {}

        # Get implementation (method to call)
        implementation = element.get('implementation') or element.get('{http://activiti.org/bpmn}class')
        if implementation:
            result['implementation'] = implementation

        return result

    def _parse_gateway(self, element) -> Dict[str, Any]:
        """Parse gateway specific attributes"""
        result = {}

        # Get default flow
        default_flow = element.get('default')
        if default_flow:
            result['default'] = default_flow

        return result

    def _parse_timer_event(self, element) -> Dict[str, Any]:
        """Parse timer event specific attributes"""
        result = {}

        # Get timer definition
        timer_def = element.xpath('./bpmn:timerEventDefinition', namespaces=self.NAMESPACES)
        if timer_def:
            timer = timer_def[0]

            # Check for time duration
            duration = timer.xpath('./bpmn:timeDuration', namespaces=self.NAMESPACES)
            if duration:
                result['timeDuration'] = duration[0].text

            # Check for time date
            date = timer.xpath('./bpmn:timeDate', namespaces=self.NAMESPACES)
            if date:
                result['timeDate'] = date[0].text

            # Check for time cycle
            cycle = timer.xpath('./bpmn:timeCycle', namespaces=self.NAMESPACES)
            if cycle:
                result['timeCycle'] = cycle[0].text

        return result

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the BPMN workflow

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check for start event
        start = self.get_start_event()
        if not start:
            errors.append("Workflow must have a start event")

        # Check for end event
        ends = self.get_end_events()
        if not ends:
            errors.append("Workflow must have at least one end event")

        # Check all elements have valid connections
        # (This is a simplified check - full validation would be more complex)

        return len(errors) == 0, errors

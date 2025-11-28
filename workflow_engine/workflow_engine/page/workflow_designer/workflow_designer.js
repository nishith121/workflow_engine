frappe.pages['workflow_designer'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Workflow Designer',
        single_column: true
    });

    frappe.workflow_designer = new WorkflowDesigner(page);
};

var WorkflowDesigner = function(page) {
    var self = this;
    self.page = page;
    self.wrapper = $(self.page.body);
    self.bpmnModeler = null;
    self.currentWorkflow = null;
    self.currentXML = null;

    self.make();
};

WorkflowDesigner.prototype.make = function() {
    var self = this;
    
    $(self.page.body).html(frappe.render_template('workflow_designer'));
    
    self.loadBpmnLibraries().then(function() {
        self.setupBpmnModeler();
        self.setupEventListeners();
        self.createNewDiagram();
    });
};

WorkflowDesigner.prototype.loadBpmnLibraries = function() {
    return new Promise(function(resolve, reject) {
        if (window.BpmnJS) {
            resolve();
            return;
        }

        var script = document.createElement('script');
        script.src = 'https://unpkg.com/bpmn-js@11.5.0/dist/bpmn-modeler.development.js';
        script.onload = function() {
            console.log('BPMN.js loaded successfully');
            resolve();
        };
        script.onerror = function() {
            frappe.msgprint('Failed to load BPMN.js library');
            reject();
        };
        document.head.appendChild(script);

        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/bpmn-js@11.5.0/dist/assets/diagram-js.css';
        document.head.appendChild(link);

        var link2 = document.createElement('link');
        link2.rel = 'stylesheet';
        link2.href = 'https://unpkg.com/bpmn-js@11.5.0/dist/assets/bpmn-font/css/bpmn-embedded.css';
        document.head.appendChild(link2);
    });
};

WorkflowDesigner.prototype.setupBpmnModeler = function() {
    var self = this;
    var canvas = $('#bpmn-canvas')[0];

    self.bpmnModeler = new BpmnJS({
        container: canvas,
        keyboard: {
            bindTo: document
        }
    });

    self.bpmnModeler.on('selection.changed', function(e) {
        self.onSelectionChanged(e);
    });

    self.bpmnModeler.on('commandStack.changed', function() {
        self.onDiagramChanged();
    });
};

WorkflowDesigner.prototype.setupEventListeners = function() {
    var self = this;

    $('#new-workflow').on('click', function() {
        self.createNewDiagram();
    });

    $('#load-workflow').on('click', function() {
        self.showLoadWorkflowDialog();
    });

    $('#save-workflow').on('click', function() {
        self.saveWorkflow();
    });

    $('#export-workflow').on('click', function() {
        self.exportWorkflow();
    });

    $('#import-workflow').on('click', function() {
        self.importWorkflow();
    });

    $('#save-workflow-properties').on('click', function() {
        self.saveWorkflowProperties();
    });

    $('#help-guide').on('click', function() {
        self.showHelpGuide();
        $('#help-guide-modal').modal('show');
    });
};

WorkflowDesigner.prototype.createNewDiagram = function() {
    var self = this;
    var bpmnXML = '<?xml version="1.0" encoding="UTF-8"?>' +
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
        'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
        'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
        'id="Definitions_1" ' +
        'targetNamespace="http://bpmn.io/schema/bpmn">' +
        '<bpmn:process id="Process_1" isExecutable="true">' +
        '<bpmn:startEvent id="StartEvent_1" name="Start">' +
        '<bpmn:outgoing>Flow_1</bpmn:outgoing>' +
        '</bpmn:startEvent>' +
        '<bpmn:endEvent id="EndEvent_1" name="End">' +
        '<bpmn:incoming>Flow_1</bpmn:incoming>' +
        '</bpmn:endEvent>' +
        '<bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="EndEvent_1" />' +
        '</bpmn:process>' +
        '<bpmndi:BPMNDiagram id="BPMNDiagram_1">' +
        '<bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">' +
        '<bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">' +
        '<dc:Bounds x="173" y="102" width="36" height="36" />' +
        '</bpmndi:BPMNShape>' +
        '<bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">' +
        '<dc:Bounds x="432" y="102" width="36" height="36" />' +
        '</bpmndi:BPMNShape>' +
        '<bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">' +
        '<di:waypoint x="209" y="120" />' +
        '<di:waypoint x="432" y="120" />' +
        '</bpmndi:BPMNEdge>' +
        '</bpmndi:BPMNPlane>' +
        '</bpmndi:BPMNDiagram>' +
        '</bpmn:definitions>';

    self.bpmnModeler.importXML(bpmnXML).then(function() {
        var canvas = self.bpmnModeler.get('canvas');
        canvas.zoom('fit-viewport');

        self.currentWorkflow = null;
        self.currentXML = bpmnXML;
        self.updateUI();
    }).catch(function(err) {
        console.error('Error creating diagram:', err);
        frappe.msgprint('Error creating new diagram');
    });
};

WorkflowDesigner.prototype.showLoadWorkflowDialog = function() {
    var self = this;
    frappe.call({
        method: 'workflow_engine.api.workflow_designer.get_workflow_list',
        callback: function(r) {
            if (r.message) {
                self.renderWorkflowList(r.message);
                $('#load-workflow-modal').modal('show');
            }
        }
    });
};

WorkflowDesigner.prototype.renderWorkflowList = function(workflows) {
    var self = this;
    var container = $('#workflow-list');
    container.empty();

    if (workflows.length === 0) {
        container.html('<p class="text-muted">No workflows found</p>');
        return;
    }

    var table = $('<table class="table table-bordered table-hover">');
    table.append('<thead><tr><th>Name</th><th>DocType</th><th>Status</th><th>Action</th></tr></thead>');
    var tbody = $('<tbody>');

    workflows.forEach(function(wf) {
        var row = $('<tr>');
        row.append('<td>' + wf.workflow_name + '</td>');
        row.append('<td>' + wf.linked_doctype + '</td>');
        row.append('<td>' + (wf.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-secondary">Inactive</span>') + '</td>');
        row.append('<td><button class="btn btn-sm btn-primary load-wf-btn" data-name="' + wf.name + '">Load</button></td>');
        tbody.append(row);
    });

    table.append(tbody);
    container.append(table);

    container.find('.load-wf-btn').on('click', function(e) {
        var name = $(e.target).data('name');
        self.loadWorkflow(name);
        $('#load-workflow-modal').modal('hide');
    });
};

WorkflowDesigner.prototype.loadWorkflow = function(name) {
    var self = this;
    frappe.call({
        method: 'workflow_engine.api.workflow_designer.get_workflow',
        args: { name: name },
        callback: function(r) {
            if (r.message) {
                self.currentWorkflow = r.message;
                self.currentXML = r.message.bpmn_xml;

                self.bpmnModeler.importXML(self.currentXML).then(function() {
                    var canvas = self.bpmnModeler.get('canvas');
                    canvas.zoom('fit-viewport');
                    self.updateUI();
                    frappe.show_alert({ message: 'Workflow loaded successfully', indicator: 'green' });
                }).catch(function(err) {
                    console.error('Error loading workflow:', err);
                    frappe.msgprint('Error loading workflow XML');
                });
            }
        }
    });
};

WorkflowDesigner.prototype.saveWorkflow = function() {
    var self = this;
    if (!self.currentWorkflow) {
        self.showWorkflowPropertiesDialog();
        return;
    }

    self.bpmnModeler.saveXML({ format: true }).then(function(result) {
        frappe.call({
            method: 'workflow_engine.api.workflow_designer.save_workflow',
            args: {
                name: self.currentWorkflow.name,
                bpmn_xml: result.xml
            },
            callback: function(r) {
                if (r.message) {
                    self.currentWorkflow = r.message;
                    self.currentXML = result.xml;
                    frappe.show_alert({ message: 'Workflow saved successfully', indicator: 'green' });
                }
            }
        });
    });
};

WorkflowDesigner.prototype.showWorkflowPropertiesDialog = function() {
    var self = this;
    var modal = $('#workflow-properties-modal');
    var form = $('#workflow-properties-form');

    if (self.currentWorkflow) {
        form.find('[name="workflow_name"]').val(self.currentWorkflow.workflow_name);
        form.find('[name="description"]').val(self.currentWorkflow.description || '');
        form.find('[name="linked_doctype"]').val(self.currentWorkflow.linked_doctype);
        form.find('[name="is_active"]').prop('checked', self.currentWorkflow.is_active);
        form.find('[name="workflow_config"]').val(self.currentWorkflow.workflow_config || '');
    } else {
        form[0].reset();
    }

    modal.modal('show');
};

WorkflowDesigner.prototype.saveWorkflowProperties = function() {
    var self = this;
    var form = $('#workflow-properties-form');
    var data = {
        workflow_name: form.find('[name="workflow_name"]').val(),
        description: form.find('[name="description"]').val(),
        linked_doctype: form.find('[name="linked_doctype"]').val(),
        is_active: form.find('[name="is_active"]').prop('checked') ? 1 : 0,
        workflow_config: form.find('[name="workflow_config"]').val()
    };

    if (!data.workflow_name || !data.linked_doctype) {
        frappe.msgprint('Please fill all required fields');
        return;
    }

    self.bpmnModeler.saveXML({ format: true }).then(function(result) {
        data.bpmn_xml = result.xml;

        if (self.currentWorkflow) {
            data.name = self.currentWorkflow.name;
        }

        frappe.call({
            method: 'workflow_engine.api.workflow_designer.save_workflow',
            args: data,
            callback: function(r) {
                if (r.message) {
                    self.currentWorkflow = r.message;
                    self.currentXML = result.xml;
                    self.updateUI();
                    $('#workflow-properties-modal').modal('hide');
                    frappe.show_alert({ message: 'Workflow saved successfully', indicator: 'green' });
                }
            }
        });
    });
};

WorkflowDesigner.prototype.exportWorkflow = function() {
    var self = this;
    if (!self.currentXML) {
        frappe.msgprint('No workflow to export');
        return;
    }

    self.bpmnModeler.saveXML({ format: true }).then(function(result) {
        var filename = (self.currentWorkflow ? self.currentWorkflow.workflow_name : 'workflow') + '.bpmn';
        var blob = new Blob([result.xml], { type: 'application/xml' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    });
};

WorkflowDesigner.prototype.importWorkflow = function() {
    var self = this;
    var input = document.createElement('input');
    input.type = 'file';
    input.accept = '.bpmn,.xml';
    input.onchange = function(e) {
        var file = e.target.files[0];
        if (file) {
            var reader = new FileReader();
            reader.onload = function(event) {
                var xml = event.target.result;
                self.bpmnModeler.importXML(xml).then(function() {
                    var canvas = self.bpmnModeler.get('canvas');
                    canvas.zoom('fit-viewport');
                    self.currentXML = xml;
                    self.currentWorkflow = null;
                    self.updateUI();
                    frappe.show_alert({ message: 'Workflow imported successfully', indicator: 'green' });
                }).catch(function(err) {
                    console.error('Error importing workflow:', err);
                    frappe.msgprint('Error importing workflow XML');
                });
            };
            reader.readAsText(file);
        }
    };
    input.click();
};

WorkflowDesigner.prototype.onSelectionChanged = function(e) {
    var element = e.newSelection[0];

    if (!element) {
        $('#properties-panel').html('<p class="text-muted">Select an element to view properties</p>');
        return;
    }

    var html =
        '<div class="property-item">' +
            '<strong>ID:</strong> ' + element.id +
        '</div>' +
        '<div class="property-item">' +
            '<strong>Type:</strong> ' + element.type +
        '</div>' +
        '<div class="property-item">' +
            '<strong>Name:</strong> ' + (element.businessObject.name || 'N/A') +
        '</div>';

    $('#properties-panel').html(html);
};

WorkflowDesigner.prototype.onDiagramChanged = function() {
    $('#save-workflow').prop('disabled', false);
};

WorkflowDesigner.prototype.updateUI = function() {
    var self = this;
    if (self.currentWorkflow) {
        $('#current-workflow-name').text(self.currentWorkflow.workflow_name);
        $('#save-workflow').prop('disabled', false);
        $('#export-workflow').prop('disabled', false);

        var infoHtml =
            '<div class="info-item"><strong>Name:</strong> ' + self.currentWorkflow.workflow_name + '</div>' +
            '<div class="info-item"><strong>DocType:</strong> ' + self.currentWorkflow.linked_doctype + '</div>' +
            '<div class="info-item"><strong>Status:</strong> ' + (self.currentWorkflow.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-secondary">Inactive</span>') + '</div>' +
            '<div class="info-item"><strong>Version:</strong> ' + self.currentWorkflow.version + '</div>' +
            '<button class="btn btn-sm btn-default mt-2" id="edit-workflow-props">Edit Properties</button>';
        $('#workflow-info').html(infoHtml);

        $('#edit-workflow-props').on('click', function() {
            self.showWorkflowPropertiesDialog();
        });
    } else {
        $('#current-workflow-name').text('New Workflow (unsaved)');
        $('#save-workflow').prop('disabled', false);
        $('#export-workflow').prop('disabled', false);

        var infoHtml = '<p class="text-muted">New workflow - click Save to create</p>';
        $('#workflow-info').html(infoHtml);
    }
};

WorkflowDesigner.prototype.showHelpGuide = function() {
    var html = '<h3>Welcome to the Workflow Designer!</h3>' +
        '<p>Create powerful BPMN 2.0 workflows with drag-and-drop simplicity.</p>' +
        '<hr>' +
        '<h4><i class="fa fa-play-circle text-success"></i> Getting Started</h4>' +
        '<ol>' +
        '<li><strong>Create New:</strong> Click + New Workflow button</li>' +
        '<li><strong>Load Existing:</strong> Click Load to open saved workflows</li>' +
        '<li><strong>Save Your Work:</strong> Click Save button</li>' +
        '</ol>' +
        '<hr>' +
        '<h4><i class="fa fa-puzzle-piece text-primary"></i> BPMN Elements</h4>' +
        '<div class="row">' +
        '<div class="col-md-6"><h5>Events</h5><ul>' +
        '<li><strong>Start Event:</strong> Where workflow begins</li>' +
        '<li><strong>End Event:</strong> Where workflow completes</li>' +
        '</ul></div>' +
        '<div class="col-md-6"><h5>Tasks</h5><ul>' +
        '<li><strong>User Task:</strong> Requires human action</li>' +
        '<li><strong>Script Task:</strong> Automated execution</li>' +
        '</ul></div>' +
        '</div>' +
        '<div class="row mt-3">' +
        '<div class="col-md-6"><h5>Gateways</h5><ul>' +
        '<li><strong>Exclusive Gateway:</strong> Choose ONE path</li>' +
        '<li><strong>Parallel Gateway:</strong> Execute ALL paths</li>' +
        '</ul></div>' +
        '<div class="col-md-6"><h5>Connections</h5><ul>' +
        '<li><strong>Sequence Flow:</strong> Connect elements</li>' +
        '</ul></div>' +
        '</div>' +
        '<hr>' +
        '<h4><i class="fa fa-mouse-pointer text-info"></i> Editor Controls</h4>' +
        '<ul>' +
        '<li><strong>Pan:</strong> Click and drag on canvas</li>' +
        '<li><strong>Zoom:</strong> Mouse wheel</li>' +
        '<li><strong>Select:</strong> Click on element</li>' +
        '<li><strong>Delete:</strong> Select and press Delete key</li>' +
        '</ul>' +
        '<hr>' +
        '<h4><i class="fa fa-graduation-cap text-success"></i> Sample Workflows</h4>' +
        '<p>We have created 4 sample workflows to help you learn. Click <strong>Load</strong> to view them!</p>' +
        '<ol>' +
        '<li>Purchase Order Approval - Simple linear workflow</li>' +
        '<li>Task Assignment - Conditional branching</li>' +
        '<li>User Onboarding - Parallel processing</li>' +
        '<li>Document Processing - Complex workflow</li>' +
        '</ol>' +
        '<hr>' +
        '<div class="alert alert-info">' +
        '<h5><i class="fa fa-info-circle"></i> Need More Help?</h5>' +
        '<p>Check out the sample workflows by clicking Load!</p>' +
        '</div>';
    
    $('#help-guide-content').html(html);
};

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
    
    // Show loading indicator
    $(self.page.body).html('<div class="text-center p-5"><i class="fa fa-spinner fa-spin fa-3x text-primary"></i><p class="mt-3 text-muted">Loading Workflow Designer...</p></div>');
    
    self.loadBpmnLibraries()
        .then(function() {
            console.log('[Workflow Designer] Libraries loaded successfully');
            $(self.page.body).html(frappe.render_template('workflow_designer'));
            self.setupBpmnModeler();
            self.setupEventListeners();
            self.createNewDiagram();
        })
        .catch(function(err) {
            console.error('[Workflow Designer] Failed to initialize:', err);
            $(self.page.body).html(
                '<div class="alert alert-danger m-5">' +
                '<h4><i class="fa fa-exclamation-triangle"></i> Failed to Load Workflow Designer</h4>' +
                '<p>Could not load required libraries. Please check your internet connection and try refreshing the page.</p>' +
                '<p class="text-muted"><small>Error: ' + (err.message || err) + '</small></p>' +
                '<button class="btn btn-primary mt-3" onclick="location.reload()"><i class="fa fa-refresh"></i> Retry</button>' +
                '</div>'
            );
        });
};

WorkflowDesigner.prototype.loadBpmnLibraries = function() {
    return new Promise(function(resolve, reject) {
        console.log('[Workflow Designer] Starting library load...');
        var promises = [];
        
        // Load BPMN.js if not already loaded
        if (!window.BpmnJS) {
            console.log('[Workflow Designer] Loading BPMN.js from CDN...');
            promises.push(new Promise(function(bpmnResolve, bpmnReject) {
                var script = document.createElement('script');
                script.src = 'https://unpkg.com/bpmn-js@11.5.0/dist/bpmn-modeler.production.min.js';
                script.onload = function() {
                    // Give it a moment to initialize the global
                    setTimeout(function() {
                        if (window.BpmnJS) {
                            console.log('[Workflow Designer] BPMN.js loaded successfully');
                            bpmnResolve();
                        } else {
                            console.error('[Workflow Designer] Failed to load BPMN.js - global variable not available');
                            bpmnReject(new Error('BpmnJS not available after script load'));
                        }
                    }, 100);
                };
                script.onerror = function(error) {
                    console.error('[Workflow Designer] Failed to load BPMN.js script:', error);
                    bpmnReject(new Error('Failed to load BPMN.js from CDN'));
                };
                document.head.appendChild(script);

                var link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://unpkg.com/bpmn-js@11.5.0/dist/assets/diagram-js.css';
                document.head.appendChild(link);

                var link2 = document.createElement('link');
                link2.rel = 'stylesheet';
                link2.href = 'https://unpkg.com/bpmn-js@11.5.0/dist/assets/bpmn-js.css';
                document.head.appendChild(link2);
                
                var link3 = document.createElement('link');
                link3.rel = 'stylesheet';
                link3.href = 'https://unpkg.com/bpmn-js@11.5.0/dist/assets/bpmn-font/css/bpmn-embedded.css';
                document.head.appendChild(link3);
            }));
        } else {
            console.log('[Workflow Designer] BPMN.js already loaded');
        }
        
        // Load Monaco Editor if not already loaded
        if (!window.monaco) {
            console.log('[Workflow Designer] Loading Monaco Editor from CDN...');
            promises.push(new Promise(function(monacoResolve, monacoReject) {
                // Add loader script
                var loaderScript = document.createElement('script');
                loaderScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs/loader.min.js';
                loaderScript.onload = function() {
                    // Configure Monaco loader
                    require.config({ 
                        paths: { 
                            'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' 
                        }
                    });
                    
                    // Load Monaco editor
                    require(['vs/editor/editor.main'], function() {
                        console.log('[Workflow Designer] Monaco Editor loaded successfully');
                        monacoResolve();
                    });
                };
                loaderScript.onerror = function() {
                    console.warn('[Workflow Designer] Monaco Editor failed to load, will use textarea fallback');
                    monacoResolve(); // Resolve anyway to continue
                };
                document.head.appendChild(loaderScript);
            }));
        } else {
            console.log('[Workflow Designer] Monaco Editor already loaded');
        }
        
        if (promises.length === 0) {
            console.log('[Workflow Designer] All libraries already loaded');
            resolve();
        } else {
            Promise.all(promises).then(resolve).catch(reject);
        }
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
    this.currentElement = element;

    if (!element) {
        $('#properties-panel').html('<p class="text-muted">Select an element to view properties</p>');
        return;
    }

    this.renderPropertiesPanel(element);
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

// ==================== PROPERTIES PANEL RENDERERS ====================

WorkflowDesigner.prototype.renderPropertiesPanel = function(element) {
    var self = this;
    var type = element.type;
    
    // Route to specific renderer based on element type
    if (type === 'bpmn:UserTask') {
        self.renderUserTaskProperties(element);
    } else if (type === 'bpmn:ScriptTask') {
        self.renderScriptTaskProperties(element);
    } else if (type === 'bpmn:ServiceTask') {
        self.renderServiceTaskProperties(element);
    } else if (type === 'bpmn:ExclusiveGateway' || type === 'bpmn:ParallelGateway') {
        self.renderGatewayProperties(element);
    } else if (type ===  'bpmn:SequenceFlow') {
        self.renderSequenceFlowProperties(element);
    } else {
        // Default properties for other elements
        self.renderDefaultProperties(element);
    }
};

WorkflowDesigner.prototype.renderDefaultProperties = function(element) {
    var html = '<div class="properties-form">' +
        '<h6 class="mb-3">' + element.type.replace('bpmn:', '') + '</h6>' +
        '<div class="form-group">' +
            '<label>ID:</label>' +
            '<input type="text" class="form-control" value="' + element.id + '" disabled>' +
        '</div>' +
        '<div class="form-group">' +
            '<label>Name:</label>' +
            '<input type="text" class="form-control prop-name" value="' + (element.businessObject.name || '') + '">' +
        '</div>' +
        '<button class="btn btn-primary btn-sm mt-2 save-props">Save</button>' +
        '</div>';
    
    $('#properties-panel').html(html);
    
    var self = this;
    $('#properties-panel .save-props').on('click', function() {
        self.updateElementProperty(element, 'name', $('.prop-name').val());
    });
};

WorkflowDesigner.prototype.updateElementProperty = function(element, property, value) {
    var self = this;
    var modeling = self.bpmnModeler.get('modeling');
    var updates = {};
    updates[property] = value;
    modeling.updateProperties(element, updates);
    frappe.show_alert({message: 'Property updated', indicator: 'green'});
};

WorkflowDesigner.prototype.updateActivitiProperty = function(element, property, value) {
    var self = this;
    var modeling = self.bpmnModeler.get('modeling');
    var updates = {};
    updates['activiti:' + property] = value;
    modeling.updateProperties(element, updates);
};

WorkflowDesigner.prototype.renderUserTaskProperties = function(element) {
    var self = this;
    var bo = element.businessObject;
    
    // Get current values
    var name = bo.name || '';
    var assignee = bo.$attrs['activiti:assignee'] || '';
    var candidateGroups = bo.$attrs['activiti:candidateGroups'] || '';
    var dueDate = bo.$attrs['activiti:dueDate'] || '';
    
    var html = '<div class="properties-form">' +
        '<h6 class="mb-3"><i class="fa fa-user"></i> User Task Properties</h6>' +
        '<div class="form-group">' +
            '<label>Name: <span class="text-danger">*</span></label>' +
            '<input type="text" class="form-control prop-name" value="' + name + '" placeholder="e.g., Manager Approval">' +
        '</div>' +
        '<hr>' +
        '<h6 class="mb-2">Assignment</h6>' +
        '<div class="form-group">' +
            '<label>' +
                '<input type="radio" name="assignment-type" value="user" ' + (assignee ? 'checked' : '') + '> ' +
                'Assign to Specific User' +
            '</label>' +
            '<div class="mt-2 assignment-user" style="display:' + (assignee ? 'block' : 'none') + '">' +
                '<input type="text" class="form-control prop-assignee" value="' + assignee + '" placeholder="${doc.owner} or user@example.com">' +
                '<small class="form-text text-muted">Use ${doc.field_name} for dynamic assignment</small>' +
            '</div>' +
        '</div>' +
        '<div class="form-group">' +
            '<label>' +
                '<input type="radio" name="assignment-type" value="role" ' + (candidateGroups ? 'checked' : '') + '> ' +
                'Assign to Role' +
            '</label>' +
            '<div class="mt-2 assignment-role" style="display:' + (candidateGroups ? 'block' : 'none') + '">' +
                '<input type="text" class="form-control prop-role" value="' + candidateGroups + '" placeholder="e.g., Manager, Approver">' +
                '<small class="form-text text-muted">Enter Frappe role name</small>' +
            '</div>' +
        '</div>' +
        '<hr>' +
        '<div class="form-group">' +
            '<label>Due Date:</label>' +
            '<input type="text" class="form-control prop-duedate" value="' + dueDate + '" placeholder="e.g., 3d, 1w, 2h">' +
            '<small class="form-text text-muted">Examples: 3d=3 days, 1w=1 week, 2h=2 hours</small>' +
        '</div>' +
        '<button class="btn btn-primary btn-sm mt-3 save-user-task-props">Save Properties</button>' +
        '</div>';
    
    $('#properties-panel').html(html);
    
    // Event listeners
    $('input[name="assignment-type"]').on('change', function() {
        if ($(this).val() === 'user') {
            $('.assignment-user').show();
            $('.assignment-role').hide();
        } else {
            $('.assignment-user').hide();
            $('.assignment-role').show();
        }
    });
    
    $('.save-user-task-props').on('click', function() {
        var name = $('.prop-name').val();
        var assignmentType = $('input[name="assignment-type"]:checked').val();
        var assignee = $('.prop-assignee').val();
        var role = $('.prop-role').val();
        var dueDate = $('.prop-duedate').val();
        
        // Update name
        self.updateElementProperty(element, 'name', name);
        
        // Update assignment
        if (assignmentType === 'user' && assignee) {
            self.updateActivitiProperty(element, 'assignee', assignee);
            self.updateActivitiProperty(element, 'candidateGroups', '');
        } else if (assignmentType === 'role' && role) {
            self.updateActivitiProperty(element, 'candidateGroups', role);
            self.updateActivitiProperty(element, 'assignee', '');
        }
        
        // Update due date
        if (dueDate) {
            self.updateActivitiProperty(element, 'dueDate', dueDate);
        }
        
        frappe.show_alert({message: 'User task properties updated', indicator: 'green'});
    });
};

WorkflowDesigner.prototype.renderScriptTaskProperties = function(element) {
    var self = this;
    var bo = element.businessObject;
    
    var name = bo.name || '';
    var script = bo.script || '';
    
    var html = '<div class="properties-form">' +
        '<h6 class="mb-3"><i class="fa fa-code"></i> Script Task Properties</h6>' +
        '<div class="form-group">' +
            '<label>Name: <span class="text-danger">*</span></label>' +
            '<input type="text" class="form-control prop-name" value="' + name + '" placeholder="e.g., Send Email">' +
        '</div>' +
        '<hr>' +
        '<div class="form-group">' +
            '<label>Python Script:</label>' +
            '<div id="monaco-editor" style="height: 300px; border: 1px solid #ddd;"></div>' +
            '<small class="form-text text-muted">Access workflow context via: context.get_variable(), context.set_variable()</small>' +
        '</div>' +
        '<button class="btn btn-primary btn-sm mt-3 save-script-task-props">Save Properties</button>' +
        '</div>';
    
    $('#properties-panel').html(html);
    
    // Initialize Monaco Editor if available, otherwise use textarea
    var editor;
    if (window.monaco) {
        editor = monaco.editor.create(document.getElementById('monaco-editor'), {
            value: script,
            language: 'python',
            theme: 'vs-dark',
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 12
        });
    } else {
        // Fallback to textarea
        $('#monaco-editor').replaceWith('<textarea id="script-textarea" class="form-control" rows="10" style="font-family: monospace;">' + script + '</textarea>');
    }
    
    $('.save-script-task-props').on('click', function() {
        var name = $('.prop-name').val();
        var scriptContent;
        
        if (window.monaco && editor) {
            scriptContent = editor.getValue();
        } else {
            scriptContent = $('#script-textarea').val();
        }
        
        self.updateElementProperty(element, 'name', name);
        
        // Update script content in BPMN element
        var modeling = self.bpmnModeler.get('modeling');
        var moddle = self.bpmnModeler.get('moddle');
        
        // Create script element
        var scriptElement = moddle.create('bpmn:Script', {
            value: scriptContent
        });
        
        modeling.updateProperties(element, {
            script: scriptContent,
            scriptFormat: 'python'
        });
        
        frappe.show_alert({message: 'Script task properties updated', indicator: 'green'});
        
        // Cleanup Monaco editor
        if (editor) {
            editor.dispose();
        }
    });
};

WorkflowDesigner.prototype.renderGatewayProperties = function(element) {
    var self = this;
    var bo = element.businessObject;
    var name = bo.name || '';
    var gatewayType = element.type.replace('bpmn:', '');
    
    var html = '<div class="properties-form">' +
        '<h6 class="mb-3"><i class="fa fa-code-fork"></i> ' + gatewayType + ' Properties</h6>' +
        '<div class="form-group">' +
            '<label>Name:</label>' +
            '<input type="text" class="form-control prop-name" value="' + name + '" placeholder="e.g., Approval Decision">' +
        '</div>' +
        '<hr>' +
        '<h6 class="mb-2">Outgoing Flows</h6>' +
        '<p class="text-muted">Select individual flows to set conditions</p>' +
        '</div>';
    
    $('#properties-panel').html(html);
    
    $('.save-props').on('click', function() {
        var name = $('.prop-name').val();
        self.updateElementProperty(element, 'name', name);
    });
};

WorkflowDesigner.prototype.renderSequenceFlowProperties = function(element) {
    var self = this;
    var bo = element.businessObject;
    var name = bo.name || '';
    var condition = '';
    
    // Get condition expression if exists
    if (bo.conditionExpression && bo.conditionExpression.body) {
        condition = bo.conditionExpression.body;
    }
    
    var html = '<div class="properties-form">' +
        '<h6 class="mb-3"><i class="fa fa-arrow-right"></i> Sequence Flow Properties</h6>' +
        '<div class="form-group">' +
            '<label>Name:</label>' +
            '<input type="text" class="form-control prop-name" value="' + name + '" placeholder="e.g., Approved, Rejected">' +
        '</div>' +
        '<hr>' +
        '<div class="form-group">' +
            '<label>Condition (Python Expression):</label>' +
            '<textarea class="form-control prop-condition" rows="4" placeholder="e.g., context.get_variable(\'approved\') == True">' + condition + '</textarea>' +
            '<small class="form-text text-muted">Python expression that evaluates to True/False. Leave empty for default flow.</small>' +
        '</div>' +
        '<div class="alert alert-info mt-2">' +
            '<strong>Examples:</strong><br>' +
            '• context.get_variable(\'action\') == \'Approve\'<br>' +
            '• context.get_variable(\'amount\') > 1000<br>' +
            '• context.doc.status == \'Pending\'<br>' +
        '</div>' +
        '<button class="btn btn-primary btn-sm mt-2 save-flow-props">Save Properties</button>' +
        '</div>';
    
    $('#properties-panel').html(html);
    
    $('.save-flow-props').on('click', function() {
        var name = $('.prop-name').val();
        var conditionText = $('.prop-condition').val();
        
        self.updateElementProperty(element, 'name', name);
        
        // Update condition expression
        if (conditionText) {
            var modeling = self.bpmnModeler.get('modeling');
            var moddle = self.bpmnModeler.get('moddle');
            
            var conditionExpression = moddle.create('bpmn:FormalExpression', {
                body: conditionText
            });
            
            modeling.updateProperties(element, {
                conditionExpression: conditionExpression
            });
        }
        
        frappe.show_alert({message: 'Sequence flow properties updated', indicator: 'green'});
    });
};

WorkflowDesigner.prototype.renderServiceTaskProperties = function(element) {
    var self = this;
    var bo = element.businessObject;
    
    var name = bo.name || '';
    var implementation = bo.$attrs['activiti:class'] || bo.implementation || '';
    
    var html = '<div class="properties-form">' +
        '<h6 class="mb-3"><i class="fa fa-cog"></i> Service Task Properties</h6>' +
        '<div class="form-group">' +
            '<label>Name: <span class="text-danger">*</span></label>' +
            '<input type="text" class="form-control prop-name" value="' + name + '" placeholder="e.g., Call External API">' +
        '</div>' +
        '<hr>' +
        '<div class="form-group">' +
            '<label>API Method/Class:</label>' +
            '<input type="text" class="form-control prop-implementation" value="' + implementation + '" placeholder="e.g., workflow_engine.api.send_email">' +
            '<small class="form-text text-muted">Python method path to execute</small>' +
        '</div>' +
        '<button class="btn btn-primary btn-sm mt-3 save-service-task-props">Save Properties</button>' +
        '</div>';
    
    $('#properties-panel').html(html);
    
    $('.save-service-task-props').on('click', function() {
        var name = $('.prop-name').val();
        var implementation = $('.prop-implementation').val();
        
        self.updateElementProperty(element, 'name', name);
        
        if (implementation) {
            self.updateActivitiProperty(element, 'class', implementation);
        }
        
        frappe.show_alert({message: 'Service task properties updated', indicator: 'green'});
    });
};

// Global JavaScript for Workflow Engine

frappe.provide('workflow_engine');

workflow_engine = {
    start_workflow: function(workflow_definition, reference_doctype, reference_name, callback) {
        frappe.call({
            method: 'workflow_engine.api.workflow_execution.start_workflow',
            args: {
                workflow_definition: workflow_definition,
                reference_doctype: reference_doctype,
                reference_name: reference_name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Workflow started successfully'),
                        indicator: 'green'
                    });
                    if (callback) {
                        callback(r.message);
                    }
                }
            }
        });
    },

    complete_task: function(task_name, action, comments, form_data, callback) {
        frappe.call({
            method: 'workflow_engine.api.workflow_execution.complete_task',
            args: {
                task_name: task_name,
                action: action,
                comments: comments,
                form_data: form_data ? JSON.stringify(form_data) : null
            },
            callback: function(r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Task completed successfully'),
                        indicator: 'green'
                    });
                    if (callback) {
                        callback(r.message);
                    }
                }
            }
        });
    },

    get_my_tasks: function(status, callback) {
        frappe.call({
            method: 'workflow_engine.api.workflow_execution.get_my_tasks',
            args: {
                status: status
            },
            callback: function(r) {
                if (r.message && callback) {
                    callback(r.message);
                }
            }
        });
    },

    show_task_dialog: function(task_name) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Workflow Task',
                name: task_name
            },
            callback: function(r) {
                if (r.message) {
                    let task = r.message;
                    let d = new frappe.ui.Dialog({
                        title: task.node_name || 'Workflow Task',
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'task_info',
                                options: `
                                    <div class="workflow-task-info">
                                        <p><strong>Description:</strong> ${task.task_description || 'N/A'}</p>
                                        <p><strong>Priority:</strong> ${task.priority}</p>
                                        <p><strong>Due Date:</strong> ${task.due_date || 'Not set'}</p>
                                    </div>
                                `
                            },
                            {
                                fieldtype: 'Section Break'
                            },
                            {
                                fieldtype: 'Select',
                                fieldname: 'action',
                                label: 'Action',
                                options: ['Approve', 'Reject', 'Send Back'],
                                reqd: 1
                            },
                            {
                                fieldtype: 'Text Editor',
                                fieldname: 'comments',
                                label: 'Comments'
                            }
                        ],
                        primary_action_label: 'Submit',
                        primary_action: function(values) {
                            workflow_engine.complete_task(
                                task_name,
                                values.action,
                                values.comments,
                                null,
                                function() {
                                    d.hide();
                                    frappe.set_route('Form', 'Workflow Task', task_name);
                                }
                            );
                        }
                    });
                    d.show();
                }
            }
        });
    }
};

// Add to window for global access
window.workflow_engine = workflow_engine;

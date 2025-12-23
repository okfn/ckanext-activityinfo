ckan.module('activityinfo-download', function($) {
    return {
        initialize: function() {
            var self = this;
            this.el = this.el[0];
            // container div for all fields activity_info_new_div
            this.container_div = this.el.querySelector('#activity_info_new_div');
            this.dbSelect = this.el.querySelector('#ai-database-select');
            this.formSelect = this.el.querySelector('#ai-form-select');
            this.formatSelect = this.el.querySelector('#ai-format-select');
            this.errorDiv = this.el.querySelector('#ai-error');
            this.infoDiv = this.el.querySelector('#ai-info');
            this.radioBtn = document.getElementById('resource-url-activityinfo');
            // Include resource description to include Activity Info info
            this.descriptionField = document.getElementById('field-description');
            
            // Hidden fields for form submission
            this.dbIdField = this.el.querySelector('#ai-database-id-field');
            this.formIdField = this.el.querySelector('#ai-form-id-field');
            this.formatField = this.el.querySelector('#ai-format-field');
            this.formLabelField = this.el.querySelector('#ai-form-label-field');
            
            this.databasesLoaded = false;
            this.csrfToken = this.getCSRFToken();

            if (!this.dbSelect) {
                console.error('ActivityInfo: Could not find database select element');
                return;
            }

            // Load databases when ActivityInfo option is selected
            if (this.radioBtn) {
                this.radioBtn.addEventListener('change', function() {
                    if (this.checked && !self.databasesLoaded) {
                        self.container_div.style.display = 'block';
                        self.loadDatabases();
                    }
                });

                var aiButton = document.getElementById('btn-activity-info');
                if (aiButton) {
                    aiButton.addEventListener('click', function() {
                        if (!self.databasesLoaded) {
                            self.container_div.style.display = 'block';
                            setTimeout(function() {
                                self.loadDatabases();
                            }, 100);
                        }
                    });
                }

                if (this.radioBtn.checked) {
                    this.loadDatabases();
                }
            }

            this.dbSelect.addEventListener('change', function() {
                self.onDatabaseChange();
            });

            this.formSelect.addEventListener('change', function() {
                self.onFormChange();
            });

            this.formatSelect.addEventListener('change', function() {
                self.onFormatChange();
            });
        },

        getCSRFToken: function() {
            var csrf_field = $('meta[name=csrf_field_name]').attr('content');
            if (!csrf_field) return null;
            var csrf_token = $('meta[name='+ csrf_field +']').attr('content');  
            return csrf_token;
        },

        setupHeaders: function() {
            var headers = { 'Content-Type': 'application/json' };
            if (this.csrfToken) headers['X-CSRFToken'] = this.csrfToken;
            return headers;
        },

        showError: function(msg) {
            console.error('ActivityInfo Error:', msg);
            this.errorDiv.textContent = msg;
            this.errorDiv.style.display = 'block';
        },

        hideError: function() {
            this.errorDiv.style.display = 'none';
        },

        updateHiddenFields: function() {
            this.dbIdField.value = this.dbSelect.value || '';
            this.formIdField.value = this.formSelect.value || '';
            this.formatField.value = this.formatSelect.value || 'csv';
            
            var selectedForm = this.formSelect.options[this.formSelect.selectedIndex];
            this.formLabelField.value = selectedForm && selectedForm.value ? selectedForm.textContent.trim() : '';
            
            // Update resource name field if empty
            var nameField = document.getElementById('field-name');
            if (nameField && !nameField.value && this.formLabelField.value) {
                nameField.value = this.formLabelField.value;
            }
            
            // Update format field
            var formatField = document.getElementById('field-format');
            if (formatField && this.formatSelect.value) {
                formatField.value = this.formatSelect.value.toUpperCase();
            }

            // Update description field with ActivityInfo info
            if (this.descriptionField) {
                var dbLabel = this.dbSelect.options[this.dbSelect.selectedIndex] && this.dbSelect.value ? this.dbSelect.options[this.dbSelect.selectedIndex].textContent.trim() : '';
                var formLabel = selectedForm && selectedForm.value ? selectedForm.textContent.trim() : '';
                var desc = "This resource was downloaded from ActivityInfo.";
                if (dbLabel || formLabel) {
                    desc += " Database: " + (dbLabel || "-") + ", Form: " + (formLabel || "-");
                }
                this.descriptionField.value = desc;
            }
        },

        loadDatabases: function() {
            var self = this;
            this.hideError();
            this.dbSelect.innerHTML = '<option value="">-- Select database --</option>';
            this.dbSelect.style.display = 'none';
            this.el.querySelector('#ai-databases-loading').style.display = 'block';
            this.el.querySelector('#ai-step-form').style.display = 'none';
            this.el.querySelector('#ai-step-format').style.display = 'none';
            this.infoDiv.style.display = 'none';

            fetch('/api/action/act_info_get_databases', {
                method: 'POST',
                headers: this.setupHeaders(),
                body: JSON.stringify({})
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    self.el.querySelector('#ai-databases-loading').style.display = 'none';
                    if (!data.success) {
                        var errorMsg = data.error ? (data.error.message || data.error.__type || JSON.stringify(data.error)) : 'Failed to load databases';
                        self.showError(errorMsg);
                        return;
                    }
                    if (!data.result || data.result.length === 0) {
                        self.showError('No databases found. Please check your ActivityInfo API key.');
                        return;
                    }
                    data.result.forEach(function(db) {
                        var opt = document.createElement('option');
                        opt.value = db.databaseId;
                        opt.textContent = db.label || db.databaseId;
                        self.dbSelect.appendChild(opt);
                    });
                    self.dbSelect.style.display = 'block';
                    self.databasesLoaded = true;
                    
                    // Restore selection if editing
                    if (self.dbIdField.value) {
                        self.dbSelect.value = self.dbIdField.value;
                        self.onDatabaseChange();
                    }
                })
                .catch(function(e) {
                    self.el.querySelector('#ai-databases-loading').style.display = 'none';
                    self.showError('Error loading databases: ' + e.message);
                });
        },

        onDatabaseChange: function() {
            var dbId = this.dbSelect.value;
            this.updateHiddenFields();
            
            if (!dbId) {
                this.el.querySelector('#ai-step-form').style.display = 'none';
                this.el.querySelector('#ai-step-format').style.display = 'none';
                this.infoDiv.style.display = 'none';
                return;
            }
            this.loadForms(dbId);
        },

        loadForms: function(dbId) {
            var self = this;
            this.hideError();
            this.formSelect.innerHTML = '<option value="">-- Select form --</option>';
            this.formSelect.style.display = 'none';
            this.el.querySelector('#ai-forms-loading').style.display = 'block';
            this.el.querySelector('#ai-step-form').style.display = 'block';
            this.el.querySelector('#ai-step-format').style.display = 'none';
            this.infoDiv.style.display = 'none';

            fetch('/api/action/act_info_get_forms', {
                method: 'POST',
                headers: this.setupHeaders(),
                body: JSON.stringify({ database_id: dbId })
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    self.el.querySelector('#ai-forms-loading').style.display = 'none';
                    if (!data.success) {
                        var errorMsg = data.error ? (data.error.message || data.error.__type || JSON.stringify(data.error)) : 'Failed to load forms';
                        self.showError(errorMsg);
                        return;
                    }
                    data.result.forms.forEach(function(form) {
                        var opt = document.createElement('option');
                        opt.value = form.id;
                        opt.textContent = form.label || form.id;
                        self.formSelect.appendChild(opt);
                    });
                    data.result.sub_forms.forEach(function(form) {
                        var opt = document.createElement('option');
                        opt.value = form.id;
                        opt.textContent = form.label || form.id;
                        self.formSelect.appendChild(opt);
                    });
                    self.formSelect.style.display = 'block';
                    
                    // Restore selection if editing
                    if (self.formIdField.value) {
                        self.formSelect.value = self.formIdField.value;
                        self.onFormChange();
                    }
                })
                .catch(function(e) {
                    self.el.querySelector('#ai-forms-loading').style.display = 'none';
                    self.showError('Error loading forms: ' + e.message);
                });
        },

        onFormChange: function() {
            this.updateHiddenFields();
            
            if (this.formSelect.value) {
                this.el.querySelector('#ai-step-format').style.display = 'block';
                this.infoDiv.style.display = 'block';
                
                // Restore format selection if editing
                if (this.formatField.value) {
                    this.formatSelect.value = this.formatField.value;
                }
            } else {
                this.el.querySelector('#ai-step-format').style.display = 'none';
                this.infoDiv.style.display = 'none';
            }
        },

        onFormatChange: function() {
            this.updateHiddenFields();
        }
    };
});

ckan.module('activityinfo-download', function($) {
    return {
        initialize: function() {
            var self = this;
            this.el = this.el[0]; // Get the DOM element
            this.dbSelect = this.el.querySelector('#ai-database-select');
            this.formSelect = this.el.querySelector('#ai-form-select');
            this.formatSelect = this.el.querySelector('#ai-format-select');
            this.importBtn = this.el.querySelector('#ai-import-btn');
            this.progressDiv = this.el.querySelector('#ai-download-progress');
            this.progressText = this.el.querySelector('#ai-progress-text');
            this.errorDiv = this.el.querySelector('#ai-error');
            this.radioBtn = document.getElementById('resource-url-activityinfo');
            this.databasesLoaded = false;
            
            // Get CSRF token from the page
            this.csrfToken = this.getCSRFToken();

            if (!this.dbSelect) {
                console.error('ActivityInfo: Could not find database select element');
                return;
            }

            // Load databases when ActivityInfo option is selected
            if (this.radioBtn) {
                this.radioBtn.addEventListener('change', function() {
                    if (this.checked && !self.databasesLoaded) {
                        self.loadDatabases();
                    }
                });

                // Also listen for click on the button that selects this radio
                var aiButton = document.getElementById('btn-activity-info');
                if (aiButton) {
                    aiButton.addEventListener('click', function() {
                        if (!self.databasesLoaded) {
                            setTimeout(function() {
                                self.loadDatabases();
                            }, 100);
                        }
                    });
                }

                // If already checked on page load, load databases
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

            this.importBtn.addEventListener('click', function() {
                self.startImport();
            });
        },

        getCSRFToken: function() {
            var metaTag = document.querySelector('meta[name="csrf_token"]');
            if (metaTag) {
                return metaTag.getAttribute('content');
            }
            var match = document.cookie.match(/csrf_token=([^;]+)/);
            if (match) {
                return match[1];
            }
            var input = document.querySelector('input[name="_csrf_token"]');
            if (input) {
                return input.value;
            }
            return null;
        },

        getHeaders: function() {
            var headers = {
                'Content-Type': 'application/json',
            };
            if (this.csrfToken) {
                headers['X-CSRFToken'] = this.csrfToken;
            }
            return headers;
        },

        resetForm: function() {
            this.dbSelect.innerHTML = '<option value="">-- Select database --</option>';
            this.formSelect.innerHTML = '<option value="">-- Select form --</option>';
            this.el.querySelector('#ai-step-form').style.display = 'none';
            this.el.querySelector('#ai-step-format').style.display = 'none';
            this.el.querySelector('#ai-step-import').style.display = 'none';
            this.progressDiv.style.display = 'none';
            this.errorDiv.style.display = 'none';
        },

        showError: function(msg) {
            console.error('ActivityInfo Error:', msg);
            this.errorDiv.textContent = msg;
            this.errorDiv.style.display = 'block';
        },

        loadDatabases: function() {
            var self = this;
            console.log('ActivityInfo: Loading databases...');
            this.resetForm();
            this.dbSelect.style.display = 'none';
            this.el.querySelector('#ai-databases-loading').style.display = 'block';

            fetch('/api/action/act_info_get_databases', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({})
            })
                .then(function(r) { 
                    console.log('ActivityInfo: Got response', r.status);
                    return r.json(); 
                })
                .then(function(data) {
                    console.log('ActivityInfo: Parsed response', data);
                    self.el.querySelector('#ai-databases-loading').style.display = 'none';
                    if (!data.success) {
                        var errorMsg = 'Failed to load databases';
                        if (data.error) {
                            errorMsg = data.error.message || data.error.__type || JSON.stringify(data.error);
                        }
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
                })
                .catch(function(e) {
                    console.error('ActivityInfo: Fetch error', e);
                    self.el.querySelector('#ai-databases-loading').style.display = 'none';
                    self.showError('Error loading databases: ' + e.message);
                });
        },

        onDatabaseChange: function() {
            var dbId = this.dbSelect.value;
            if (!dbId) {
                this.el.querySelector('#ai-step-form').style.display = 'none';
                this.el.querySelector('#ai-step-format').style.display = 'none';
                this.el.querySelector('#ai-step-import').style.display = 'none';
                return;
            }
            this.loadForms(dbId);
        },

        loadForms: function(dbId) {
            var self = this;
            this.formSelect.innerHTML = '<option value="">-- Select form --</option>';
            this.formSelect.style.display = 'none';
            this.el.querySelector('#ai-forms-loading').style.display = 'block';
            this.el.querySelector('#ai-step-form').style.display = 'block';
            this.el.querySelector('#ai-step-format').style.display = 'none';
            this.el.querySelector('#ai-step-import').style.display = 'none';

            fetch('/api/action/act_info_get_forms', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ database_id: dbId })
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    self.el.querySelector('#ai-forms-loading').style.display = 'none';
                    if (!data.success) {
                        var errorMsg = 'Failed to load forms';
                        if (data.error) {
                            errorMsg = data.error.message || data.error.__type || JSON.stringify(data.error);
                        }
                        self.showError(errorMsg);
                        return;
                    }
                    data.result.forms.forEach(function(form) {
                        var opt = document.createElement('option');
                        opt.value = form.id;
                        opt.textContent = form.label || form.id;
                        self.formSelect.appendChild(opt);
                    });
                    self.formSelect.style.display = 'block';
                })
                .catch(function(e) {
                    self.el.querySelector('#ai-forms-loading').style.display = 'none';
                    self.showError('Error loading forms: ' + e.message);
                });
        },

        onFormChange: function() {
            if (this.formSelect.value) {
                this.el.querySelector('#ai-step-format').style.display = 'block';
                this.el.querySelector('#ai-step-import').style.display = 'block';
            } else {
                this.el.querySelector('#ai-step-format').style.display = 'none';
                this.el.querySelector('#ai-step-import').style.display = 'none';
            }
        },

        startImport: function() {
            var self = this;
            var formId = this.formSelect.value;
            var format = this.formatSelect.value;
            if (!formId) return;

            this.importBtn.disabled = true;
            this.progressDiv.style.display = 'block';
            this.progressText.textContent = 'Starting export job...';

            fetch('/activity-info/download/' + formId + '.' + format.toLowerCase(), {
                method: 'GET',
                headers: this.getHeaders()
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (!data.success) {
                        self.showError('Failed to start export');
                        self.progressDiv.style.display = 'none';
                        self.importBtn.disabled = false;
                        return;
                    }
                    self.pollJobStatus(data.job_id);
                })
                .catch(function(e) {
                    self.showError('Error: ' + e.message);
                    self.progressDiv.style.display = 'none';
                    self.importBtn.disabled = false;
                });
        },

        pollJobStatus: function(jobId) {
            var self = this;
            fetch('/activity-info/job-status/' + jobId, {
                method: 'GET',
                headers: this.getHeaders()
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (!data.success) {
                        self.showError('Job failed');
                        self.progressDiv.style.display = 'none';
                        self.importBtn.disabled = false;
                        return;
                    }
                    var state = data.result.state;
                    if (state === 'completed' && data.download_url) {
                        self.progressText.textContent = 'Download ready!';
                        
                        var linkRadio = document.getElementById('resource-url-link');
                        if (linkRadio) {
                            linkRadio.checked = true;
                        }
                        
                        var urlField = document.getElementById('field-resource-url') || document.querySelector('input[name="url"]');
                        if (urlField) {
                            urlField.value = data.download_url;
                            urlField.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        
                        var nameField = document.getElementById('field-name');
                        if (nameField && !nameField.value) {
                            var selectedForm = self.formSelect.options[self.formSelect.selectedIndex];
                            nameField.value = selectedForm.textContent;
                        }
                        
                        var formatField = document.getElementById('field-format');
                        if (formatField) {
                            formatField.value = self.formatSelect.value;
                        }

                        self.progressDiv.style.display = 'none';
                        self.importBtn.disabled = false;
                    } else if (state === 'failed') {
                        self.showError('Export job failed');
                        self.progressDiv.style.display = 'none';
                        self.importBtn.disabled = false;
                    } else {
                        var pct = data.result.percentComplete || 0;
                        self.progressText.textContent = 'Exporting... ' + pct + '%';
                        setTimeout(function() { self.pollJobStatus(jobId); }, 1500);
                    }
                })
                .catch(function(e) {
                    self.showError('Error checking status: ' + e.message);
                    self.progressDiv.style.display = 'none';
                    self.importBtn.disabled = false;
                });
        }
    };
});

document.addEventListener('DOMContentLoaded', function() {
    var btnActivityInfo = document.getElementById('btn-activity-info');
    if (!btnActivityInfo) return;

    var dbSelect = document.getElementById('ai-database-select');
    var formSelect = document.getElementById('ai-form-select');
    var formatSelect = document.getElementById('ai-format-select');
    var importBtn = document.getElementById('ai-import-btn');
    var progressDiv = document.getElementById('ai-download-progress');
    var progressText = document.getElementById('ai-progress-text');
    var errorDiv = document.getElementById('ai-error');

    // Open modal when button is clicked
    btnActivityInfo.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $('#activity-info-modal').modal('show');
    });

    // Load databases when modal opens
    $('#activity-info-modal').on('show.bs.modal', function() {
        resetModal();
        loadDatabases();
    });

    function resetModal() {
        dbSelect.innerHTML = '<option value="">-- Select database --</option>';
        dbSelect.style.display = 'none';
        document.getElementById('ai-databases-loading').style.display = 'block';
        formSelect.innerHTML = '<option value="">-- Select form --</option>';
        document.getElementById('ai-step-form').style.display = 'none';
        document.getElementById('ai-step-format').style.display = 'none';
        progressDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        importBtn.disabled = true;
    }

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.style.display = 'block';
    }

    function loadDatabases() {
        var csrf_field = $('meta[name=csrf_field_name]').attr('content');
        var csrf_token = $('meta[name='+ csrf_field +']').attr('content');
        
        fetch('/api/action/act_info_get_databases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify({})
        })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                document.getElementById('ai-databases-loading').style.display = 'none';
                if (!data.success) {
                    showError(data.error || 'Failed to load databases');
                    return;
                }
                data.result.forEach(function(db) {
                    var opt = document.createElement('option');
                    opt.value = db.databaseId;
                    opt.textContent = db.label || db.databaseId;
                    dbSelect.appendChild(opt);
                });
                dbSelect.style.display = 'block';
            })
            .catch(function(e) {
                document.getElementById('ai-databases-loading').style.display = 'none';
                showError('Error loading databases: ' + e.message);
            });
    }

    dbSelect.addEventListener('change', function() {
        var dbId = this.value;
        if (!dbId) {
            document.getElementById('ai-step-form').style.display = 'none';
            return;
        }
        loadForms(dbId);
    });

    function loadForms(dbId) {
        formSelect.innerHTML = '<option value="">-- Select form --</option>';
        formSelect.style.display = 'none';
        document.getElementById('ai-forms-loading').style.display = 'block';
        document.getElementById('ai-step-form').style.display = 'block';
        document.getElementById('ai-step-format').style.display = 'none';
        importBtn.disabled = true;

        fetch('/activity-info/api/database/' + dbId + '/forms')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                document.getElementById('ai-forms-loading').style.display = 'none';
                if (!data.success) {
                    showError(data.error || 'Failed to load forms');
                    return;
                }
                data.result.forms.forEach(function(form) {
                    var opt = document.createElement('option');
                    opt.value = form.id;
                    opt.textContent = form.label || form.id;
                    formSelect.appendChild(opt);
                });
                formSelect.style.display = 'block';
            })
            .catch(function(e) {
                document.getElementById('ai-forms-loading').style.display = 'none';
                showError('Error loading forms: ' + e.message);
            });
    }

    formSelect.addEventListener('change', function() {
        if (this.value) {
            document.getElementById('ai-step-format').style.display = 'block';
            importBtn.disabled = false;
        } else {
            document.getElementById('ai-step-format').style.display = 'none';
            importBtn.disabled = true;
        }
    });

    importBtn.addEventListener('click', function() {
        var formId = formSelect.value;
        var format = formatSelect.value;
        if (!formId) return;

        importBtn.disabled = true;
        progressDiv.style.display = 'block';
        progressText.textContent = 'Starting export job...';

        fetch('/activity-info/download/' + formId + '.' + format.toLowerCase())
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.success) {
                    showError('Failed to start export');
                    progressDiv.style.display = 'none';
                    importBtn.disabled = false;
                    return;
                }
                pollJobStatus(data.job_id);
            })
            .catch(function(e) {
                showError('Error: ' + e.message);
                progressDiv.style.display = 'none';
                importBtn.disabled = false;
            });
    });

    function pollJobStatus(jobId) {
        fetch('/activity-info/job-status/' + jobId)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.success) {
                    showError('Job failed');
                    progressDiv.style.display = 'none';
                    importBtn.disabled = false;
                    return;
                }
                var state = data.result.state;
                if (state === 'completed' && data.download_url) {
                    progressText.textContent = 'Download ready!';
                    // Set the URL in the resource form
                    var urlField = document.getElementById('field-resource-url') || document.querySelector('input[name="url"]');
                    if (urlField) {
                        urlField.value = data.download_url;
                        urlField.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    // Set name from form label if name field is empty
                    var nameField = document.getElementById('field-name');
                    if (nameField && !nameField.value) {
                        var selectedForm = formSelect.options[formSelect.selectedIndex];
                        nameField.value = selectedForm.textContent;
                    }
                    // Set format field
                    var formatField = document.getElementById('field-format');
                    if (formatField) {
                        formatField.value = formatSelect.value;
                    }
                    // Close modal
                    $('#activity-info-modal').modal('hide');
                } else if (state === 'failed') {
                    showError('Export job failed');
                    progressDiv.style.display = 'none';
                    importBtn.disabled = false;
                } else {
                    var pct = data.result.percentComplete || 0;
                    progressText.textContent = 'Exporting... ' + pct + '%';
                    setTimeout(function() { pollJobStatus(jobId); }, 1500);
                }
            })
            .catch(function(e) {
                showError('Error checking status: ' + e.message);
                progressDiv.style.display = 'none';
                importBtn.disabled = false;
            });
    }
});

(function() {
    'use strict';

    var POLL_INTERVAL = 3000;

    document.addEventListener('DOMContentLoaded', function() {
        var buttons = document.querySelectorAll('.activityinfo-update-resource-btn');
        buttons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                handleUpdateClick(btn);
            });
        });
    });

    function getCSRFToken() {
        var csrfField = document.querySelector('meta[name=csrf_field_name]');
        if (!csrfField) return null;
        var csrfMeta = document.querySelector('meta[name=' + csrfField.getAttribute('content') + ']');
        return csrfMeta ? csrfMeta.getAttribute('content') : null;
    }

    function handleUpdateClick(btn) {
        var resourceId = btn.dataset.activityinfoResourceId;
        if (!resourceId) return;

        // Replace button with status label
        var statusLabel = document.createElement('span');
        statusLabel.className = 'activityinfo-update-status';
        statusLabel.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Update in progress...';
        btn.parentNode.replaceChild(statusLabel, btn);

        var headers = { 'Content-Type': 'application/json' };
        var csrfToken = getCSRFToken();
        if (csrfToken) headers['X-CSRFToken'] = csrfToken;

        fetch('/api/action/act_info_update_resource_file', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ resource_id: resourceId })
        })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.success) {
                    var msg = data.error ? (data.error.message || JSON.stringify(data.error)) : 'Failed to start update';
                    statusLabel.innerHTML = '<i class="fa fa-exclamation-triangle"></i> Error: ' + msg;
                    return;
                }
                pollResourceStatus(resourceId, statusLabel);
            })
            .catch(function(e) {
                statusLabel.innerHTML = '<i class="fa fa-exclamation-triangle"></i> Error: ' + e.message;
            });
    }

    function pollResourceStatus(resourceId, statusLabel) {
        var headers = { 'Content-Type': 'application/json' };
        var csrfToken = getCSRFToken();
        if (csrfToken) headers['X-CSRFToken'] = csrfToken;

        fetch('/api/action/resource_show', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ id: resourceId })
        })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.success) {
                    statusLabel.innerHTML = '<i class="fa fa-exclamation-triangle"></i> Error checking status';
                    return;
                }
                var res = data.result;
                var status = res.activityinfo_status;
                var progress = res.activityinfo_progress || 0;

                if (status === 'complete') {
                    statusLabel.innerHTML = '<span class="badge badge-success"><i class="fa fa-check"></i> Resource updated successfully</span>';
                } else if (status === 'error') {
                    statusLabel.innerHTML = '<i class="fa fa-exclamation-triangle"></i> Error: ' + (res.activityinfo_error || 'Unknown error');
                } else {
                    statusLabel.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Update in progress... ' + progress + '%';
                    setTimeout(function() {
                        pollResourceStatus(resourceId, statusLabel);
                    }, POLL_INTERVAL);
                }
            })
            .catch(function(e) {
                statusLabel.innerHTML = '<i class="fa fa-exclamation-triangle"></i> Error: ' + e.message;
            });
    }
})();

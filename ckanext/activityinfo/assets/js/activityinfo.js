(function() {
    'use strict';

    // Poll interval in milliseconds
    const POLL_INTERVAL = 2000;

    document.addEventListener('DOMContentLoaded', function() {
        initDownloadButtons();
    });

    function initDownloadButtons() {
        const downloadButtons = document.querySelectorAll('.ai-download-btn');
        downloadButtons.forEach(function(btn) {
            btn.addEventListener('click', handleDownloadClick);
        });
    }

    function handleDownloadClick(event) {
        const btn = event.currentTarget;
        const formId = btn.dataset.formId;
        const formLabel = btn.dataset.formLabel;
        const downloadUrl = btn.dataset.downloadUrl;
        const jobStatusUrlTemplate = btn.dataset.jobStatusUrl;

        // Disable button and show spinner
        setButtonLoading(btn, true, 'Starting...');

        // Start the download job
        fetch(downloadUrl)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Failed to start download job');
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success && data.job_id) {
                    const jobStatusUrl = jobStatusUrlTemplate.replace('__JOB_ID__', data.job_id);
                    pollJobStatus(btn, data.job_id, jobStatusUrl, formLabel);
                } else {
                    throw new Error(data.error || 'Failed to start download job');
                }
            })
            .catch(function(error) {
                console.error('Download error:', error);
                setButtonLoading(btn, false);
                showAlert('Error starting download: ' + error.message, 'danger');
            });
    }

    function pollJobStatus(btn, jobId, jobStatusUrl, formLabel) {
        fetch(jobStatusUrl)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Failed to get job status');
                }
                return response.json();
            })
            .then(function(data) {
                const jobStatus = data.result || data;
                const state = jobStatus.state;
                const percentComplete = jobStatus.percentComplete || 0;

                if (state === 'completed') {
                    setButtonLoading(btn, false);
                    // Use the full download URL from the response
                    const downloadUrl = data.download_url;
                    if (downloadUrl) {
                        // Open in new tab to trigger download from ActivityInfo
                        window.open(downloadUrl, '_blank');
                        showAlert('Download ready for "' + formLabel + '"', 'success');
                    } else {
                        showAlert('Download completed but no download URL provided', 'warning');
                    }
                } else if (state === 'failed') {
                    setButtonLoading(btn, false);
                    showAlert('Download failed for "' + formLabel + '"', 'danger');
                } else {
                    // Still in progress
                    setButtonLoading(btn, true, percentComplete + '%');
                    setTimeout(function() {
                        pollJobStatus(btn, jobId, jobStatusUrl, formLabel);
                    }, POLL_INTERVAL);
                }
            })
            .catch(function(error) {
                console.error('Status poll error:', error);
                setButtonLoading(btn, false);
                showAlert('Error checking download status: ' + error.message, 'danger');
            });
    }

    function setButtonLoading(btn, isLoading, progressText) {
        const textSpan = btn.querySelector('.download-text');
        const spinnerSpan = btn.querySelector('.download-spinner');
        const progressSpan = btn.querySelector('.progress-text');

        btn.disabled = isLoading;

        if (isLoading) {
            textSpan.style.display = 'none';
            spinnerSpan.style.display = 'inline';
            if (progressText) {
                progressSpan.textContent = progressText;
            }
        } else {
            textSpan.style.display = 'inline';
            spinnerSpan.style.display = 'none';
        }
    }

    function showAlert(message, type) {
        // Try to find existing flash message container
        let flashContainer = document.querySelector('.flash-messages');
        if (!flashContainer) {
            flashContainer = document.createElement('div');
            flashContainer.className = 'flash-messages';
            const mainContent = document.querySelector('.primary') || document.body;
            mainContent.insertBefore(flashContainer, mainContent.firstChild);
        }

        const alert = document.createElement('div');
        alert.className = 'alert alert-' + type + ' alert-dismissible fade show';
        alert.innerHTML = message + 
            '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
            '<span aria-hidden="true">&times;</span></button>';
        
        flashContainer.appendChild(alert);

        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            alert.remove();
        }, 5000);
    }
})();

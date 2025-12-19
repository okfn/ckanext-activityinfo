"""Background jobs for ActivityInfo downloads."""
from __future__ import annotations

import logging
import os
import tempfile
import time

from ckan.plugins import toolkit
from werkzeug.datastructures import FileStorage

from ckanext.activityinfo.utils import get_user_token
from ckanext.activityinfo.data.base import ActivityInfoClient


log = logging.getLogger(__name__)


def download_activityinfo_resource(resource_id: str, user: str) -> None:
    """Background job to download ActivityInfo data and update the resource.

    Args:
        resource_id: The CKAN resource ID
        user: The username who initiated the download
    """

    log.info(f"ActivityInfo Job: Starting download for resource {resource_id}")

    context = {'user': user}

    resource = toolkit.get_action('resource_show')(context, {'id': resource_id})

    form_id = resource.get('activityinfo_form_id')
    format_type = resource.get('activityinfo_format', 'csv').lower()
    form_label = resource.get('activityinfo_form_label', 'ActivityInfo Export')

    if not form_id:
        raise ValueError("Missing activityinfo_form_id")

    _update_resource_status(toolkit.fresh_context(context), resource_id, 'exporting', 0)

    token = get_user_token(user)
    if not token:
        raise ValueError("No ActivityInfo API key configured for user")

    client = ActivityInfoClient(api_key=token)

    log.info(f"ActivityInfo Job: Starting export for form {form_id}")
    job_info = client.start_job_download_form_data(form_id, format=format_type.upper())
    job_id = job_info.get('id') or job_info.get('jobId')

    if not job_id:
        raise ValueError("Failed to start ActivityInfo export job")

    log.debug(f"ActivityInfo Job: Export job started with ID {job_id}")

    # Poll for job completion
    max_wait = 300  # 5 minutes max
    poll_interval = 3
    elapsed = 0

    while elapsed < max_wait:
        status = client.get_job_status(job_id)
        state = status.get('state')
        percent = status.get('percentComplete', 0)
        # Update progress
        _update_resource_status(toolkit.fresh_context(context), resource_id, 'exporting', percent)

        if state == 'completed':
            result = status.get('result', {})
            download_url = result.get('downloadUrl') if isinstance(result, dict) else None
            if not download_url:
                raise ValueError("Export completed but no download URL provided")

            log.info(f"ActivityInfo Job: Export completed, downloading from {download_url}")
            _update_resource_status(toolkit.fresh_context(context), resource_id, 'downloading', 100)

            # Download the file
            if not download_url.startswith('http'):
                download_url = f"{client.base_url}/{download_url.lstrip('/')}"

            file_data = client.download_file(download_url)

            # Generate filename
            safe_label = "".join(c if c.isalnum() or c in '-_ ' else '_' for c in form_label)
            filename = f"{safe_label}.{format_type}"

            # Save to temp file and update resource
            _update_resource_with_file(toolkit.fresh_context(context), resource_id, file_data, filename, format_type)

            log.info(f"ActivityInfo Job: Successfully updated resource {resource_id}")
            return

        elif state == 'failed':
            error = status.get('error', 'Unknown error')
            _update_resource_status(toolkit.fresh_context(context), resource_id, 'error', percent, error)
            raise ValueError(f"ActivityInfo export job failed: {error}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    _update_resource_status(toolkit.fresh_context(context), resource_id, 'error', 0, 'Timeout waiting for export job to complete')
    raise ValueError(f"ActivityInfo export job timed out after {max_wait} seconds")


def _update_resource_status(context: dict, resource_id: str, status: str,
                            progress: int, error: str = '') -> None:
    """Update the ActivityInfo status fields on a resource."""

    toolkit.get_action('resource_patch')(
        context,
        {
            'id': resource_id,
            'activityinfo_status': status,
            'activityinfo_progress': progress,
            'activityinfo_error': error,
        }
    )


def _update_resource_with_file(context: dict, resource_id: str,
                               file_data: bytes, filename: str, format_type: str) -> None:
    """Update resource with the downloaded file."""
    suffix = f'.{format_type}'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_data)
        tmp_path = tmp.name

    if format_type == 'xlsx':
        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        mime_type = 'text/csv'

    f = open(tmp_path, 'rb')

    file_storage = FileStorage(
        stream=f,
        filename=filename,
        content_type=mime_type
    )

    try:
        toolkit.get_action('resource_patch')(
            context,
            {
                'id': resource_id,
                'upload': file_storage,
                'url': filename,
                'activityinfo_status': 'complete',
                'activityinfo_progress': 100,
                'activityinfo_error': '',
            }
        )
    except Exception as e:
        error = f"ActivityInfo Job: Failed to update resource {resource_id} with downloaded file: {e}"
        log.error(error)
        _update_resource_status(toolkit.fresh_context(context), resource_id, 'error', 100, error)
        raise

    f.close()

import io
import logging

from ckan.plugins import toolkit
from werkzeug.datastructures import FileStorage
from ckanext.activityinfo.jobs.download import download_activityinfo_resource


log = logging.getLogger(__name__)


@toolkit.chained_action
def resource_create(original_action, context, data_dict):
    """Chain resource_create to handle ActivityInfo imports."""

    if data_dict.get('url_type') != 'activityinfo':
        return original_action(context, data_dict)

    form_id = data_dict.get('activityinfo_form_id')
    format_type = data_dict.get('activityinfo_format', 'csv').lower()
    form_label = data_dict.get('activityinfo_form_label', 'ActivityInfo Export')

    if not form_id:
        return original_action(context, data_dict)

    user = context.get('user')
    log.info(f"ActivityInfo: Creating resource for form {form_id} as {format_type} for user {user}")

    # Create a placeholder file
    placeholder_content, filename, mime_type = _create_placeholder_file(form_label, format_type)

    file_storage = FileStorage(
        stream=io.BytesIO(placeholder_content),
        filename=filename,
        content_type=mime_type
    )

    # Modify data_dict to use upload with placeholder
    data_dict['upload'] = file_storage
    data_dict['url'] = filename
    data_dict['url_type'] = 'upload'
    data_dict['resource_type'] = 'activityinfo'

    # Set status fields
    data_dict['activityinfo_status'] = 'pending'
    data_dict['activityinfo_progress'] = 0
    data_dict['activityinfo_error'] = ''

    if not data_dict.get('name'):
        data_dict['name'] = form_label

    data_dict['format'] = format_type.upper()

    # Create the resource with placeholder
    result = original_action(context, data_dict)

    # Enqueue the download job
    toolkit.enqueue_job(
        download_activityinfo_resource,
        [result['id'], user],
        title=f"Download ActivityInfo form: {form_label}",
        rq_kwargs={'timeout': 600}
    )

    log.info(f"ActivityInfo: Enqueued download job for resource {result['id']}")

    return result


@toolkit.chained_action
def resource_update(original_action, context, data_dict):
    """Chain resource_update to handle ActivityInfo re-imports."""

    if data_dict.get('url_type') != 'activityinfo':
        return original_action(context, data_dict)

    form_id = data_dict.get('activityinfo_form_id')
    format_type = data_dict.get('activityinfo_format', 'csv').lower()
    form_label = data_dict.get('activityinfo_form_label', 'ActivityInfo Export')

    if not form_id:
        return original_action(context, data_dict)

    user = context.get('user')
    log.info(f"ActivityInfo: Updating resource for form {form_id} as {format_type} for user {user}")

    placeholder_content, filename, mime_type = _create_placeholder_file(form_label, format_type)

    file_storage = FileStorage(
        stream=io.BytesIO(placeholder_content),
        filename=filename,
        content_type=mime_type
    )

    data_dict['upload'] = file_storage
    data_dict['url'] = filename
    data_dict['url_type'] = 'upload'
    data_dict['resource_type'] = 'activityinfo'

    data_dict['activityinfo_status'] = 'pending'
    data_dict['activityinfo_progress'] = 0
    data_dict['activityinfo_error'] = ''

    result = original_action(context, data_dict)

    toolkit.enqueue_job(
        download_activityinfo_resource,
        [result['id'], user],
        title=f"Re-download ActivityInfo form: {form_label}",
        rq_kwargs={'timeout': 600}
    )

    log.info(f"ActivityInfo: Enqueued re-download job for resource {result['id']}")

    return result


def _create_placeholder_file(form_label: str, format_type: str) -> tuple[bytes, str, str]:
    """Create a placeholder file for the ActivityInfo resource.

    Returns:
        Tuple of (content_bytes, filename, mime_type)
    """
    safe_label = "".join(c if c.isalnum() or c in '-_ ' else '_' for c in form_label)

    # Simple CSV placeholder for both formats
    content = f"status,message\npending,Downloading {form_label} from ActivityInfo...\n".encode('utf-8')
    filename = f"{safe_label}.{format_type}"
    mime_type = 'text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return content, filename, mime_type

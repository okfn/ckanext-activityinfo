import logging

from ckan.plugins import toolkit
from ckanext.activityinfo.jobs.download import download_activityinfo_resource


log = logging.getLogger(__name__)


@toolkit.chained_action
def resource_create(original_action, context, data_dict):
    """Chain resource_create to handle ActivityInfo imports."""

    # url_type = activityinfo means we are creating an ActivityInfo resource
    if data_dict.get('url_type') != 'activityinfo':
        return original_action(context, data_dict)

    form_id = data_dict.get('activityinfo_form_id')
    format_type = data_dict.get('activityinfo_format', 'csv').lower()
    form_label = data_dict.get('activityinfo_form_label', 'ActivityInfo Export')

    if not form_id:
        return original_action(context, data_dict)

    user = context.get('user')
    log.info(f"ActivityInfo: Creating resource for form {form_id} as {format_type} for user {user}")

    # Modify data_dict to use upload with placeholder
    data_dict['upload'] = ''
    data_dict['url'] = 'activityinfo.waiting.csv'  # fake filename
    data_dict['url_type'] = ''  # The final job will move this to 'upload'

    # Set ActivityInfo-specific fields
    data_dict['activityinfo_form_id'] = form_id
    data_dict['activityinfo_form_label'] = form_label
    data_dict['activityinfo_format'] = format_type

    # Set status fields
    data_dict['activityinfo_status'] = 'pending'
    data_dict['activityinfo_progress'] = 0
    data_dict['activityinfo_error'] = ''

    if not data_dict.get('name'):
        data_dict['name'] = form_label

    data_dict['format'] = format_type.upper()

    # Create the resource with placeholder
    # If we get a validation error, we need to change the fields we changed so the user
    # can redefine the "upload" file
    try:
        result = original_action(context, data_dict)
    except toolkit.ValidationError as ve:
        # Clean modified fields so the form shows correctly
        data_dict['upload'] = None
        data_dict['url'] = ''
        data_dict['url_type'] = ''
        data_dict['activityinfo_form_id'] = None
        data_dict['activityinfo_form_label'] = None
        data_dict['activityinfo_format'] = None
        data_dict['activityinfo_status'] = None
        data_dict['activityinfo_progress'] = None
        data_dict['activityinfo_error'] = None
        raise ve

    # Enqueue the download job
    toolkit.enqueue_job(
        download_activityinfo_resource,
        [result['id'], user],
        title=f"Download ActivityInfo form: {form_label}",
        rq_kwargs={'timeout': 600}
    )

    log.info(f"ActivityInfo: Enqueued download job for resource {result['id']}")

    return result

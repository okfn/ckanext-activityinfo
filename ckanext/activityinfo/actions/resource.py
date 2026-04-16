import logging

from ckan.plugins import toolkit
from ckanext.activityinfo.jobs.download import download_activityinfo_resource
from ckanext.activityinfo.utils import VALID_AUTO_UPDATE_VALUES


log = logging.getLogger(__name__)


def _validate_auto_update_fields(data_dict):
    """Validate activityinfo_auto_update and activityinfo_auto_update_runs fields."""
    errors = {}

    auto_update = data_dict.get('activityinfo_auto_update')
    if auto_update and auto_update not in VALID_AUTO_UPDATE_VALUES:
        errors['activityinfo_auto_update'] = (
            f'Invalid value. Must be one of: {", ".join(VALID_AUTO_UPDATE_VALUES)}'
        )

    auto_update_runs = data_dict.get('activityinfo_auto_update_runs')
    if auto_update_runs is not None and auto_update_runs != '':
        try:
            runs = int(auto_update_runs)
            if runs < 1 or runs > 20:
                errors['activityinfo_auto_update_runs'] = 'Must be between 1 and 20'
        except (ValueError, TypeError):
            errors['activityinfo_auto_update_runs'] = 'Must be a number between 1 and 20'

    if errors:
        raise toolkit.ValidationError(errors)


@toolkit.chained_action
def resource_create(original_action, context, data_dict):
    """ Chain resource_create to handle ActivityInfo imports.
        We must create one or more resources depending on the selected formats.
        Users can check more than one format, so we create a resource per format.
    """

    # Validate auto-update fields regardless of url_type
    _validate_auto_update_fields(data_dict)

    # url_type = activityinfo means we are creating an ActivityInfo resource
    if data_dict.get('url_type') != 'activityinfo':
        return original_action(context, data_dict)

    form_id = data_dict.get('activityinfo_form_id')
    # Support multiple formats (comma-separated) or single format
    formats_str = data_dict.get('activityinfo_formats', '') or data_dict.get('activityinfo_format', 'csv')
    formats = [f.strip().lower() for f in formats_str.split(',') if f.strip()]

    # Ensure at least one format is selected
    if not formats:
        formats = ['csv']

    form_label = data_dict.get('activityinfo_form_label', 'ActivityInfo Export')

    if not form_id:
        return original_action(context, data_dict)

    user = context.get('user')
    log.info(f"ActivityInfo: Creating resource(s) for form {form_id} as {formats} for user {user}")

    # Create a resource for each format
    results = []
    first_result = None

    for i, format_type in enumerate(formats):
        # Create a copy of data_dict for each resource
        resource_data = data_dict.copy()

        # Modify data_dict to use upload with placeholder
        resource_data['upload'] = ''
        resource_data['url'] = f'activityinfo.waiting.{format_type}'  # fake filename
        resource_data['url_type'] = ''  # The final job will move this to 'upload'

        # Set ActivityInfo-specific fields
        resource_data['activityinfo_form_id'] = form_id
        resource_data['activityinfo_form_label'] = form_label
        resource_data['activityinfo_format'] = format_type

        # Set status fields
        resource_data['activityinfo_status'] = 'pending'
        resource_data['activityinfo_progress'] = 0
        resource_data['activityinfo_error'] = ''

        # Store which user created this resource (for auto-update auth)
        resource_data['activityinfo_user'] = user

        # Set name with format suffix if multiple formats
        if len(formats) > 1:
            resource_data['name'] = f"{form_label} ({format_type.upper()})"
        elif not resource_data.get('name'):
            resource_data['name'] = form_label

        resource_data['format'] = format_type.upper()

        # Create the resource with placeholder
        try:
            result = original_action(context, resource_data)
            results.append(result)
            if first_result is None:
                first_result = result
        except toolkit.ValidationError as ve:
            # Clean modified fields so the form shows correctly
            # Only raise on first resource to avoid partial creation issues
            if i == 0:
                data_dict['upload'] = None
                data_dict['url'] = ''
                data_dict['url_type'] = ''
                data_dict['activityinfo_form_id'] = None
                data_dict['activityinfo_form_label'] = None
                data_dict['activityinfo_format'] = None
                data_dict['activityinfo_formats'] = None
                data_dict['activityinfo_status'] = None
                data_dict['activityinfo_progress'] = None
                data_dict['activityinfo_error'] = None
                raise ve
            else:
                log.error(f"ActivityInfo: Failed to create resource for format {format_type}: {ve}")
                continue

        # Enqueue the download job
        toolkit.enqueue_job(
            download_activityinfo_resource,
            [result['id'], user],
            title=f"Download ActivityInfo form: {form_label} ({format_type.upper()})",
            rq_kwargs={'timeout': 600}
        )

        log.info(f"ActivityInfo: Enqueued download job for resource {result['id']} ({format_type})")

    # Return the first result (standard CKAN behavior expects single resource)
    return first_result


@toolkit.chained_action
def resource_update(original_action, context, data_dict):
    """Chain resource_update to validate ActivityInfo auto-update fields."""
    _validate_auto_update_fields(data_dict)
    return original_action(context, data_dict)

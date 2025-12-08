import logging
from ckan.common import current_user
from ckanext.activityinfo.utils import get_user_token


log = logging.getLogger(__name__)


def get_activity_info_api_key(user_id=None):
    """ Get the API key in a request context. """
    if not user_id:
        user_id = current_user.name

    token = get_user_token(user_id)
    return token


def get_activityinfo_status(resource):
    """Get the ActivityInfo download status for a resource.

    Returns:
        dict with 'status', 'progress', and 'error' keys, or None if not an ActivityInfo resource
    """
    if resource.get('resource_type') != 'activityinfo' and not resource.get('activityinfo_form_id'):
        return None

    return {
        'status': resource.get('activityinfo_status', 'unknown'),
        'progress': resource.get('activityinfo_progress', 0),
        'error': resource.get('activityinfo_error', ''),
        'form_id': resource.get('activityinfo_form_id'),
        'form_label': resource.get('activityinfo_form_label'),
    }


def is_activityinfo_processing(resource):
    """Check if an ActivityInfo resource is still processing."""
    if resource.get('resource_type') != 'activityinfo':
        return False
    status = resource.get('activityinfo_status')
    return status in ('pending', 'exporting', 'downloading')


def is_activityinfo_resource(resource):
    """Check if a resource is an ActivityInfo resource."""
    return resource.get('resource_type') == 'activityinfo'

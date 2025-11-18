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

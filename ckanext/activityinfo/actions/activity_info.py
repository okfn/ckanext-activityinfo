import logging
from requests.exceptions import HTTPError
from ckan.plugins import toolkit
from ckanext.activityinfo.utils import get_user_token
from ckanext.activityinfo.data.base import ActivityInfoClient
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError


log = logging.getLogger(__name__)


def act_info_get_databases(context, data_dict):
    '''
    Action function to get ActivityInfo databases for a user.
    '''
    toolkit.check_access('act_info_get_databases', context, data_dict)
    user = context.get('user')
    log.debug(f"Getting ActivityInfo databases for user {user}")
    token = get_user_token(user)
    aic = ActivityInfoClient(api_key=token)
    try:
        databases = aic.get_databases()
    except HTTPError as e:
        # We can expect a HTTPError 401 Client Error: Unauthorized for url: https://www.activityinfo.org/resources/databases
        # for users with an invalid API key
        error = f"Error retrieving databases for user {user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    return databases

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


def act_info_get_forms(context, data_dict):
    '''
    Action function to get ActivityInfo forms for a database.
    '''
    toolkit.check_access('act_info_get_forms', context, data_dict)
    user = context.get('user')
    database_id = data_dict.get('database_id')
    if not database_id:
        raise toolkit.ValidationError({'database_id': 'Missing value'})

    log.debug(f"Getting ActivityInfo forms for database {database_id} and user {user}")
    token = get_user_token(user)
    aic = ActivityInfoClient(api_key=token)
    try:
        data = aic.get_forms(database_id, include_db_data=True)
    except HTTPError as e:
        error = f"Error retrieving forms for database {database_id} and user {user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    ret = {
        'forms': data['forms'],
        'database': data['database']
    }
    return ret

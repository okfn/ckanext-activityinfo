import logging
from ckan.plugins import toolkit
from ckanext.activityinfo.utils import get_user_token
from ckanext.activityinfo.data.base import ActivityInfoClient


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
    databases = aic.get_databases()
    return databases

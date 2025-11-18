import logging
from ckan.plugins import toolkit
from ckanext.activityinfo.utils import get_user_token


log = logging.getLogger(__name__)


@toolkit.auth_disallow_anonymous_access
def act_info_get_databases(context, data_dict):
    user = context.get('user')
    token = get_user_token(user)
    if not token:
        return {'success': False, 'msg': f"No ActivityInfo token found for user {user}."}
    return {'success': True}

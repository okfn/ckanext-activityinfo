import logging
from ckan.plugins import toolkit
from ckanext.activityinfo.utils import get_user_token


log = logging.getLogger(__name__)


def require_activity_info_token_decorator(func):
    def wrapper(context, data_dict):
        user = context.get('user')
        token = get_user_token(user)
        if not token:
            return {'success': False, 'msg': f"No ActivityInfo token found for user {user}.", 'activity_info_token': None}
        return {'success': True, 'activity_info_token': token}
    return wrapper


@toolkit.auth_disallow_anonymous_access
@require_activity_info_token_decorator
def act_info_get_databases(context, data_dict):
    return {'success': True}


@toolkit.auth_disallow_anonymous_access
@require_activity_info_token_decorator
def act_info_get_forms(context, data_dict):
    return {'success': True}

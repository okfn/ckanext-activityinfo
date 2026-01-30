import logging
from functools import wraps
from ckan.plugins import toolkit
from ckan import model
from sqlalchemy import and_


log = logging.getLogger(__name__)


def get_activity_info_user_plugin_extras(user_name_or_id):
    """
    Utility function to get the ActivityInfo plugin extras for a user.
    """
    log.debug(f"Retrieving ActivityInfo plugin extras for user {user_name_or_id}")
    if not user_name_or_id:
        return None

    # Only sysadmin can get other users' info, so we use the site user
    site_user = toolkit.get_action("get_site_user")({"ignore_auth": True}, {})
    user = toolkit.get_action('user_show')(
        context={'user': site_user['name']},
        data_dict={'id': user_name_or_id, 'include_plugin_extras': True}
    )

    if 'plugin_extras' not in user:
        log.error(f"No plugin extras found for user {user_name_or_id}")
        return None

    return user['plugin_extras']


def get_user_token(user_name_or_id):
    """
    Utility function to get the ActivityInfo user token.
    """
    log.debug(f"Retrieving ActivityInfo token for user {user_name_or_id}")

    plugin_extras = get_activity_info_user_plugin_extras(user_name_or_id)
    if not plugin_extras:
        return None
    if 'activity_info' not in plugin_extras:
        return None

    return plugin_extras['activity_info'].get('api_key')


def get_ckan_resources(form_id):
    """ Search for internal resources linked to the given ActivityInfo form ID
    Args:
        form_id: The ActivityInfo form ID
    Returns:
        A list of tuples (resource_name, resource_url)

    """
    search_dict = {'query': f'activityinfo_form_id:{form_id}'}
    resources = toolkit.get_action('resource_search')({'ignore_auth': True}, search_dict)
    ret = []
    if resources.get('count', 0) > 0:
        results = resources['results']
        for res in results:
            pkg = toolkit.get_action('package_show')(
                {'ignore_auth': True}, {'id': res['package_id']}
            )
            pkg_type = pkg.get('type', 'dataset')
            resource_url = toolkit.url_for(f'{pkg_type}_resource.read', id=pkg['name'], resource_id=res['id'])
            ret.append(
                (res.get('name', 'Unnamed resource'), resource_url)
            )

    return ret


def get_ai_resources(limit=100):
    """ Search for all resources linked to any ActivityInfo form ID
    Args:
        limit: Maximum number of resources to return, default 100
    Returns:
        A list of resources with their URLs

    """
    search_dict = {
        'query': 'activityinfo_status:complete',
        'limit': limit,
    }
    resources = toolkit.get_action('resource_search')({'ignore_auth': True}, search_dict)
    ret = []
    if resources.get('count', 0) > 0:
        results = resources['results']
        for res in results:
            pkg = toolkit.get_action('package_show')(
                {'ignore_auth': True}, {'id': res['package_id']}
            )
            pkg_type = pkg.get('type', 'dataset')
            resource_url = toolkit.url_for(f'{pkg_type}_resource.read', id=pkg['name'], resource_id=res['id'])
            res['final_url'] = resource_url
            res['package'] = pkg
            ret.append(res)

    return ret


def get_users_with_activity_info_token():
    """
    Get all users that have an ActivityInfo API key set in their plugin_extras.
    Uses SQLAlchemy to query the JSONB plugin_extras column.

    Returns:
        A list of user objects with ActivityInfo API keys.
    """
    # Query users where plugin_extras -> 'activity_info' -> 'api_key' exists and is not null
    # Use chained -> operators: plugin_extras -> 'activity_info' ->> 'api_key'
    users = model.Session.query(model.User).filter(
        and_(
            model.User.state == 'active',
            model.User.plugin_extras.isnot(None),
            model.User.plugin_extras['activity_info'].isnot(None),
            model.User.plugin_extras['activity_info']['api_key'].astext.isnot(None),
            model.User.plugin_extras['activity_info']['api_key'].astext != '',
        )
    ).all()

    final_users = []
    for user in users:
        final_users.append({
            'id': user.id,
            'name': user.name,
        })

    return final_users


def require_sysadmin_user(func):
    '''
    Decorator for flask view functions. Returns 403 response if no user is logged in or if the login user is external
    '''

    @wraps(func)
    def view_wrapper(*args, **kwargs):
        if not toolkit.current_user or toolkit.current_user.is_anonymous:
            return toolkit.abort(403, "Forbidden")
        if not toolkit.current_user.sysadmin:
            return toolkit.abort(403, "Sysadmin user required")
        return func(*args, **kwargs)

    return view_wrapper

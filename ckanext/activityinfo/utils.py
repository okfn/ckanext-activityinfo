import logging
from ckan.plugins import toolkit


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

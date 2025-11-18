import logging
from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def get_user_token(user_id):
    """
    Utility function to get the ActivityInfo user token.
    """
    log.debug(f"Retrieving ActivityInfo token for user {user_id}")
    try:
        user = toolkit.get_action('user_show')(
            context={'ignore_auth': True},
            data_dict={'id': user_id, 'include_plugin_extras': True}
        )
    except toolkit.ObjectNotFound:
        log.error(f"User {user_id} not found")
        return None

    if 'activity_info' not in user.plugin_extras:
        log.error(f"No ActivityInfo plugin extras found for user {user_id}")
        return None

    return user.plugin_extras.get('activity_info').get('api_key')

import logging
from flask import Blueprint
from ckan.plugins import toolkit


log = logging.getLogger(__name__)
activityinfo_bp = Blueprint('activity_info', __name__, url_prefix='/activity-info')


@activityinfo_bp.route('/')
def index():
    extra_vars = {}
    return toolkit.render('activity_info/index.html', extra_vars)


@activityinfo_bp.route('/update-api-key', methods=['POST'])
def update_api_key():
    """Create or update the current ActivityInfo API key for the logged-in user."""
    api_key = toolkit.request.form.get('activityinfo_api_key')
    if not api_key:
        message = 'Missing ActivityInfo API key.'
        log.error(message)
        toolkit.h.flash_error(message)
        return toolkit.redirect_to('activity_info.index')

    user_dict = toolkit.get_action('user_show')(
        context={'ignore_auth': True},
        data_dict={'id': toolkit.c.user, 'include_plugin_extras': True}
    )
    plugin_extras = user_dict.get('plugin_extras')
    if not plugin_extras:
        plugin_extras = {}
    activity_info_extras = plugin_extras.get('activity_info', {})
    activity_info_extras['api_key'] = api_key
    plugin_extras['activity_info'] = activity_info_extras
    toolkit.get_action('user_patch')(
        context={'user': toolkit.c.user},
        data_dict={
            'id': toolkit.c.user,
            'plugin_extras': plugin_extras
        }
    )
    toolkit.h.flash_success('ActivityInfo API key updated successfully.')
    return toolkit.redirect_to('activity_info.index')


@activityinfo_bp.route('/remove-api-key', methods=['POST'])
def remove_api_key():
    """Remove the current ActivityInfo API key for the logged-in user."""
    user_dict = toolkit.get_action('user_show')(
        context={'ignore_auth': True},
        data_dict={'id': toolkit.c.user, 'include_plugin_extras': True}
    )
    plugin_extras = user_dict.get('plugin_extras')
    if not plugin_extras or 'activity_info' not in plugin_extras:
        toolkit.h.flash_error('No ActivityInfo API key found to remove.')
        return toolkit.redirect_to('activity_info.index')

    activity_info_extras = plugin_extras.get('activity_info', {})
    activity_info_extras.pop('api_key', None)
    plugin_extras['activity_info'] = activity_info_extras
    toolkit.get_action('user_patch')(
        context={'user': toolkit.c.user},
        data_dict={
            'id': toolkit.c.user,
            'plugin_extras': plugin_extras
        }
    )
    toolkit.h.flash_success('ActivityInfo API key removed successfully.')
    return toolkit.redirect_to('activity_info.index')

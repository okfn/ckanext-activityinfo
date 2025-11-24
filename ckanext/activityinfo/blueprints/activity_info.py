import logging
from flask import Blueprint
from ckan.common import current_user
from ckan.plugins import toolkit
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError
from ckanext.activityinfo.utils import get_activity_info_user_plugin_extras, get_user_token


log = logging.getLogger(__name__)
activityinfo_bp = Blueprint('activity_info', __name__, url_prefix='/activity-info')


@activityinfo_bp.route('/')
def index():
    extra_vars = {
        'api_key': get_user_token(current_user.name),
    }
    return toolkit.render('activity_info/index.html', extra_vars)


@activityinfo_bp.route('/databases')
def databases():
    try:
        ai_databases = toolkit.get_action('act_info_get_databases')(
            context={'user': toolkit.c.user},
            data_dict={}
        )
    except ActivityInfoConnectionError as e:
        message = f"Could not retrieve ActivityInfo databases: {e}"
        log.error(message)
        toolkit.h.flash_error(message)
        return toolkit.redirect_to('activity_info.index')

    log.info(f"Retrieved {ai_databases}")
    extra_vars = {
        'databases': ai_databases,
    }
    return toolkit.render('activity_info/databases.html', extra_vars)


@activityinfo_bp.route('/databases/<database_id>/forms')
def forms(database_id):
    try:
        data = toolkit.get_action('act_info_get_forms')(
            context={'user': toolkit.c.user},
            data_dict={'database_id': database_id}
        )
    except (ActivityInfoConnectionError, toolkit.ValidationError) as e:
        message = f"Could not retrieve ActivityInfo forms: {e}"
        log.error(message)
        toolkit.h.flash_error(message)
        return toolkit.redirect_to('activity_info.databases')

    log.info(f"Retrieved {data}")
    extra_vars = {
        'forms': data['forms'],
        'database_id': database_id,
        'database': data['database'],
    }
    return toolkit.render('activity_info/forms.html', extra_vars)


@activityinfo_bp.route('/update-api-key', methods=['POST'])
def update_api_key():
    """Create or update the current ActivityInfo API key for the logged-in user."""
    api_key = toolkit.request.form.get('activityinfo_api_key')
    if not api_key:
        message = 'Missing ActivityInfo API key.'
        log.error(message)
        toolkit.h.flash_error(message)
        return toolkit.redirect_to('activity_info.index')

    plugin_extras = get_activity_info_user_plugin_extras(toolkit.c.user) or {}
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
    plugin_extras = get_activity_info_user_plugin_extras(toolkit.c.user) or {}
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

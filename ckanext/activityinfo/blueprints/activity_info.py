import logging
from flask import Blueprint
from ckan.common import current_user
from ckan.plugins import toolkit
from ckanext.activityinfo.data.base import ActivityInfoClient
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError
from ckanext.activityinfo.utils import get_activity_info_user_plugin_extras, get_user_token


log = logging.getLogger(__name__)
activityinfo_bp = Blueprint('activity_info', __name__, url_prefix='/activity-info')


@activityinfo_bp.route('/')
def index():
    """ Home page
        If the user has an API key, redirect to databases
        If not, show a page to enter the API key
    """
    extra_vars = {
        'api_key': get_user_token(current_user.name),
    }
    if extra_vars['api_key']:
        return toolkit.redirect_to('activity_info.databases')
    return toolkit.render('activity_info/index.html', extra_vars)


@activityinfo_bp.route('/api-key')
def api_key():
    """ Create or update the current ActivityInfo API key for the logged-in user.
    """
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
    # add the ActivityInfo URL to each database
    aic = ActivityInfoClient()
    for db in ai_databases:
        db['url'] = aic.get_url_to_database(db['databaseId'])

    extra_vars = {
        'databases': ai_databases,
    }
    return toolkit.render('activity_info/databases.html', extra_vars)


@activityinfo_bp.route('/database/<database_id>/forms')
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

    # Add urls to each form
    aic = ActivityInfoClient()
    for form in data['forms']:
        form['url'] = aic.get_url_to_form(form['id'])

    extra_vars = {
        'forms': data['forms'],
        'database_id': database_id,
        'database': data['database'],
    }
    return toolkit.render('activity_info/forms.html', extra_vars)


@activityinfo_bp.route('/database/<database_id>/form/<form_id>')
def form(database_id, form_id):
    try:
        data = toolkit.get_action('act_info_get_form')(
            context={'user': toolkit.c.user},
            data_dict={
                'database_id': database_id,
                'form_id': form_id
            }
        )
    except (ActivityInfoConnectionError, toolkit.ValidationError) as e:
        message = f"Could not retrieve ActivityInfo form details: {e}"
        log.error(message)
        toolkit.h.flash_error(message)
        return toolkit.redirect_to('activity_info.forms', database_id=database_id)

    log.info(f"Retrieved {data}")
    form = data['forms'][form_id]
    schema = form.get('schema', {})
    fields = schema.get('elements', {})
    extra_vars = {
        'data': data,
        'form': form,
        'database_id': schema['databaseId'],
        'database': {'label': 'Test DB'},
        'fields': fields,
    }
    return toolkit.render('activity_info/form_details.html', extra_vars)


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
    site_user = toolkit.get_action("get_site_user")({"ignore_auth": True}, {})
    toolkit.get_action('user_patch')(
        context={'user': site_user['name']},
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
    site_user = toolkit.get_action("get_site_user")({"ignore_auth": True}, {})
    toolkit.get_action('user_patch')(
        context={'user': site_user['name']},
        data_dict={
            'id': toolkit.c.user,
            'plugin_extras': plugin_extras
        }
    )
    toolkit.h.flash_success('ActivityInfo API key removed successfully.')
    return toolkit.redirect_to('activity_info.index')

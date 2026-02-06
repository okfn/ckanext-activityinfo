import logging
from flask import Blueprint, Response
from ckan.common import current_user
from ckan.plugins import toolkit
from ckan.views.api import _finish_ok
from ckanext.activityinfo.data.base import ActivityInfoClient
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError
from ckanext.activityinfo.utils import get_activity_info_user_plugin_extras, get_ckan_resources, get_user_token


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
        return toolkit.redirect_to('activity_info.api_key')

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

    # Add urls and related CKAN resources to each form
    aic = ActivityInfoClient()
    for form in data['forms']:
        form['url'] = aic.get_url_to_form(form['id'])
        form['resources'] = get_ckan_resources(form['id'])

    # Add urls to each sub_form
    for sub_form in data.get('sub_forms', []):
        sub_form['url'] = aic.get_url_to_form(sub_form['id'])
        sub_form['resources'] = get_ckan_resources(sub_form['id'])

    extra_vars = {
        'forms': data['forms'],
        'sub_forms': data.get('sub_forms', []),
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
        return toolkit.redirect_to('activity_info.api_key')

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
    return toolkit.redirect_to('activity_info.databases')


@activityinfo_bp.route('/remove-api-key', methods=['POST'])
def remove_api_key():
    """Remove the current ActivityInfo API key for the logged-in user."""
    plugin_extras = get_activity_info_user_plugin_extras(toolkit.c.user) or {}
    if not plugin_extras or 'activity_info' not in plugin_extras:
        toolkit.h.flash_error('No ActivityInfo API key found to remove.')
        return toolkit.redirect_to('activity_info.api_key')

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
    return toolkit.redirect_to('activity_info.api_key')


@activityinfo_bp.route('/download/<form_id>.<format>')
def download_form_data(form_id, format='csv'):
    """ Download form data as JSON file.
        This starts an export job and returns the job status URL.
    """
    try:
        job_info = toolkit.get_action('act_start_download_job')(
            context={'user': toolkit.c.user},
            data_dict={'form_id': form_id, 'format': format.upper()}
        )
    except ActivityInfoConnectionError as e:
        error = f"Error starting export job for form {form_id} and user {toolkit.c.user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    job_id = job_info.get('id')
    log.info(f"Started export job: {job_id}")
    ret = {
        'success': True,
        'job_id': job_id,
        'result': job_info,
    }
    return _finish_ok(ret)


@activityinfo_bp.route('/job-status/<job_id>')
def job_status(job_id):
    """ Get the status of an ActivityInfo export job. """
    try:
        job_status = toolkit.get_action('act_info_get_job_status')(
            context={'user': toolkit.c.user},
            data_dict={'job_id': job_id}
        )
    except ActivityInfoConnectionError as e:
        error = f"Error getting job status for job {job_id} and user {toolkit.c.user}: {e}"
        log.error(error)
        return _finish_ok({'success': False, 'error': str(e)})

    log.info(f"Job status for {job_id}: {job_status}")

    # Build proxy download URL if job is completed
    proxy_download_url = None
    if job_status.get('state') == 'completed':
        result = job_status.get('result', {})
        relative_url = result.get('downloadUrl', '')
        if relative_url:
            proxy_download_url = toolkit.url_for('activity_info.download_file', job_id=job_id)

    ret = {
        'success': True,
        'result': job_status,
        'download_url': proxy_download_url,
    }
    return _finish_ok(ret)


@activityinfo_bp.route('/download-file/<job_id>')
def download_file(job_id):
    """Proxy download endpoint that fetches the file server-side.

    This avoids the 307 redirect issue where ActivityInfo redirects to
    a GCS signed URL and the browser forwards the Authorization header,
    causing GCS to reject the request.
    """
    token = get_user_token(current_user.name)
    if not token:
        return toolkit.abort(403, "No ActivityInfo API key configured")

    client = ActivityInfoClient(api_key=token)

    try:
        job_data = client.get_job_status(job_id)
    except Exception as e:
        log.error(f"Failed to get job status for {job_id}: {e}")
        return toolkit.abort(500, f"Failed to get export job status: {e}")

    if job_data.get('state') != 'completed':
        state = job_data.get('state', 'unknown')
        return toolkit.abort(400, f"Export job is not completed (state: {state})")

    result = job_data.get('result', {})
    download_url = result.get('downloadUrl', '')
    if not download_url:
        return toolkit.abort(500, "Export completed but no download URL provided")

    if not download_url.startswith('http'):
        download_url = f"{client.base_url}/{download_url.lstrip('/')}"

    try:
        file_content = client.download_file(download_url)
    except Exception as e:
        log.error(f"Failed to download file for job {job_id}: {e}")
        return toolkit.abort(502, f"Failed to download file from ActivityInfo: {e}")

    # Determine content type and filename from the URL
    if download_url.endswith('.xlsx'):
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f"export-{job_id}.xlsx"
    elif download_url.endswith('.txt'):
        content_type = 'text/plain'
        filename = f"export-{job_id}.txt"
    else:
        content_type = 'text/csv'
        filename = f"export-{job_id}.csv"

    return Response(
        file_content,
        mimetype=content_type,
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

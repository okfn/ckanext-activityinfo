import logging
from requests.exceptions import HTTPError
from ckan.plugins import toolkit
from ckanext.activityinfo.utils import get_user_token
from ckanext.activityinfo.data.base import ActivityInfoClient
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError


log = logging.getLogger(__name__)


@toolkit.side_effect_free
def act_info_get_databases(context, data_dict):
    '''
    Action function to get ActivityInfo databases for a user.
    '''
    toolkit.check_access('act_info_get_databases', context, data_dict)
    user = context.get('user')
    log.debug(f"Getting ActivityInfo databases for user {user}")
    token = get_user_token(user)
    aic = ActivityInfoClient(api_key=token)
    try:
        databases = aic.get_databases()
    except HTTPError as e:
        # We can expect a HTTPError 401 Client Error: Unauthorized for url: https://www.activityinfo.org/resources/databases
        # for users with an invalid API key
        error = f"Error retrieving databases for user {user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    return databases


@toolkit.side_effect_free
def act_info_get_forms(context, data_dict):
    '''
    Action function to get ActivityInfo forms for a database.
    '''
    toolkit.check_access('act_info_get_forms', context, data_dict)
    user = context.get('user')
    database_id = data_dict.get('database_id')
    if not database_id:
        raise toolkit.ValidationError({'database_id': 'Missing value'})

    log.debug(f"Getting ActivityInfo forms for database {database_id} and user {user}")
    token = get_user_token(user)
    aic = ActivityInfoClient(api_key=token)
    try:
        data = aic.get_forms(database_id, include_db_data=True)
    except HTTPError as e:
        error = f"Error retrieving forms for database {database_id} and user {user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    ret = {
        'forms': data['forms'],
        'sub_forms': data.get('sub_forms', []),
        'database': data['database']
    }
    return ret


@toolkit.side_effect_free
def act_info_get_form(context, data_dict):
    '''
    Action function to get a specific ActivityInfo form.
    '''
    toolkit.check_access('act_info_get_form', context, data_dict)
    user = context.get('user')
    database_id = data_dict.get('database_id')
    form_id = data_dict.get('form_id')
    if not database_id:
        raise toolkit.ValidationError({'database_id': 'Missing value'})
    if not form_id:
        raise toolkit.ValidationError({'form_id': 'Missing value'})

    log.debug(f"Getting ActivityInfo form {form_id} for database {database_id} and user {user}")
    token = get_user_token(user)
    aic = ActivityInfoClient(api_key=token)
    try:
        form = aic.get_form(database_id, form_id)
    except HTTPError as e:
        error = f"Error retrieving form {form_id} for database {database_id} and user {user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    return form


def act_start_download_job(context, data_dict):
    '''
    Action function to start an ActivityInfo export job to download form data.
    '''
    toolkit.check_access('act_start_download_job', context, data_dict)
    user = context.get('user')
    form_id = data_dict.get('form_id')
    format = data_dict.get('format', 'CSV')
    if not form_id:
        raise toolkit.ValidationError({'form_id': 'Missing value'})

    log.debug(f"Starting ActivityInfo download job for form {form_id} and user {user}")
    token = get_user_token(user)
    aic = ActivityInfoClient(api_key=token)
    try:
        job_info = aic.start_job_download_form_data(form_id, format=format)
    except HTTPError as e:
        error = f"Error starting download job for form {form_id} and user {user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    return job_info


@toolkit.side_effect_free
def act_info_get_job_status(context, data_dict):
    '''
    Action function to get the status of an ActivityInfo export job.
    '''
    toolkit.check_access('act_info_get_job_status', context, data_dict)
    user = context.get('user')
    job_id = data_dict.get('job_id')
    if not job_id:
        raise toolkit.ValidationError({'job_id': 'Missing value'})

    log.debug(f"Getting ActivityInfo job status for job {job_id} and user {user}")
    token = get_user_token(user)
    aic = ActivityInfoClient(api_key=token)
    try:
        job_status = aic.get_job_status(job_id)
    except HTTPError as e:
        error = f"Error retrieving job status for job {job_id} and user {user}: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    return job_status

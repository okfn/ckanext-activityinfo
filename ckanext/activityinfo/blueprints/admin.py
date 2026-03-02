import logging
from flask import Blueprint
from ckan.plugins import toolkit
from ckanext.activityinfo.helpers import get_activityinfo_enable_flag
from ckanext.activityinfo.utils import (
    require_sysadmin_user,
    get_ai_resources,
    get_users_with_activity_info_token,
)


log = logging.getLogger(__name__)
activityinfo_admin_blueprint = Blueprint('activity_info_admin', __name__, url_prefix='/activityinfo/admin')


@activityinfo_admin_blueprint.route('/')
@require_sysadmin_user
def index():
    """ Display ActivityInfo admin configuration
        We show a list of all users with ActivityInfo API keys
        and also all resources linked to ActivityInfo databases
    """
    log.info('ActivityInfo admin index view')
    if not get_activityinfo_enable_flag():
        log.warning('ActivityInfo admin page accessed but ActivityInfo is disabled via feature flag')
        toolkit.h.flash_notice('ActivityInfo is currently disabled. Enable it in the configuration to use this page.')
        return toolkit.redirect_to('admin.index')

    ai_users = get_users_with_activity_info_token()
    ai_resources = get_ai_resources()

    ctx = {
        'ai_users': ai_users,
        'ai_resources': ai_resources,
    }
    return toolkit.render('activity_info/admin.html', ctx)

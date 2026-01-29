import logging
from flask import Blueprint
from ckan.plugins import toolkit
from ckanext.activityinfo.utils import require_sysadmin_user, get_ai_resources


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

    ai_users = []
    ai_resources = get_ai_resources()

    ctx = {
        'ai_users': ai_users,
        'ai_resources': ai_resources,
    }
    return toolkit.render('activity_info/admin.html', ctx)

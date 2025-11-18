from flask import Blueprint
from ckan.plugins import toolkit


activityinfo_bp = Blueprint('activity_info', __name__, url_prefix='/activity-info')


@activityinfo_bp.route('/')
def index():
    extra_vars = {}
    return toolkit.render('activity_info/index.html', extra_vars)


@activityinfo_bp.route('/update-api-key', methods=['POST'])
def update_api_key():
    pass


@activityinfo_bp.route('/remove-api-key', methods=['POST'])
def remove_api_key():
    pass

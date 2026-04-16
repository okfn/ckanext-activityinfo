import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from ckan.plugins import toolkit
from ckan import model
from sqlalchemy import and_, cast
from sqlalchemy.dialects.postgresql import JSONB


log = logging.getLogger(__name__)

# Valid values for the activityinfo_auto_update field.
# 'never' means auto-update is disabled.
VALID_AUTO_UPDATE_VALUES = ('never', 'daily', 'weekly')
SCHEDULABLE_AUTO_UPDATE_VALUES = ('daily', 'weekly')

# Resource.extras is stored as UnicodeText (JSON string), not native JSONB.
# Cast it to JSONB so we can use PostgreSQL JSON operators in queries.
_extras_jsonb = cast(model.Resource.extras, JSONB)


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


def get_ckan_resources(form_id):
    """ Search for internal resources linked to the given ActivityInfo form ID
    Args:
        form_id: The ActivityInfo form ID
    Returns:
        A list of tuples (resource_name, resource_url)
    """
    resources = model.Session.query(model.Resource).filter(
        and_(
            model.Resource.state == 'active',
            _extras_jsonb['activityinfo_form_id'].astext == form_id,
        )
    ).all()

    ret = []
    for res in resources:
        pkg = toolkit.get_action('package_show')(
            {'ignore_auth': True}, {'id': res.package_id}
        )
        pkg_type = pkg.get('type', 'dataset')
        resource_url = toolkit.url_for(
            f'{pkg_type}_resource.read', id=pkg['name'], resource_id=res.id
        )
        ret.append(
            (res.name or 'Unnamed resource', resource_url)
        )

    return ret


def get_ai_resources(limit=100):
    """ Search for all resources linked to any ActivityInfo form ID
    Args:
        limit: Maximum number of resources to return, default 100
    Returns:
        A list of resources with their URLs
    """
    resources = model.Session.query(model.Resource).filter(
        and_(
            model.Resource.state == 'active',
            _extras_jsonb['activityinfo_status'].astext == 'complete',
        )
    ).limit(limit).all()

    ret = []
    for res in resources:
        pkg = toolkit.get_action('package_show')(
            {'ignore_auth': True}, {'id': res.package_id}
        )
        pkg_type = pkg.get('type', 'dataset')
        resource_url = toolkit.url_for(
            f'{pkg_type}_resource.read', id=pkg['name'], resource_id=res.id
        )
        res_dict = res.as_dict()
        res_dict['final_url'] = resource_url
        res_dict['package'] = pkg
        ret.append(res_dict)

    return ret


def get_users_with_activity_info_token():
    """
    Get all users that have an ActivityInfo API key set in their plugin_extras.
    Uses SQLAlchemy to query the JSONB plugin_extras column.

    Returns:
        A list of user objects with ActivityInfo API keys.
    """
    # Query users where plugin_extras -> 'activity_info' -> 'api_key' exists and is not null
    # Use chained -> operators: plugin_extras -> 'activity_info' ->> 'api_key'
    users = model.Session.query(model.User).filter(
        and_(
            model.User.state == 'active',
            model.User.plugin_extras.isnot(None),
            model.User.plugin_extras['activity_info'].isnot(None),
            model.User.plugin_extras['activity_info']['api_key'].astext.isnot(None),
            model.User.plugin_extras['activity_info']['api_key'].astext != '',
        )
    ).all()

    final_users = []
    for user in users:
        final_users.append({
            'id': user.id,
            'name': user.name,
        })

    return final_users


def get_resources_due_for_auto_update():
    """Find all ActivityInfo resources that are due for automatic update.

    A resource is due when:
    - activityinfo_auto_update is 'daily' or 'weekly'
    - activityinfo_status is 'complete' (not currently processing)
    - activityinfo_auto_update_count < activityinfo_auto_update_runs
    - Enough time has passed since activityinfo_last_updated
      (24h for daily, 7 days for weekly), or never updated yet

    Returns:
        A list of resource dicts that need updating.
    """
    now = datetime.now(timezone.utc)

    # Query resources with auto-update enabled and status complete
    resources = model.Session.query(model.Resource).filter(
        and_(
            model.Resource.state == 'active',
            _extras_jsonb['activityinfo_status'].astext == 'complete',
            _extras_jsonb['activityinfo_auto_update'].astext.in_(
                SCHEDULABLE_AUTO_UPDATE_VALUES
            ),
        )
    ).all()

    due_resources = []
    for res in resources:
        extras = res.extras or {}
        frequency = extras.get('activityinfo_auto_update')
        max_runs = _safe_int(extras.get('activityinfo_auto_update_runs'), 1)
        current_count = _safe_int(extras.get('activityinfo_auto_update_count'), 0)

        # Check run limit
        if current_count >= max_runs:
            log.debug(
                f"Skipping resource {res.id}: "
                f"run limit reached ({current_count}/{max_runs})"
            )
            continue

        # Check timing
        last_updated = extras.get('activityinfo_last_updated')
        if last_updated:
            try:
                last_dt = datetime.fromisoformat(last_updated)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                if frequency == 'daily' and (now - last_dt) < timedelta(hours=24):
                    log.debug(
                        f"Skipping resource {res.id}: "
                        f"last updated {last_updated}, not yet due (daily)"
                    )
                    continue
                if frequency == 'weekly' and (now - last_dt) < timedelta(days=7):
                    log.debug(
                        f"Skipping resource {res.id}: "
                        f"last updated {last_updated}, not yet due (weekly)"
                    )
                    continue
            except (ValueError, TypeError):
                pass

        due_resources.append(res.as_dict())

    return due_resources


def _safe_int(value, default=0):
    """Safely convert a value to int, returning default on failure."""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def require_sysadmin_user(func):
    '''
    Decorator for flask view functions. Returns 403 response if no user is logged in or if the login user is external
    '''

    @wraps(func)
    def view_wrapper(*args, **kwargs):
        if not toolkit.current_user or toolkit.current_user.is_anonymous:
            return toolkit.abort(403, "Forbidden")
        if not toolkit.current_user.sysadmin:
            return toolkit.abort(403, "Sysadmin user required")
        return func(*args, **kwargs)

    return view_wrapper

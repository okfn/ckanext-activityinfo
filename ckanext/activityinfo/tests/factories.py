from ckantoolkit.tests import factories
import factory


def _generate_plugin_extras(user):
    plugin_extras = {'activity_info': {'api_key': "api_key_{}".format(user.name)}}
    return plugin_extras


class ActivityInfoUser(factories.UserWithToken):
    plugin_extras = factory.LazyAttribute(_generate_plugin_extras)


class ActivityInfoResource(factories.Resource):
    url = 'activityinfo.waiting.csv'
    format = 'CSV'
    activityinfo_form_id = factory.Sequence(lambda n: "form_{0:05d}".format(n))
    activityinfo_database_id = factory.Sequence(lambda n: "db_{0:05d}".format(n))
    activityinfo_form_label = 'Test Form'
    activityinfo_status = 'complete'
    activityinfo_progress = 100
    activityinfo_error = ''
    activityinfo_format = 'csv'
    activityinfo_auto_update = 'never'
    activityinfo_auto_update_runs = 1

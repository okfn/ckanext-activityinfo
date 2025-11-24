from ckantoolkit.tests import factories
import factory


def _generate_plugin_extras(user):
    plugin_extras = {'activityinfo': {'api_key': "test_api_key_{}".format(user.name)}}
    return plugin_extras


class ActivityInfoUser(factories.User):
    plugin_extras = factory.LazyAttribute(_generate_plugin_extras)

from ckantoolkit.tests import factories
import factory


def _generate_plugin_extras(user):
    plugin_extras = {'activity_info': {'api_key': "api_key_{}".format(user.name)}}
    return plugin_extras


class ActivityInfoUser(factories.UserWithToken):
    plugin_extras = factory.LazyAttribute(_generate_plugin_extras)

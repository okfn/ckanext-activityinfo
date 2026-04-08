from types import SimpleNamespace
import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.tests import factories


@pytest.fixture
def setup_data():
    obj = SimpleNamespace()
    obj.activityinfo_user = factories.ActivityInfoUser()
    obj.regular_user = ckan_factories.UserWithToken()
    return obj


@pytest.mark.usefixtures("clean_db")
class TestAutoUpdateFieldsOnCreate:

    def test_create_resource_with_auto_update_daily(self, setup_data):
        """Test creating a resource with daily auto-update."""
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
        )
        result = toolkit.get_action('resource_show')(
            context={'user': setup_data.activityinfo_user['name']},
            data_dict={'id': resource['id']}
        )
        assert result['activityinfo_auto_update'] == 'daily'
        assert int(result['activityinfo_auto_update_runs']) == 5

    def test_create_resource_with_auto_update_weekly(self, setup_data):
        """Test creating a resource with weekly auto-update."""
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='weekly',
            activityinfo_auto_update_runs=10,
        )
        result = toolkit.get_action('resource_show')(
            context={'user': setup_data.activityinfo_user['name']},
            data_dict={'id': resource['id']}
        )
        assert result['activityinfo_auto_update'] == 'weekly'
        assert int(result['activityinfo_auto_update_runs']) == 10

    def test_create_resource_with_auto_update_never(self, setup_data):
        """Test creating a resource with never auto-update (default)."""
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='never',
            activityinfo_auto_update_runs=1,
        )
        result = toolkit.get_action('resource_show')(
            context={'user': setup_data.activityinfo_user['name']},
            data_dict={'id': resource['id']}
        )
        assert result['activityinfo_auto_update'] == 'never'
        assert int(result['activityinfo_auto_update_runs']) == 1

    def test_create_resource_defaults(self, setup_data):
        """Test that default values are set when auto-update fields are not provided."""
        resource = factories.ActivityInfoResource()
        result = toolkit.get_action('resource_show')(
            context={'user': setup_data.activityinfo_user['name']},
            data_dict={'id': resource['id']}
        )
        assert result['activityinfo_auto_update'] == 'never'
        assert int(result['activityinfo_auto_update_runs']) == 1

    def test_create_resource_invalid_auto_update_value(self, setup_data):
        """Test that invalid auto-update frequency is rejected."""
        with pytest.raises(toolkit.ValidationError) as exc_info:
            factories.ActivityInfoResource(
                activityinfo_auto_update='monthly',
            )
        assert 'activityinfo_auto_update' in exc_info.value.error_dict

    def test_create_resource_invalid_runs_zero(self, setup_data):
        """Test that 0 runs is rejected."""
        with pytest.raises(toolkit.ValidationError) as exc_info:
            factories.ActivityInfoResource(
                activityinfo_auto_update_runs=0,
            )
        assert 'activityinfo_auto_update_runs' in exc_info.value.error_dict

    def test_create_resource_invalid_runs_too_high(self, setup_data):
        """Test that runs > 20 is rejected."""
        with pytest.raises(toolkit.ValidationError) as exc_info:
            factories.ActivityInfoResource(
                activityinfo_auto_update_runs=21,
            )
        assert 'activityinfo_auto_update_runs' in exc_info.value.error_dict

    def test_create_resource_invalid_runs_negative(self, setup_data):
        """Test that negative runs is rejected."""
        with pytest.raises(toolkit.ValidationError) as exc_info:
            factories.ActivityInfoResource(
                activityinfo_auto_update_runs=-1,
            )
        assert 'activityinfo_auto_update_runs' in exc_info.value.error_dict

    def test_create_resource_invalid_runs_not_a_number(self, setup_data):
        """Test that non-numeric runs is rejected."""
        with pytest.raises(toolkit.ValidationError) as exc_info:
            factories.ActivityInfoResource(
                activityinfo_auto_update_runs='abc',
            )
        assert 'activityinfo_auto_update_runs' in exc_info.value.error_dict


@pytest.mark.usefixtures("clean_db")
class TestAutoUpdateFieldsOnUpdate:

    def test_update_resource_auto_update(self, setup_data):
        """Test updating auto-update frequency on an existing resource."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='never',
            activityinfo_auto_update_runs=1,
        )

        updated = toolkit.get_action('resource_update')(
            context={'user': user_name},
            data_dict={
                'id': resource['id'],
                'package_id': resource['package_id'],
                'url': resource['url'],
                'activityinfo_auto_update': 'daily',
                'activityinfo_auto_update_runs': 7,
            }
        )
        assert updated['activityinfo_auto_update'] == 'daily'
        assert int(updated['activityinfo_auto_update_runs']) == 7

    def test_update_resource_auto_update_to_weekly(self, setup_data):
        """Test changing auto-update from daily to weekly."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
        )

        updated = toolkit.get_action('resource_update')(
            context={'user': user_name},
            data_dict={
                'id': resource['id'],
                'package_id': resource['package_id'],
                'url': resource['url'],
                'activityinfo_auto_update': 'weekly',
                'activityinfo_auto_update_runs': 20,
            }
        )
        assert updated['activityinfo_auto_update'] == 'weekly'
        assert int(updated['activityinfo_auto_update_runs']) == 20

    def test_update_resource_invalid_auto_update_value(self, setup_data):
        """Test that invalid auto-update frequency is rejected on update."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource()

        with pytest.raises(toolkit.ValidationError) as exc_info:
            toolkit.get_action('resource_update')(
                context={'user': user_name},
                data_dict={
                    'id': resource['id'],
                    'package_id': resource['package_id'],
                    'url': resource['url'],
                    'activityinfo_auto_update': 'hourly',
                }
            )
        assert 'activityinfo_auto_update' in exc_info.value.error_dict

    def test_update_resource_invalid_runs_too_high(self, setup_data):
        """Test that runs > 20 is rejected on update."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource()

        with pytest.raises(toolkit.ValidationError) as exc_info:
            toolkit.get_action('resource_update')(
                context={'user': user_name},
                data_dict={
                    'id': resource['id'],
                    'package_id': resource['package_id'],
                    'url': resource['url'],
                    'activityinfo_auto_update_runs': 21,
                }
            )
        assert 'activityinfo_auto_update_runs' in exc_info.value.error_dict

    def test_update_resource_invalid_runs_zero(self, setup_data):
        """Test that 0 runs is rejected on update."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource()

        with pytest.raises(toolkit.ValidationError) as exc_info:
            toolkit.get_action('resource_update')(
                context={'user': user_name},
                data_dict={
                    'id': resource['id'],
                    'package_id': resource['package_id'],
                    'url': resource['url'],
                    'activityinfo_auto_update_runs': 0,
                }
            )
        assert 'activityinfo_auto_update_runs' in exc_info.value.error_dict

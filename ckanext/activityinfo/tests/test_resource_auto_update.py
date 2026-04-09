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


@pytest.mark.usefixtures("clean_db")
class TestActivityInfoMetadataPreservedOnUpdate:
    """Ensure ActivityInfo metadata fields survive resource updates.

    When a user edits a resource (e.g. changes the name), the ActivityInfo
    fields (form_id, status, etc.) must not be wiped.
    """

    def test_metadata_preserved_when_updating_name(self, setup_data):
        """Updating only the name should preserve all ActivityInfo fields."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_form_id='form_abc',
            activityinfo_database_id='db_xyz',
            activityinfo_form_label='My Form',
            activityinfo_status='complete',
            activityinfo_progress=100,
            activityinfo_format='csv',
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
        )

        updated = toolkit.get_action('resource_update')(
            context={'user': user_name},
            data_dict={
                'id': resource['id'],
                'package_id': resource['package_id'],
                'url': resource['url'],
                'name': 'New Resource Name',
                # Simulates what the form submits via hidden fields
                'activityinfo_form_id': resource['activityinfo_form_id'],
                'activityinfo_database_id': resource['activityinfo_database_id'],
                'activityinfo_form_label': resource['activityinfo_form_label'],
                'activityinfo_status': resource['activityinfo_status'],
                'activityinfo_progress': resource['activityinfo_progress'],
                'activityinfo_format': resource['activityinfo_format'],
                'activityinfo_auto_update': resource['activityinfo_auto_update'],
                'activityinfo_auto_update_runs': resource['activityinfo_auto_update_runs'],
            }
        )

        assert updated['name'] == 'New Resource Name'
        assert updated['activityinfo_form_id'] == 'form_abc'
        assert updated['activityinfo_database_id'] == 'db_xyz'
        assert updated['activityinfo_form_label'] == 'My Form'
        assert updated['activityinfo_status'] == 'complete'
        assert int(updated['activityinfo_progress']) == 100
        assert updated['activityinfo_format'] == 'csv'
        assert updated['activityinfo_auto_update'] == 'daily'
        assert int(updated['activityinfo_auto_update_runs']) == 5

    def test_metadata_preserved_when_changing_auto_update(self, setup_data):
        """Changing auto-update settings should preserve other AI fields."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_form_id='form_123',
            activityinfo_database_id='db_456',
            activityinfo_form_label='Test Form',
            activityinfo_status='complete',
            activityinfo_format='xlsx',
            activityinfo_auto_update='never',
            activityinfo_auto_update_runs=1,
        )

        updated = toolkit.get_action('resource_update')(
            context={'user': user_name},
            data_dict={
                'id': resource['id'],
                'package_id': resource['package_id'],
                'url': resource['url'],
                'activityinfo_form_id': resource['activityinfo_form_id'],
                'activityinfo_database_id': resource['activityinfo_database_id'],
                'activityinfo_form_label': resource['activityinfo_form_label'],
                'activityinfo_status': resource['activityinfo_status'],
                'activityinfo_format': resource['activityinfo_format'],
                'activityinfo_auto_update': 'weekly',
                'activityinfo_auto_update_runs': 10,
            }
        )

        assert updated['activityinfo_form_id'] == 'form_123'
        assert updated['activityinfo_database_id'] == 'db_456'
        assert updated['activityinfo_form_label'] == 'Test Form'
        assert updated['activityinfo_status'] == 'complete'
        assert updated['activityinfo_format'] == 'xlsx'
        assert updated['activityinfo_auto_update'] == 'weekly'
        assert int(updated['activityinfo_auto_update_runs']) == 10

    def test_resource_still_detected_as_activityinfo_after_update(self, setup_data):
        """After update, is_activityinfo_resource should still return True."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_form_id='form_detect',
        )

        updated = toolkit.get_action('resource_update')(
            context={'user': user_name},
            data_dict={
                'id': resource['id'],
                'package_id': resource['package_id'],
                'url': resource['url'],
                'name': 'Changed Name',
                'activityinfo_form_id': resource['activityinfo_form_id'],
                'activityinfo_database_id': resource.get('activityinfo_database_id', ''),
                'activityinfo_form_label': resource.get('activityinfo_form_label', ''),
                'activityinfo_status': resource.get('activityinfo_status', ''),
                'activityinfo_format': resource.get('activityinfo_format', ''),
            }
        )

        from ckanext.activityinfo.helpers import is_activityinfo_resource
        assert is_activityinfo_resource(updated) is True
        assert updated['activityinfo_form_id'] == 'form_detect'

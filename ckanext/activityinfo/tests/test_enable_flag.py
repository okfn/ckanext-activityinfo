from unittest import mock
from types import SimpleNamespace
import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.helpers import get_activityinfo_enable_flag
from ckanext.activityinfo.tests import factories


@pytest.fixture
def setup_data():
    """Test setup data."""
    obj = SimpleNamespace()
    obj.activityinfo_user = factories.ActivityInfoUser()
    obj.sysadmin = ckan_factories.SysadminWithToken()
    obj.regular_user = ckan_factories.UserWithToken()
    return obj


class TestGetActivityinfoEnableFlag:
    """Tests for the get_activityinfo_enable_flag helper function."""

    def test_default_is_enabled(self):
        """When no config is set, the flag defaults to True."""
        assert get_activityinfo_enable_flag() is True

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'true')
    def test_explicit_true(self):
        """When config is explicitly 'true', returns True."""
        assert get_activityinfo_enable_flag() is True

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'false')
    def test_explicit_false(self):
        """When config is explicitly 'false', returns False."""
        assert get_activityinfo_enable_flag() is False


@pytest.mark.usefixtures("clean_db")
class TestActivityInfoBlueprintDisabled:
    """Tests that blueprints redirect when the feature flag is disabled."""

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'false')
    def test_user_index_redirects_when_disabled(self, app, setup_data):
        """User blueprint redirects to home when flag is disabled."""
        url = toolkit.url_for('activity_info.index')
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ, follow_redirects=False)
        assert resp.status_code == 302

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'false')
    def test_user_index_shows_flash_warning_when_disabled(self, app, setup_data):
        """User blueprint shows a warning flash message when flag is disabled."""
        url = toolkit.url_for('activity_info.index')
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ, follow_redirects=True)
        assert 'ActivityInfo is currently disabled' in resp.body

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'false')
    def test_admin_index_redirects_when_disabled(self, app, setup_data):
        """Admin blueprint redirects to admin index when flag is disabled."""
        url = toolkit.url_for('activity_info_admin.index')
        environ = {"Authorization": setup_data.sysadmin["token"]}
        resp = app.get(url, headers=environ, follow_redirects=False)
        assert resp.status_code == 302

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'false')
    def test_admin_index_shows_flash_warning_when_disabled(self, app, setup_data):
        """Admin blueprint shows a warning flash message when flag is disabled."""
        url = toolkit.url_for('activity_info_admin.index')
        environ = {"Authorization": setup_data.sysadmin["token"]}
        resp = app.get(url, headers=environ, follow_redirects=True)
        assert 'ActivityInfo is currently disabled' in resp.body


@pytest.mark.usefixtures("clean_db")
class TestActivityInfoBlueprintEnabled:
    """Tests that blueprints work normally when the feature flag is enabled."""

    def test_user_index_accessible_when_enabled_by_default(self, app, setup_data):
        """User blueprint works normally with default config (enabled)."""
        url = toolkit.url_for('activity_info.index')
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'true')
    def test_user_index_accessible_when_explicitly_enabled(self, app, setup_data):
        """User blueprint works normally when explicitly enabled."""
        url = toolkit.url_for('activity_info.index')
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'true')
    def test_activityinfo_user_index_redirects_to_databases(self, app, setup_data):
        """User with API key gets redirected to databases when enabled."""
        url = toolkit.url_for('activity_info.index')
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        fake_databases = [{"databaseId": "0001", "label": "DB 01"}]
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_databases",
            return_value=fake_databases,
        ):
            resp = app.get(url, headers=environ, follow_redirects=True)
            assert resp.status_code == 200


@pytest.mark.usefixtures("clean_db")
class TestUserReadNavLink:
    """Tests that the Activity Info nav link on user profile respects the flag."""

    def test_user_read_shows_nav_link_when_enabled_by_default(self, app, setup_data):
        """User profile page shows Activity Info nav link with default config."""
        url = toolkit.url_for('user.read', id=setup_data.regular_user["name"])
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200
        assert 'Activity Info' in resp.body

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'true')
    def test_user_read_shows_nav_link_when_explicitly_enabled(self, app, setup_data):
        """User profile page shows Activity Info nav link when flag is true."""
        url = toolkit.url_for('user.read', id=setup_data.regular_user["name"])
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200
        assert 'Activity Info' in resp.body

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'false')
    def test_user_read_hides_nav_link_when_disabled(self, app, setup_data):
        """User profile page hides Activity Info nav link when flag is false."""
        url = toolkit.url_for('user.read', id=setup_data.regular_user["name"])
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200
        assert 'Activity Info' not in resp.body


@pytest.mark.usefixtures("clean_db")
class TestNewResourceActivityInfoButton:
    """Tests that the Activity Info button on new resource form respects the flag."""

    @pytest.fixture
    def dataset(self, setup_data):
        """Create a dataset owned by the activityinfo user."""
        return ckan_factories.Dataset(
            user=setup_data.activityinfo_user,
        )

    def test_new_resource_shows_button_when_enabled_by_default(self, app, setup_data, dataset):
        """New resource form shows Activity Info button with default config for AI user."""
        url = toolkit.url_for('dataset_resource.new', id=dataset['id'])
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200
        assert 'btn-activity-info' in resp.body

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'true')
    def test_new_resource_shows_button_when_explicitly_enabled(self, app, setup_data, dataset):
        """New resource form shows Activity Info button when flag is true for AI user."""
        url = toolkit.url_for('dataset_resource.new', id=dataset['id'])
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200
        assert 'btn-activity-info' in resp.body

    @pytest.mark.ckan_config('ckanext.activityinfo.activityinfo_enabled', 'false')
    def test_new_resource_hides_button_when_disabled(self, app, setup_data, dataset):
        """New resource form hides Activity Info button when flag is false."""
        url = toolkit.url_for('dataset_resource.new', id=dataset['id'])
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200
        assert 'btn-activity-info' not in resp.body

    def test_new_resource_hides_button_for_user_without_api_key(self, app, setup_data, dataset):
        """New resource form hides Activity Info button for users without API key."""
        url = toolkit.url_for('dataset_resource.new', id=dataset['id'])
        environ = {"Authorization": setup_data.regular_user["token"]}
        resp = app.get(url, headers=environ)
        assert resp.status_code == 200
        assert 'btn-activity-info' not in resp.body

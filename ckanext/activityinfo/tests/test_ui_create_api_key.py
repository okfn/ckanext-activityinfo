import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories


@pytest.mark.usefixtures("clean_db")
class TestCreateApiKey:
    def test_create_api_key_success(self, app):
        user_no_api_key = ckan_factories.UserWithToken()
        environ = {"Authorization": user_no_api_key["token"]}
        api_key = "test-activityinfo-api-key"

        url = toolkit.url_for("activity_info.update_api_key")
        resp = app.post(
            url,
            params={"activityinfo_api_key": api_key},
            headers=environ,
        )
        # Should redirect to index after success
        assert resp.status_code == 200
        assert "ActivityInfo API key updated successfully" in resp.body

    def test_create_api_key_missing(self, app):
        user_no_api_key = ckan_factories.UserWithToken()
        environ = {"Authorization": user_no_api_key["token"]}
        url = toolkit.url_for("activity_info.update_api_key")
        resp = app.post(
            url,
            params={},  # No api_key provided
            headers=environ,
        )
        # Should redirect to index after error and display error message
        assert 'Missing ActivityInfo API key' in resp.body

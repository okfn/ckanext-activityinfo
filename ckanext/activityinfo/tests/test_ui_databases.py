from unittest import mock
import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError


@pytest.mark.usefixtures("clean_db")
class TestDatabasesView:
    def test_databases_success(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_databases = [
            {
                "databaseId": "0001",
                "label": "Database label 01",
                "description": "",
                "ownerId": "999999999",
                "billingAccountId": 8888888888888888,
                "suspended": False,
                "publishedTemplate": False,
                "languages": []
            },
            {
                "databaseId": "0002",
                "label": "Database label 02",
                "description": "",
                "ownerId": "999999999",
                "billingAccountId": 8888888888888888,
                "suspended": False,
                "publishedTemplate": False,
                "languages": []
            }
        ]

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_databases",
            return_value=fake_databases,
        ):
            url = toolkit.url_for("activity_info.databases")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            assert "Database label 01" in resp.text
            assert "Database label 02" in resp.text

    def test_databases_no_api_key_user(self, app):
        user = ckan_factories.UserWithToken()
        environ = {"Authorization": user["token"]}

        # expected error
        # NotAuthorized: No ActivityInfo token found for user XXXX.
        with pytest.raises(toolkit.NotAuthorized) as excinfo:
            url = toolkit.url_for("activity_info.databases")
            app.get(url, headers=environ)
        assert "No ActivityInfo token found for user" in str(excinfo.value)

    def test_databases_connection_error(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_databases",
            side_effect=ActivityInfoConnectionError("Connection failed"),
        ):
            url = toolkit.url_for("activity_info.databases")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 302 or resp.status_code == 200
            # Should redirect or flash error, but not show databases

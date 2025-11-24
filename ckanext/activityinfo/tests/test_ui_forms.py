from unittest import mock
import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError


@pytest.mark.usefixtures("clean_db")
class TestFormsView:
    def test_forms_success(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_forms = [
            {
                "id": "form01",
                "label": "Form label 01",
                "type": "FORM"
            },
            {
                "id": "form02",
                "label": "Form label 02",
                "type": "FORM"
            }
        ]
        fake_database = {
            "databaseId": "db01",
            "label": "Database label 01",
            "resources": fake_forms
        }
        fake_data = {
            "forms": fake_forms,
            "database": fake_database
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            return_value=fake_data,
        ):
            url = toolkit.url_for("activity_info.forms", database_id="db01")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            assert "Form label 01" in resp.body
            assert "Form label 02" in resp.body
            assert "Database label 01" in resp.body

    def test_forms_no_api_key_user(self, app):
        user = ckan_factories.UserWithToken()
        environ = {"Authorization": user["token"]}
        with pytest.raises(toolkit.NotAuthorized) as excinfo:
            url = toolkit.url_for("activity_info.forms", database_id="db01")
            app.get(url, headers=environ)
        assert "No ActivityInfo token found for user" in str(excinfo.value)

    def test_forms_connection_error(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            side_effect=ActivityInfoConnectionError("Connection failed"),
        ):
            url = toolkit.url_for("activity_info.forms", database_id="db01")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 302 or resp.status_code == 200
            # Should redirect or flash error, but not show forms

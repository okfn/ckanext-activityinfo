from unittest import mock
import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError


@pytest.mark.usefixtures("clean_db")
class TestFormView:
    def test_form_success(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_form_id = "form01"
        fake_database_id = "db01"
        fake_form = {
            "id": fake_form_id,
            "label": "Form label 01",
            "schema": {
                "databaseId": fake_database_id,
                "elements": [
                    {"code": "field1", "label": "Field 1"},
                    {"code": "field2", "label": "Field 2"}
                ]
            }
        }
        fake_data = {
            "forms": {fake_form_id: fake_form}
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_form",
            return_value=fake_data,
        ):
            url = toolkit.url_for("activity_info.form", database_id=fake_database_id, form_id=fake_form_id)
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            assert "Form label 01" in resp.body
            assert "Field 1" in resp.body
            assert "Field 2" in resp.body

    def test_form_no_api_key_user(self, app):
        user = ckan_factories.UserWithToken()
        environ = {"Authorization": user["token"]}
        with pytest.raises(toolkit.NotAuthorized) as excinfo:
            url = toolkit.url_for("activity_info.form", database_id="db01", form_id="form01")
            app.get(url, headers=environ)
        assert "No ActivityInfo token found for user" in str(excinfo.value)

    def test_form_connection_error(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_form",
            side_effect=ActivityInfoConnectionError("Connection failed"),
        ):
            url = toolkit.url_for("activity_info.form", database_id="db01", form_id="form01")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 302 or resp.status_code == 200
            # Should redirect or flash error, but not show form details

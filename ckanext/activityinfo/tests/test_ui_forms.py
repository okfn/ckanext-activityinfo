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
            "sub_forms": [],
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

    def test_forms_with_sub_forms_success(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_forms = [
            {
                "id": "form01",
                "label": "Main Form 01",
                "type": "FORM",
                "visibility": "PUBLIC",
                "description": "Main form description"
            }
        ]
        fake_sub_forms = [
            {
                "id": "subform01",
                "label": "Sub Form 01",
                "type": "SUB_FORM",
                "visibility": "PRIVATE",
                "description": "Sub form description"
            },
            {
                "id": "subform02",
                "label": "Sub Form 02",
                "type": "SUB_FORM",
                "visibility": "PUBLIC",
                "description": ""
            }
        ]
        fake_database = {
            "databaseId": "db01",
            "label": "Database label 01",
            "resources": fake_forms + fake_sub_forms
        }
        fake_data = {
            "forms": fake_forms,
            "sub_forms": fake_sub_forms,
            "database": fake_database
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            return_value=fake_data,
        ):
            url = toolkit.url_for("activity_info.forms", database_id="db01")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            # Check main forms are displayed
            assert "Main Form 01" in resp.body
            # Check sub forms section and content
            assert "Sub Forms" in resp.body
            assert "Sub Form 01" in resp.body
            assert "Sub Form 02" in resp.body

    def test_forms_without_sub_forms_no_section(self, app, ai_user_with_api_key):
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_forms = [
            {
                "id": "form01",
                "label": "Form label 01",
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
            "sub_forms": [],
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
            # Sub Forms section should not appear when there are no sub forms
            assert resp.body.count("Sub Forms") == 0

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

    def test_forms_have_format_selector(self, app, ai_user_with_api_key):
        """Test that the forms page includes format selectors for downloads."""
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_forms = [
            {
                "id": "form01",
                "label": "Form label 01",
                "type": "FORM",
                "visibility": "PUBLIC",
                "description": ""
            }
        ]
        fake_database = {
            "databaseId": "db01",
            "label": "Database label 01",
            "resources": fake_forms
        }
        fake_data = {
            "forms": fake_forms,
            "sub_forms": [],
            "database": fake_database
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            return_value=fake_data,
        ):
            url = toolkit.url_for("activity_info.forms", database_id="db01")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            # Check format selector is present
            assert "ai-format-select" in resp.body
            # Check available format options
            assert 'value="CSV"' in resp.body
            assert 'value="XLSX"' in resp.body
            assert 'value="TEXT"' in resp.body
            # Check download button is present
            assert "ai-download-btn" in resp.body
            assert "Download" in resp.body

    def test_forms_download_url_template(self, app, ai_user_with_api_key):
        """Test that download buttons have the correct URL template with format placeholder."""
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_forms = [
            {
                "id": "form01",
                "label": "Form label 01",
                "type": "FORM",
                "visibility": "PUBLIC",
                "description": ""
            }
        ]
        fake_database = {
            "databaseId": "db01",
            "label": "Database label 01",
            "resources": fake_forms
        }
        fake_data = {
            "forms": fake_forms,
            "sub_forms": [],
            "database": fake_database
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            return_value=fake_data,
        ):
            url = toolkit.url_for("activity_info.forms", database_id="db01")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            # Check that the download URL template contains the format placeholder
            assert "data-download-url-template" in resp.body
            assert "__FORMAT__" in resp.body


@pytest.mark.usefixtures("clean_db")
class TestDownloadFormData:
    def test_download_form_data_csv(self, app, ai_user_with_api_key):
        """Test starting a download job with CSV format."""
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_job_info = {
            "id": "job123",
            "state": "started",
            "percentComplete": 0
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.start_job_download_form_data",
            return_value=fake_job_info,
        ) as mock_start_job:
            url = toolkit.url_for("activity_info.download_form_data", form_id="form01", format="csv")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            data = resp.json
            assert data["success"] is True
            assert data["job_id"] == "job123"
            # Verify the format was passed correctly (uppercase)
            mock_start_job.assert_called_once_with("form01", format="CSV")

    def test_download_form_data_xlsx(self, app, ai_user_with_api_key):
        """Test starting a download job with XLSX format."""
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_job_info = {
            "id": "job456",
            "state": "started",
            "percentComplete": 0
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.start_job_download_form_data",
            return_value=fake_job_info,
        ) as mock_start_job:
            url = toolkit.url_for("activity_info.download_form_data", form_id="form01", format="xlsx")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            data = resp.json
            assert data["success"] is True
            assert data["job_id"] == "job456"
            mock_start_job.assert_called_once_with("form01", format="XLSX")

    def test_download_form_data_text(self, app, ai_user_with_api_key):
        """Test starting a download job with TEXT format."""
        user = ai_user_with_api_key
        environ = {"Authorization": user["token"]}
        fake_job_info = {
            "id": "job789",
            "state": "started",
            "percentComplete": 0
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.start_job_download_form_data",
            return_value=fake_job_info,
        ) as mock_start_job:
            url = toolkit.url_for("activity_info.download_form_data", form_id="form01", format="text")
            resp = app.get(url, headers=environ)
            assert resp.status_code == 200
            data = resp.json
            assert data["success"] is True
            mock_start_job.assert_called_once_with("form01", format="TEXT")

    def test_download_form_data_no_api_key(self, app):
        """Test that download fails for users without API key."""
        user = ckan_factories.UserWithToken()
        environ = {"Authorization": user["token"]}
        with pytest.raises(toolkit.NotAuthorized) as excinfo:
            url = toolkit.url_for("activity_info.download_form_data", form_id="form01", format="csv")
            app.get(url, headers=environ)
        assert "No ActivityInfo token found for user" in str(excinfo.value)

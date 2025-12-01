from unittest import mock
from types import SimpleNamespace
import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.tests import factories


@pytest.fixture
def setup_data():
    """test setup data"""
    obj = SimpleNamespace()
    obj.activityinfo_user = factories.ActivityInfoUser()
    obj.regular_user = ckan_factories.UserWithToken()
    return obj


@pytest.mark.usefixtures("clean_db")
class TestDownloadEndpoints:

    def test_download_form_data_starts_job(self, app, setup_data):
        """Test that download endpoint starts an export job"""
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        form_id = "test_form_123"

        fake_job_response = {
            "id": "job_abc123",
            "state": "started",
            "percentComplete": 0
        }

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.start_job_download_form_data",
            return_value=fake_job_response,
        ):
            resp = app.get(f"/activity-info/download/{form_id}", headers=environ)

            assert resp.status_code == 200
            data = resp.json
            assert data["success"] is True
            assert data["job_id"] == "job_abc123"
            assert data["result"]["state"] == "started"

    def test_download_form_data_unauthorized(self, app):
        """Test that download requires authentication"""
        form_id = "test_form_123"
        with pytest.raises(toolkit.NotAuthorized):
            app.get(f"/activity-info/download/{form_id}")

    def test_job_status_in_progress(self, app, setup_data):
        """Test job status endpoint when job is in progress"""
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        job_id = "job_abc123"

        fake_status = {
            "id": job_id,
            "state": "started",
            "percentComplete": 50
        }

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_job_status",
            return_value=fake_status,
        ):
            resp = app.get(f"/activity-info/job-status/{job_id}", headers=environ)

            assert resp.status_code == 200
            data = resp.json
            assert data["success"] is True
            assert data["result"]["state"] == "started"
            assert data["result"]["percentComplete"] == 50
            assert data["download_url"] is None

    def test_job_status_completed(self, app, setup_data):
        """Test job status endpoint when job is completed"""
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        job_id = "job_abc123"

        fake_status = {
            "id": job_id,
            "state": "completed",
            "percentComplete": 100,
            "result": {
                "downloadUrl": "/resources/jobs/job_abc123/download"
            }
        }

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_job_status",
            return_value=fake_status,
        ):
            resp = app.get(f"/activity-info/job-status/{job_id}", headers=environ)

            assert resp.status_code == 200
            data = resp.json
            assert data["success"] is True
            assert data["result"]["state"] == "completed"
            assert data["download_url"] == "https://www.activityinfo.org/resources/jobs/job_abc123/download"

    def test_job_status_failed(self, app, setup_data):
        """Test job status endpoint when job has failed"""
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
        job_id = "job_abc123"

        fake_status = {
            "id": job_id,
            "state": "failed",
            "percentComplete": 0
        }

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_job_status",
            return_value=fake_status,
        ):
            resp = app.get(f"/activity-info/job-status/{job_id}", headers=environ)

            assert resp.status_code == 200
            data = resp.json
            assert data["success"] is True
            assert data["result"]["state"] == "failed"
            assert data["download_url"] is None


@pytest.mark.usefixtures("clean_db")
class TestDownloadActions:

    def test_act_start_download_job_action(self, setup_data):
        """Test the act_start_download_job action"""

        form_id = "test_form_123"
        fake_job_response = {
            "id": "job_abc123",
            "state": "started",
            "percentComplete": 0
        }

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.start_job_download_form_data",
            return_value=fake_job_response,
        ):
            result = toolkit.get_action('act_start_download_job')(
                context={'user': setup_data.activityinfo_user['name']},
                data_dict={'form_id': form_id}
            )

            assert result["id"] == "job_abc123"
            assert result["state"] == "started"

    def test_act_start_download_job_missing_form_id(self, setup_data):
        """Test that act_start_download_job raises error when form_id is missing"""

        with pytest.raises(toolkit.ValidationError) as exc_info:
            toolkit.get_action('act_start_download_job')(
                context={'user': setup_data.activityinfo_user['name']},
                data_dict={}
            )

        assert 'form_id' in str(exc_info.value)

    def test_act_info_get_job_status_action(self, setup_data):
        """Test the act_info_get_job_status action"""

        job_id = "job_abc123"
        fake_status = {
            "id": job_id,
            "state": "completed",
            "percentComplete": 100
        }

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_job_status",
            return_value=fake_status,
        ):
            result = toolkit.get_action('act_info_get_job_status')(
                context={'user': setup_data.activityinfo_user['name']},
                data_dict={'job_id': job_id}
            )

            assert result["id"] == job_id
            assert result["state"] == "completed"

    def test_act_info_get_job_status_missing_job_id(self, setup_data):
        """Test that act_info_get_job_status raises error when job_id is missing"""

        with pytest.raises(toolkit.ValidationError) as exc_info:
            toolkit.get_action('act_info_get_job_status')(
                context={'user': setup_data.activityinfo_user['name']},
                data_dict={}
            )

        assert 'job_id' in str(exc_info.value)

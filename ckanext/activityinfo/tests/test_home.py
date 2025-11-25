from unittest import mock
from types import SimpleNamespace
import pytest
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.tests import factories


@pytest.fixture
def setup_data():
    """test setup data"""
    obj = SimpleNamespace()
    # Create CKAN users
    obj.activityinfo_user = factories.ActivityInfoUser()
    obj.regular_user = ckan_factories.UserWithToken()

    return obj


@pytest.mark.usefixtures("clean_db")
class TestActivityInfoUI:
    def test_regular_user(self, app, setup_data):
        environ = {"Authorization": setup_data.regular_user["token"]}

        resp = app.get("/activity-info", headers=environ)
        assert resp.status_code == 200
        # This must be redirected to the /api-key URL
        assert "Add API key" in resp.body

    def test_activityinfo_user(self, app, setup_data):
        environ = {"Authorization": setup_data.activityinfo_user["token"]}
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
        ]

        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_databases",
            return_value=fake_databases,
        ):
            resp = app.get("/activity-info", headers=environ)
            assert resp.status_code == 200
            # Activity info users will be redirected to see their databases
            assert "Activity Info databases" in resp.body

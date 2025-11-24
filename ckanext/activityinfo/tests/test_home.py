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


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestActivityInfoUI:
    def test_regular_user(self, app, setup_data):
        environ = {"Authorization": setup_data.regular_user["token"]}

        resp = app.get("/activity-info", headers=environ)
        assert resp.status_code == 200
        # CKAN users without a registered ActivityInfo token, will be asked to add one
        assert "Add API key" in resp.body

    def test_activityinfo_user(self, app, setup_data):
        environ = {"Authorization": setup_data.activityinfo_user["token"]}

        resp = app.get("/activity-info", headers=environ)
        assert resp.status_code == 200
        # Activity info users will see the ActivityInfo UI
        assert "Update API key" in resp.body

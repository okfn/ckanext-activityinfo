import pytest
from ckantoolkit.tests import factories as ckan_factories


@pytest.fixture
def user_no_api_key():
    """A CKAN user without an ActivityInfo API key."""
    return ckan_factories.UserWithToken()


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestCreateApiKey:
    def test_create_api_key_success(self, app, user_no_api_key):
        environ = {"Authorization": user_no_api_key["token"]}
        api_key = "test-activityinfo-api-key"

        resp = app.post(
            "/activity-info/update-api-key",
            params={"activityinfo_api_key": api_key},
            headers=environ,
            status=302,
        )
        # Should redirect to index after success
        assert resp.headers["Location"].endswith("/activity-info")

        # Now, check that the API key is stored and visible in the UI
        resp2 = app.get("/activity-info", headers=environ)
        assert resp2.status_code == 200
        assert api_key[:10] in resp2.body  # truncated API key should be visible

    def test_create_api_key_missing(self, app, user_no_api_key):
        environ = {"Authorization": user_no_api_key["token"]}
        resp = app.post(
            "/activity-info/update-api-key",
            params={},  # No api_key provided
            headers=environ,
            status=302,
        )
        # Should redirect to index after error
        assert resp.headers["Location"].endswith("/activity-info")
        # Optionally, could check for error flash message if test client supports it

import pytest
from ckan.plugins import toolkit


@pytest.mark.usefixtures("clean_db")
class TestRemoveApiKey:
    def test_remove_api_key_success(self, app, ai_user_with_api_key):
        environ = {"Authorization": ai_user_with_api_key["token"]}
        url = toolkit.url_for("activity_info.remove_api_key")
        resp = app.post(url, headers=environ)
        assert resp.status_code == 200
        assert "ActivityInfo API key removed successfully" in resp.body

        # Confirm key is no longer visible in UI
        resp2 = app.get(toolkit.url_for("activity_info.index"), headers=environ)
        assert "Current API key" not in resp2.text

    def test_remove_api_key_no_key(self, app, user_no_api_key):
        environ = {"Authorization": user_no_api_key["token"]}
        url = toolkit.url_for("activity_info.remove_api_key")
        resp = app.post(url, headers=environ)
        assert resp.status_code == 200
        assert "No ActivityInfo API key found to remove." in resp.body

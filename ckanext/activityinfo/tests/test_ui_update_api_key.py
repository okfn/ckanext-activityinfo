import pytest
from ckan.plugins import toolkit


@pytest.mark.usefixtures("clean_db")
class TestUpdateApiKey:
    def test_update_api_key_success(self, app, ai_user_with_api_key):
        environ = {"Authorization": ai_user_with_api_key["token"]}
        new_api_key = "new-activityinfo-api-key"

        url = toolkit.url_for("activity_info.update_api_key")
        resp = app.post(
            url,
            params={"activityinfo_api_key": new_api_key},
            headers=environ,
        )
        assert resp.status_code == 200
        assert "ActivityInfo API key updated successfully" in resp.body
        # Confirm new key is visible in UI
        resp2 = app.get(toolkit.url_for("activity_info.index"), headers=environ)
        assert new_api_key[:10] in resp2.text

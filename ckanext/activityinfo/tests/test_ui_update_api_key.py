import pytest
from ckan.plugins import toolkit
from ckanext.activityinfo.helpers import get_activity_info_api_key


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
        ak = get_activity_info_api_key(ai_user_with_api_key["name"])
        assert ak == new_api_key

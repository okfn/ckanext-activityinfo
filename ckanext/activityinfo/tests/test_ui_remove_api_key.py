import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories
from ckanext.activityinfo.helpers import get_activity_info_api_key


@pytest.mark.usefixtures("clean_db")
class TestRemoveApiKey:
    def test_remove_api_key_success(self, app, ai_user_with_api_key):
        user_name = ai_user_with_api_key["name"]
        environ = {"Authorization": ai_user_with_api_key["token"]}
        url = toolkit.url_for("activity_info.remove_api_key")
        resp = app.post(url, headers=environ)
        f = open('p0.html', 'w')
        f.write(resp.body)
        f.close()
        assert resp.status_code == 200
        assert "ActivityInfo API key removed successfully" in resp.body

        # Confirm key is no longer in the user plugin extras
        ak = get_activity_info_api_key(user_name)
        assert ak is None

    def test_remove_api_key_no_key(self, app):
        user_no_api_key = ckan_factories.UserWithToken()
        environ = {"Authorization": user_no_api_key["token"]}
        url = toolkit.url_for("activity_info.remove_api_key")
        resp = app.post(url, headers=environ)
        assert resp.status_code == 200
        assert "No ActivityInfo API key found to remove." in resp.body

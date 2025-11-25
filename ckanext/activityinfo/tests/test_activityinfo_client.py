import pytest
import requests
from ckanext.activityinfo.data.base import ActivityInfoClient


# --- Simple requests mocker ---
class SimpleRequestsMock:
    def __init__(self):
        self._registry = {}

    def get(self, url, json=None):
        self._registry[url] = json

    def __call__(self, method, url, **kwargs):
        if method.lower() == "get" and url in self._registry:
            class Resp:
                def __init__(self, data):
                    self._data = data
                    self.status_code = 200
                    self.text = ""
                def raise_for_status(self): pass  # noqa E306
                def json(self): return self._data  # noqa E306
            return Resp(self._registry[url])
        raise RuntimeError(f"Unmocked {method} {url}")


@pytest.fixture
def requests_mock_fixture(monkeypatch):
    mocker = SimpleRequestsMock()

    def fake_get(url, headers=None, params=None, **kwargs):
        # Only mock requests to the ActivityInfo domain, pass through others
        if url.startswith("https://www.activityinfo.org/"):
            return mocker("get", url)
        # For other domains, call the real requests.get
        return requests.sessions.Session().get(url, headers=headers, params=params, **kwargs)
    monkeypatch.setattr(requests, "get", fake_get)
    return mocker


@pytest.fixture
def client():
    return ActivityInfoClient(api_key="test-api-key", debug=False)


def test_get_user_auth_headers(client):
    headers = client.get_user_auth_headers()
    assert headers["Authorization"] == "Bearer test-api-key"


def test_get_databases(requests_mock_fixture, client):
    url = "https://www.activityinfo.org/resources/databases"
    fake_response = [
        {"databaseId": "db1", "label": "DB 1"},
        {"databaseId": "db2", "label": "DB 2"},
    ]
    requests_mock_fixture.get(url, json=fake_response)
    result = client.get_databases()
    assert isinstance(result, list)
    assert result[0]["databaseId"] == "db1"


def test_get_database(requests_mock_fixture, client):
    db_id = "db1"
    url = f"https://www.activityinfo.org/resources/databases/{db_id}"
    fake_response = {"databaseId": db_id, "resources": []}
    requests_mock_fixture.get(url, json=fake_response)
    result = client.get_database(db_id)
    assert result["databaseId"] == db_id


def test_get_forms(requests_mock_fixture, client):
    db_id = "db1"
    url = f"https://www.activityinfo.org/resources/databases/{db_id}"
    fake_response = {
        "databaseId": db_id,
        "resources": [
            {"id": "f1", "type": "FORM"},
            {"id": "f2", "type": "FOLDER"},
            {"id": "f3", "type": "FORM"},
        ]
    }
    requests_mock_fixture.get(url, json=fake_response)
    result = client.get_forms(db_id)
    assert "forms" in result
    assert len(result["forms"]) == 2
    assert result["forms"][0]["id"] == "f1"
    assert result["forms"][1]["id"] == "f3"


def test_get_form(requests_mock_fixture, client):
    db_id = "db1"
    form_id = "f1"
    url = f"https://www.activityinfo.org/resources/form/{form_id}/tree/translated"
    fake_response = {"id": form_id, "fields": []}
    requests_mock_fixture.get(url, json=fake_response)
    result = client.get_form(db_id, form_id)
    assert result["id"] == form_id


def test_get_user_auth_headers_no_api_key():
    client = ActivityInfoClient(api_key=None)
    with pytest.raises(ValueError):
        client.get_user_auth_headers()

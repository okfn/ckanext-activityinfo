import pytest
import requests
from ckanext.activityinfo.data.base import ActivityInfoClient


# --- Simple requests mocker ---
class SimpleRequestsMock:
    def __init__(self):
        self._get_registry = {}
        self._post_registry = {}

    def get(self, url, json=None):
        self._get_registry[url] = json

    def post(self, url, json=None):
        self._post_registry[url] = json

    def __call__(self, method, url, **kwargs):
        if method.lower() == "get" and url in self._get_registry:
            class Resp:
                def __init__(self, data):
                    self._data = data
                    self.status_code = 200
                    self.text = ""
                def raise_for_status(self): pass  # noqa E306
                def json(self): return self._data  # noqa E306
            return Resp(self._get_registry[url])
        if method.lower() == "post" and url in self._post_registry:
            class Resp:
                def __init__(self, data):
                    self._data = data
                    self.status_code = 200
                    self.text = ""
                def raise_for_status(self): pass  # noqa E306
                def json(self): return self._data  # noqa E306
            return Resp(self._post_registry[url])
        raise RuntimeError(f"Unmocked {method} {url}")


@pytest.fixture
def requests_mock_fixture(monkeypatch):
    mocker = SimpleRequestsMock()

    def fake_get(url, headers=None, params=None, **kwargs):
        if url.startswith("https://www.activityinfo.org/"):
            return mocker("get", url)
        return requests.sessions.Session().get(url, headers=headers, params=params, **kwargs)

    def fake_post(url, headers=None, json=None, **kwargs):
        if url.startswith("https://www.activityinfo.org/"):
            return mocker("post", url)
        return requests.sessions.Session().post(url, headers=headers, json=json, **kwargs)

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)
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


def test_get_form_columns(requests_mock_fixture, client):
    form_id = "f1"
    url = f"https://www.activityinfo.org/resources/form/{form_id}/tree/translated"
    fake_response = {
        "forms": {
            form_id: {
                "schema": {
                    "databaseId": "db1",
                    "elements": [
                        {"id": "field1", "label": "Field One", "type": "text"},
                        {"id": "field2", "label": "Field Two", "type": "quantity"},
                        {"id": "subform1", "label": "Sub Form", "type": "SUB_FORM"},
                        {"id": "section1", "label": "Section", "type": "section"},
                    ]
                }
            }
        }
    }
    requests_mock_fixture.get(url, json=fake_response)
    columns = client.get_form_columns(form_id)

    # Should exclude SUB_FORM and section types
    assert len(columns) == 2
    assert columns[0] == {
        "id": "field1",
        "label": "Field One",
        "formula": "field1",
        "translate": False
    }
    assert columns[1] == {
        "id": "field2",
        "label": "Field Two",
        "formula": "field2",
        "translate": False
    }


def test_get_form_columns_uses_id_as_label_fallback(requests_mock_fixture, client):
    form_id = "f1"
    url = f"https://www.activityinfo.org/resources/form/{form_id}/tree/translated"
    fake_response = {
        "forms": {
            form_id: {
                "schema": {
                    "databaseId": "db1",
                    "elements": [
                        {"id": "field1", "type": "text"},  # No label
                    ]
                }
            }
        }
    }
    requests_mock_fixture.get(url, json=fake_response)
    columns = client.get_form_columns(form_id)

    assert len(columns) == 1
    assert columns[0]["label"] == "field1"


def test_start_job_download_form_data(requests_mock_fixture, client):
    form_id = "f1"
    form_url = f"https://www.activityinfo.org/resources/form/{form_id}/tree/translated"
    jobs_url = "https://www.activityinfo.org/resources/jobs"

    # Mock form schema response
    fake_form_response = {
        "forms": {
            form_id: {
                "schema": {
                    "databaseId": "db1",
                    "elements": [
                        {"id": "field1", "label": "Field One", "type": "text"},
                    ]
                }
            }
        }
    }
    requests_mock_fixture.get(form_url, json=fake_form_response)

    # Mock job creation response
    fake_job_response = {
        "id": "job123",
        "state": "started",
        "percentComplete": 0
    }
    requests_mock_fixture.post(jobs_url, json=fake_job_response)

    result = client.start_job_download_form_data(form_id, format="CSV")

    assert result["id"] == "job123"
    assert result["state"] == "started"


def test_start_job_download_form_data_with_custom_columns(requests_mock_fixture, client):
    form_id = "f1"
    jobs_url = "https://www.activityinfo.org/resources/jobs"

    custom_columns = [
        {"id": "custom1", "label": "Custom", "formula": "custom1", "translate": False}
    ]

    fake_job_response = {
        "id": "job456",
        "state": "started",
        "percentComplete": 0
    }
    requests_mock_fixture.post(jobs_url, json=fake_job_response)

    # Should not fetch form schema when columns are provided
    result = client.start_job_download_form_data(form_id, format="CSV", columns=custom_columns)

    assert result["id"] == "job456"


def test_start_job_download_form_data_invalid_format(client):
    with pytest.raises(ValueError) as exc_info:
        client.start_job_download_form_data("f1", format="INVALID")
    assert "Invalid format" in str(exc_info.value)


def test_get_job_status(requests_mock_fixture, client):
    job_id = "job123"
    url = f"https://www.activityinfo.org/resources/jobs/{job_id}"
    fake_response = {
        "id": job_id,
        "state": "completed",
        "percentComplete": 100,
        "result": {
            "downloadUrl": "/resources/jobs/job123/download"
        }
    }
    requests_mock_fixture.get(url, json=fake_response)

    result = client.get_job_status(job_id)

    assert result["id"] == job_id
    assert result["state"] == "completed"
    assert result["result"]["downloadUrl"] == "/resources/jobs/job123/download"


def test_get_job_file_not_ready(requests_mock_fixture, client):
    job_id = "job123"
    url = f"https://www.activityinfo.org/resources/jobs/{job_id}"
    fake_response = {
        "id": job_id,
        "state": "started",
        "percentComplete": 50
    }
    requests_mock_fixture.get(url, json=fake_response)

    done, result = client.get_job_file(job_id)

    assert done is False
    assert result == 50


def test_get_job_file_completed(requests_mock_fixture, client):
    job_id = "job123"
    url = f"https://www.activityinfo.org/resources/jobs/{job_id}"
    fake_response = {
        "id": job_id,
        "state": "completed",
        "percentComplete": 100,
        "result": {
            "downloadUrl": "/resources/jobs/job123/download"
        }
    }
    requests_mock_fixture.get(url, json=fake_response)

    done, result = client.get_job_file(job_id)

    assert done is True
    assert result == "https://www.activityinfo.org/resources/jobs/job123/download"

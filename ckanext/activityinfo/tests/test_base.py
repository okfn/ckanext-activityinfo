from unittest import mock
import pytest
from ckanext.activityinfo.data.base import ActivityInfoClient


class TestActivityInfoClientFormats:
    def test_start_job_valid_csv_format(self):
        """Test that CSV format is accepted."""
        client = ActivityInfoClient(api_key="test_key", debug=False)
        fake_columns = [{"id": "col1", "label": "Column 1", "formula": "col1", "translate": False}]
        fake_response = mock.Mock()
        fake_response.json.return_value = {"id": "job123", "state": "started"}
        fake_response.raise_for_status = mock.Mock()

        with mock.patch.object(client, "get_form_columns", return_value=fake_columns):
            with mock.patch("requests.post", return_value=fake_response) as mock_post:
                result = client.start_job_download_form_data("form01", format="CSV")
                assert result["id"] == "job123"
                # Verify the payload contains the correct format
                call_kwargs = mock_post.call_args[1]
                assert call_kwargs["json"]["descriptor"]["format"] == "CSV"

    def test_start_job_valid_xlsx_format(self):
        """Test that XLSX format is accepted."""
        client = ActivityInfoClient(api_key="test_key", debug=False)
        fake_columns = [{"id": "col1", "label": "Column 1", "formula": "col1", "translate": False}]
        fake_response = mock.Mock()
        fake_response.json.return_value = {"id": "job123", "state": "started"}
        fake_response.raise_for_status = mock.Mock()

        with mock.patch.object(client, "get_form_columns", return_value=fake_columns):
            with mock.patch("requests.post", return_value=fake_response) as mock_post:
                result = client.start_job_download_form_data("form01", format="XLSX")
                assert result["id"] == "job123"
                call_kwargs = mock_post.call_args[1]
                assert call_kwargs["json"]["descriptor"]["format"] == "XLSX"

    def test_start_job_valid_text_format(self):
        """Test that TEXT format is accepted."""
        client = ActivityInfoClient(api_key="test_key", debug=False)
        fake_columns = [{"id": "col1", "label": "Column 1", "formula": "col1", "translate": False}]
        fake_response = mock.Mock()
        fake_response.json.return_value = {"id": "job123", "state": "started"}
        fake_response.raise_for_status = mock.Mock()

        with mock.patch.object(client, "get_form_columns", return_value=fake_columns):
            with mock.patch("requests.post", return_value=fake_response) as mock_post:
                result = client.start_job_download_form_data("form01", format="TEXT")
                assert result["id"] == "job123"
                call_kwargs = mock_post.call_args[1]
                assert call_kwargs["json"]["descriptor"]["format"] == "TEXT"

    def test_start_job_invalid_format_raises_error(self):
        """Test that invalid formats raise a ValueError."""
        client = ActivityInfoClient(api_key="test_key", debug=False)

        with pytest.raises(ValueError) as excinfo:
            client.start_job_download_form_data("form01", format="INVALID")

        assert "Invalid format" in str(excinfo.value)
        assert "CSV" in str(excinfo.value)
        assert "XLSX" in str(excinfo.value)
        assert "TEXT" in str(excinfo.value)

    def test_start_job_default_format_is_csv(self):
        """Test that the default format is CSV."""
        client = ActivityInfoClient(api_key="test_key", debug=False)
        fake_columns = [{"id": "col1", "label": "Column 1", "formula": "col1", "translate": False}]
        fake_response = mock.Mock()
        fake_response.json.return_value = {"id": "job123", "state": "started"}
        fake_response.raise_for_status = mock.Mock()

        with mock.patch.object(client, "get_form_columns", return_value=fake_columns):
            with mock.patch("requests.post", return_value=fake_response) as mock_post:
                client.start_job_download_form_data("form01")
                call_kwargs = mock_post.call_args[1]
                assert call_kwargs["json"]["descriptor"]["format"] == "CSV"

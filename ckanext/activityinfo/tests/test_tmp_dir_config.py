from unittest import mock
from types import SimpleNamespace
import pytest

from ckantoolkit.tests import factories as ckan_factories

from ckanext.activityinfo.tests import factories
from ckanext.activityinfo.jobs.download import _update_resource_with_file


@pytest.fixture
def setup_data():
    """Test setup data."""
    obj = SimpleNamespace()
    obj.user = factories.ActivityInfoUser()
    obj.resource = ckan_factories.Resource()
    return obj


@pytest.fixture
def mock_file_data():
    """Mock file data for testing."""
    return b"test,data\n1,2\n3,4"


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies for _update_resource_with_file."""
    mock_temp = mock.MagicMock()
    mock_temp.name = '/tmp/test_file.csv'

    with mock.patch('tempfile.NamedTemporaryFile', return_value=mock_temp) as mock_tempfile, \
         mock.patch('builtins.open', mock.mock_open()), \
         mock.patch('ckan.plugins.toolkit.get_action', return_value=mock.MagicMock()) as mock_action:
        yield {'tempfile': mock_tempfile, 'get_action': mock_action}


@pytest.mark.usefixtures("clean_db")
class TestTmpDirConfig:
    """Tests for ckanext.activityinfo.tmp_dir configuration setting."""

    @pytest.mark.ckan_config('ckanext.activityinfo.tmp_dir', 'sys_tmp')
    def test_default_tmp_dir_uses_system_temp(
        self, setup_data, mock_file_data, mock_dependencies
    ):
        """Test that default configuration uses system temp directory."""
        context = {'user': setup_data.user['name'], 'ignore_auth': True}

        _update_resource_with_file(
            context, setup_data.resource['id'], mock_file_data, 'test_file.csv', 'csv'
        )

        mock_dependencies['tempfile'].assert_called_once_with(
            delete=False, suffix='.csv'
        )

    @pytest.mark.ckan_config('ckanext.activityinfo.tmp_dir', '/custom/tmp/path')
    def test_custom_tmp_dir_uses_specified_directory(
        self, setup_data, mock_file_data, mock_dependencies
    ):
        """Test that custom tmp_dir configuration uses specified directory."""
        context = {'user': setup_data.user['name'], 'ignore_auth': True}

        _update_resource_with_file(
            context, setup_data.resource['id'], mock_file_data, 'test_file.csv', 'csv'
        )

        mock_dependencies['tempfile'].assert_called_once_with(
            delete=False, suffix='.csv', dir='/custom/tmp/path'
        )

    @pytest.mark.ckan_config('ckanext.activityinfo.tmp_dir', None)
    def test_none_value_falls_back_to_default(
        self, setup_data, mock_file_data, mock_dependencies
    ):
        """Test that None value for tmp_dir falls back to default behavior."""
        context = {'user': setup_data.user['name'], 'ignore_auth': True}

        _update_resource_with_file(
            context, setup_data.resource['id'], mock_file_data, 'test_file.csv', 'csv'
        )

        mock_dependencies['tempfile'].assert_called_once_with(
            delete=False, suffix='.csv'
        )

    @pytest.mark.ckan_config('ckanext.activityinfo.tmp_dir', '/custom/xlsx/path')
    def test_xlsx_format_with_custom_tmp_dir(
        self, setup_data, mock_file_data, mock_dependencies
    ):
        """Test that xlsx format works correctly with custom tmp directory."""
        context = {'user': setup_data.user['name'], 'ignore_auth': True}

        _update_resource_with_file(
            context, setup_data.resource['id'], mock_file_data, 'test_file.xlsx', 'xlsx'
        )

        mock_dependencies['tempfile'].assert_called_once_with(
            delete=False, suffix='.xlsx', dir='/custom/xlsx/path'
        )

        call_args = mock_dependencies['get_action'].return_value.call_args[0][1]
        assert call_args['id'] == setup_data.resource['id']
        assert call_args['activityinfo_status'] == 'complete'

    @pytest.mark.ckan_config('ckanext.activityinfo.tmp_dir', '')
    def test_empty_string_tmp_dir_uses_custom_behavior(
        self, setup_data, mock_file_data, mock_dependencies
    ):
        """Test that empty string for tmp_dir is treated as custom directory."""
        context = {'user': setup_data.user['name'], 'ignore_auth': True}

        _update_resource_with_file(
            context, setup_data.resource['id'], mock_file_data, 'test_file.csv', 'csv'
        )

        mock_dependencies['tempfile'].assert_called_once_with(
            delete=False, suffix='.csv', dir=''
        )

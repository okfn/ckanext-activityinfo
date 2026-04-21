"""Tests for CLI resource commands (update-activity-info-resource, sync-auto-updates)."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories

from ckanext.activityinfo.cli.resources import (
    update_activityinfo_resource,
    sync_auto_updates,
)
from ckanext.activityinfo.tests import factories


@pytest.fixture
def setup_data():
    obj = SimpleNamespace()
    obj.activityinfo_user = factories.ActivityInfoUser()
    obj.regular_user = ckan_factories.UserWithToken()
    return obj


# ---- update-activity-info-resource ----

@pytest.mark.usefixtures("clean_db")
class TestUpdateActivityInfoResourceCLI:
    """Tests for the update-activity-info-resource CLI command."""

    @patch('ckanext.activityinfo.cli.resources.download_activityinfo_resource')
    def test_success(self, mock_download, setup_data):
        """Successful update should show success message."""
        resource = factories.ActivityInfoResource()
        user_name = setup_data.activityinfo_user['name']

        runner = CliRunner()
        result = runner.invoke(update_activityinfo_resource, [
            '-r', resource['id'], '-u', user_name
        ])

        assert result.exit_code == 0
        assert 'Updating ActivityInfo resource' in result.output
        assert 'updated successfully' in result.output
        mock_download.assert_called_once_with(
            resource_id=resource['id'], user=user_name
        )

    @patch('ckanext.activityinfo.cli.resources.download_activityinfo_resource')
    def test_download_failure_propagates(self, mock_download, setup_data):
        """If download raises, the exception should propagate."""
        mock_download.side_effect = ValueError("No API key configured")
        resource = factories.ActivityInfoResource()
        user_name = setup_data.activityinfo_user['name']

        runner = CliRunner()
        result = runner.invoke(update_activityinfo_resource, [
            '-r', resource['id'], '-u', user_name
        ])

        assert result.exit_code != 0
        assert 'No API key configured' in result.output

    def test_missing_resource_id(self, setup_data):
        """Missing --resource-id should fail."""
        runner = CliRunner()
        result = runner.invoke(update_activityinfo_resource, [
            '-u', 'someuser'
        ])
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'required' in result.output.lower()

    def test_missing_user_name(self, setup_data):
        """Missing --user-name should fail."""
        runner = CliRunner()
        result = runner.invoke(update_activityinfo_resource, [
            '-r', 'some-id'
        ])
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'required' in result.output.lower()

    @patch('ckanext.activityinfo.cli.resources.download_activityinfo_resource')
    def test_verbose_flag(self, mock_download, setup_data):
        """Verbose flag should not break the command."""
        resource = factories.ActivityInfoResource()
        user_name = setup_data.activityinfo_user['name']

        runner = CliRunner()
        result = runner.invoke(update_activityinfo_resource, [
            '-r', resource['id'], '-u', user_name, '-v'
        ])

        assert result.exit_code == 0
        assert 'updated successfully' in result.output


# ---- sync-auto-updates ----

@pytest.mark.usefixtures("clean_db")
class TestSyncAutoUpdatesCLI:
    """Tests for the sync-auto-updates CLI command."""

    def test_no_due_resources(self, setup_data):
        """When no resources are due, show appropriate message and exit 0."""
        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, [])
        assert result.exit_code == 0
        assert 'No resources due for update' in result.output

    def test_never_resources_not_picked_up(self, setup_data):
        """Resources with auto_update='never' should not be picked up."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='never',
            activityinfo_user=setup_data.activityinfo_user['name'],
        )
        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, [])
        assert result.exit_code == 0
        assert 'No resources due for update' in result.output

    def test_dry_run_shows_resources_without_updating(self, setup_data):
        """Dry run should list due resources but not enqueue jobs."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )

        fake_update = mock.MagicMock()
        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            result = runner.invoke(sync_auto_updates, ['--dry-run'])

        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
        assert resource['id'] in result.output
        assert user_name in result.output
        fake_update.assert_not_called()

    def test_skips_resource_without_activityinfo_user(self, setup_data):
        """Resources without activityinfo_user should be skipped."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user='',
        )

        fake_update = mock.MagicMock()
        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            result = runner.invoke(sync_auto_updates, [])

        assert '1 skipped' in result.output
        assert 'no activityinfo_user set' in result.output
        fake_update.assert_not_called()

    def test_enqueues_job_for_due_resource(self, setup_data):
        """Due resources should be enqueued via act_info_update_resource_file."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )

        action_calls = []

        def fake_update(ctx, dd):
            action_calls.append({
                'user': ctx.get('user'),
                'resource_id': dd.get('resource_id'),
            })
            return {'job_id': 'test-job-123', 'resource_id': dd['resource_id']}

        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            result = runner.invoke(sync_auto_updates, [])

        assert result.exit_code == 0
        assert '1 enqueued' in result.output
        assert 'test-job-123' in result.output

        assert len(action_calls) == 1
        assert action_calls[0]['user'] == user_name
        assert action_calls[0]['resource_id'] == resource['id']

    def test_increments_counter_after_enqueue(self, setup_data):
        """Counter and timestamp should be updated after successful enqueue."""
        user_name = setup_data.activityinfo_user['name']
        before = datetime.now(timezone.utc)
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=2,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )

        def fake_update(ctx, dd):
            return {'job_id': 'j', 'resource_id': dd['resource_id']}

        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            runner.invoke(sync_auto_updates, [])

        updated = toolkit.get_action('resource_show')(
            {'ignore_auth': True}, {'id': resource['id']}
        )
        assert int(updated['activityinfo_auto_update_count']) == 3
        last_updated = datetime.fromisoformat(updated['activityinfo_last_updated'])
        assert last_updated >= before

    def test_counter_unchanged_on_enqueue_failure(self, setup_data):
        """If enqueuing fails, counter should not be incremented."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=2,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )

        def fake_update(ctx, dd):
            raise Exception("Connection refused")

        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            result = runner.invoke(sync_auto_updates, [])

        assert '1 failed' in result.output
        assert 'Connection refused' in result.output

        updated = toolkit.get_action('resource_show')(
            {'ignore_auth': True}, {'id': resource['id']}
        )
        assert int(updated['activityinfo_auto_update_count']) == 2

    def test_per_resource_user_isolation(self, setup_data):
        """Each resource should be updated using its own activityinfo_user."""
        user_a = setup_data.activityinfo_user['name']
        user_b = factories.ActivityInfoUser()['name']

        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_a,
        )
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_b,
        )

        users_called = []

        def fake_update(ctx, dd):
            users_called.append(ctx.get('user'))
            return {'job_id': 'j', 'resource_id': dd['resource_id']}

        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            result = runner.invoke(sync_auto_updates, [])

        assert '2 enqueued' in result.output
        assert set(users_called) == {user_a, user_b}

    def test_mixed_success_and_failure(self, setup_data):
        """Summary should correctly count mixed results."""
        user_name = setup_data.activityinfo_user['name']

        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )
        # No user -> skipped
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user='',
        )

        call_count = [0]

        def fake_update(ctx, dd):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Boom")
            return {'job_id': 'j', 'resource_id': dd['resource_id']}

        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            result = runner.invoke(sync_auto_updates, [])

        assert '1 enqueued' in result.output
        assert '1 failed' in result.output
        assert '1 skipped' in result.output

    def test_recently_created_resource_not_due(self, setup_data):
        """A resource created just now (with last_updated set) should not be due."""
        user_name = setup_data.activityinfo_user['name']
        now = datetime.now(timezone.utc).isoformat()
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated=now,
            activityinfo_user=user_name,
        )

        fake_update = mock.MagicMock()
        with mock.patch.dict(
            'ckan.logic._actions',
            {'act_info_update_resource_file': fake_update},
        ):
            runner = CliRunner()
            result = runner.invoke(sync_auto_updates, [])

        assert result.exit_code == 0
        assert 'No resources due for update' in result.output
        fake_update.assert_not_called()

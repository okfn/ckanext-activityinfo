"""Tests for auto-update sync logic (utils + CLI command)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories

from ckanext.activityinfo.cli.resources import sync_auto_updates
from ckanext.activityinfo.tests import factories
from ckanext.activityinfo.utils import get_resources_due_for_auto_update

# Captured BEFORE any @patch of toolkit.get_action so tests can call the real
# action dispatcher without re-entering the mock (which causes recursion).
_REAL_GET_ACTION = toolkit.get_action


@pytest.fixture
def setup_data():
    obj = SimpleNamespace()
    obj.activityinfo_user = factories.ActivityInfoUser()
    obj.regular_user = ckan_factories.UserWithToken()
    return obj


@pytest.mark.usefixtures("clean_db")
class TestGetResourcesDueForAutoUpdate:
    """Tests for the get_resources_due_for_auto_update utility function."""

    def test_no_resources(self, setup_data):
        """No resources exist, should return empty list."""
        result = get_resources_due_for_auto_update()
        assert result == []

    def test_resource_with_never_not_due(self, setup_data):
        """Resources with auto_update='never' should not be due."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='never',
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 0

    def test_daily_resource_never_updated_is_due(self, setup_data):
        """A daily resource that was never updated should be due."""
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 1
        assert result[0]['id'] == resource['id']

    def test_weekly_resource_never_updated_is_due(self, setup_data):
        """A weekly resource that was never updated should be due."""
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='weekly',
            activityinfo_auto_update_runs=3,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 1
        assert result[0]['id'] == resource['id']

    def test_daily_resource_updated_recently_not_due(self, setup_data):
        """A daily resource updated less than 24h ago should not be due."""
        recent = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=1,
            activityinfo_last_updated=recent,
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 0

    def test_daily_resource_updated_long_ago_is_due(self, setup_data):
        """A daily resource updated more than 24h ago should be due."""
        old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=1,
            activityinfo_last_updated=old,
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 1
        assert result[0]['id'] == resource['id']

    def test_weekly_resource_updated_3_days_ago_not_due(self, setup_data):
        """A weekly resource updated 3 days ago should not be due."""
        recent = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        factories.ActivityInfoResource(
            activityinfo_auto_update='weekly',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=1,
            activityinfo_last_updated=recent,
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 0

    def test_weekly_resource_updated_8_days_ago_is_due(self, setup_data):
        """A weekly resource updated 8 days ago should be due."""
        old = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='weekly',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=1,
            activityinfo_last_updated=old,
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 1
        assert result[0]['id'] == resource['id']

    def test_run_limit_reached_not_due(self, setup_data):
        """A resource that reached its run limit should not be due."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=3,
            activityinfo_auto_update_count=3,
            activityinfo_last_updated='',
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 0

    def test_run_limit_exceeded_not_due(self, setup_data):
        """A resource that exceeded its run limit should not be due."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=2,
            activityinfo_auto_update_count=5,
            activityinfo_last_updated='',
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 0

    def test_pending_resource_not_due(self, setup_data):
        """A resource with status 'pending' should not be picked up."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_status='pending',
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 0

    def test_error_resource_not_due(self, setup_data):
        """A resource with status 'error' should not be picked up."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_status='error',
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 0

    def test_multiple_resources_mixed(self, setup_data):
        """Only due resources should be returned from a mixed set."""
        # Due: daily, never updated
        res_due = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
        )
        # Not due: never
        factories.ActivityInfoResource(
            activityinfo_auto_update='never',
        )
        # Not due: run limit reached
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=1,
            activityinfo_auto_update_count=1,
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 1
        assert result[0]['id'] == res_due['id']

    def test_due_resource_includes_activityinfo_user(self, setup_data):
        """Due resource dict should include activityinfo_user field."""
        user_name = setup_data.activityinfo_user['name']
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )
        result = get_resources_due_for_auto_update()
        assert len(result) == 1
        assert result[0]['activityinfo_user'] == user_name


@pytest.mark.usefixtures("clean_db")
class TestSyncAutoUpdatesCounterAndTimestamp:
    """Test that the sync command updates counter and timestamp correctly."""

    @patch('ckanext.activityinfo.cli.resources.toolkit.get_action')
    def test_counter_incremented_after_enqueue(self, mock_get_action, setup_data):
        """After enqueuing a job, counter should be incremented."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )

        # Mock only act_info_update_resource_file, let others pass through
        original_get_action = _REAL_GET_ACTION

        def selective_mock(action_name):
            if action_name == 'act_info_update_resource_file':
                return lambda ctx, dd: {'job_id': 'test-job', 'resource_id': dd['resource_id']}
            return original_get_action(action_name)

        mock_get_action.side_effect = selective_mock

        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, [])
        assert result.exit_code == 0

        updated = original_get_action('resource_show')(
            {'ignore_auth': True}, {'id': resource['id']}
        )
        assert int(updated['activityinfo_auto_update_count']) == 1
        assert updated['activityinfo_last_updated'] != ''

    @patch('ckanext.activityinfo.cli.resources.toolkit.get_action')
    def test_counter_not_incremented_on_failure(self, mock_get_action, setup_data):
        """If enqueuing fails, counter should not change."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=2,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )

        original_get_action = _REAL_GET_ACTION

        def selective_mock(action_name):
            if action_name == 'act_info_update_resource_file':
                raise Exception("Enqueue failed")
            return original_get_action(action_name)

        mock_get_action.side_effect = selective_mock

        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, [])
        assert '1 failed' in result.output

        updated = original_get_action('resource_show')(
            {'ignore_auth': True}, {'id': resource['id']}
        )
        assert int(updated['activityinfo_auto_update_count']) == 2

    @patch('ckanext.activityinfo.cli.resources.toolkit.get_action')
    def test_dry_run_does_not_update(self, mock_get_action, setup_data):
        """Dry run should not enqueue jobs or update anything."""
        user_name = setup_data.activityinfo_user['name']
        resource = factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user=user_name,
        )

        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, ['--dry-run'])
        assert result.exit_code == 0
        assert 'DRY RUN' in result.output

        # get_action should not have been called at all during dry run
        mock_get_action.assert_not_called()

        updated = _REAL_GET_ACTION('resource_show')(
            {'ignore_auth': True}, {'id': resource['id']}
        )
        assert int(updated['activityinfo_auto_update_count']) == 0

    @patch('ckanext.activityinfo.cli.resources.toolkit.get_action')
    def test_resource_without_user_is_skipped(self, mock_get_action, setup_data):
        """Resources with no activityinfo_user should be skipped."""
        factories.ActivityInfoResource(
            activityinfo_auto_update='daily',
            activityinfo_auto_update_runs=5,
            activityinfo_auto_update_count=0,
            activityinfo_last_updated='',
            activityinfo_user='',
        )

        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, [])
        assert '1 skipped' in result.output
        mock_get_action.assert_not_called()


@pytest.mark.usefixtures("clean_db")
class TestSyncAutoUpdatesCLIOutput:
    """Test CLI output messages."""

    def test_no_resources_message(self, setup_data):
        """When no resources are due, show appropriate message."""
        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, [])
        assert result.exit_code == 0
        assert 'No resources due for update' in result.output

    @patch('ckanext.activityinfo.cli.resources.toolkit.get_action')
    def test_summary_shows_counts(self, mock_get_action, setup_data):
        """Summary should show enqueued and failed counts."""
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

        original_get_action = _REAL_GET_ACTION

        def selective_mock(action_name):
            if action_name == 'act_info_update_resource_file':
                return lambda ctx, dd: {'job_id': 'test-job', 'resource_id': dd['resource_id']}
            return original_get_action(action_name)

        mock_get_action.side_effect = selective_mock

        runner = CliRunner()
        result = runner.invoke(sync_auto_updates, [])
        assert '2 enqueued' in result.output
        assert '0 failed' in result.output

    @patch('ckanext.activityinfo.cli.resources.toolkit.get_action')
    def test_uses_per_resource_user(self, mock_get_action, setup_data):
        """Each resource should use its own activityinfo_user."""
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

        calls = []
        original_get_action = _REAL_GET_ACTION

        def selective_mock(action_name):
            if action_name == 'act_info_update_resource_file':
                def fake_action(ctx, dd):
                    calls.append(ctx.get('user'))
                    return {'job_id': 'test-job', 'resource_id': dd['resource_id']}
                return fake_action
            return original_get_action(action_name)

        mock_get_action.side_effect = selective_mock

        runner = CliRunner()
        runner.invoke(sync_auto_updates, [])

        assert len(calls) == 2
        assert set(calls) == {user_a, user_b}

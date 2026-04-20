import logging
from datetime import datetime, timezone

import click
from ckan.plugins import toolkit
from ckanext.activityinfo.jobs.download import download_activityinfo_resource
from ckanext.activityinfo.utils import get_resources_due_for_auto_update


def _setup_download_logging(verbose=False):
    """Set up a logging handler that forwards download logs to click.echo.

    Returns (handler, logger) so the caller can remove the handler when done.
    """
    download_logger = logging.getLogger('ckanext.activityinfo.jobs.download')
    handler = logging.Handler()
    handler.emit = lambda record: click.echo(f"  {handler.format(record)}")
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    download_logger.addHandler(handler)
    download_logger.setLevel(handler.level)
    return handler, download_logger


@click.command(
    'update-activity-info-resource',
    short_help='Update a single ActivityInfo resource'
)
@click.option('-r', '--resource-id', required=True)
@click.option('-u', '--user-name', required=True, help='CKAN user with permissions (API key) to ActivityInfo')
@click.option('-v', '--verbose', count=True)
def update_activityinfo_resource(resource_id, user_name, verbose):
    """ Update a single ActivityInfo resource. """

    handler, download_logger = _setup_download_logging(verbose)

    click.echo('Updating ActivityInfo resource')
    try:
        download_activityinfo_resource(resource_id=resource_id, user=user_name)
        click.echo('ActivityInfo resource updated successfully')
    except Exception as e:
        raise click.ClickException(str(e))
    finally:
        download_logger.removeHandler(handler)


@click.command(
    'sync-auto-updates',
    short_help='Sync all ActivityInfo resources due for automatic update'
)
@click.option('-v', '--verbose', count=True)
@click.option(
    '--dry-run', is_flag=True, default=False,
    help='Show what would be updated without actually running updates'
)
def sync_auto_updates(verbose, dry_run):
    """Find and update all ActivityInfo resources due for automatic update.

    This command is meant to be run from cron. It checks all resources with
    activityinfo_auto_update set to 'daily' or 'weekly', verifies timing
    and run limits, and triggers downloads for those that are due.

    Each resource is updated using the CKAN user who originally created it
    (stored in the activityinfo_user field).
    """
    click.echo("Checking for ActivityInfo resources due for auto-update...")

    due_resources = get_resources_due_for_auto_update()

    if not due_resources:
        click.echo("No resources due for update.")
        return

    click.echo(f"Found {len(due_resources)} resource(s) due for update.")

    if dry_run:
        for res in due_resources:
            count = res.get('activityinfo_auto_update_count', 0)
            max_runs = res.get('activityinfo_auto_update_runs', 1)
            user = res.get('activityinfo_user', '?')
            click.echo(
                f"  [DRY RUN] {res['id']} - "
                f"{res.get('activityinfo_form_label', '?')} "
                f"({res.get('activityinfo_auto_update')}, "
                f"run {count}/{max_runs}, user: {user})"
            )
        return

    enqueued = 0
    failed = 0
    skipped = 0

    for res in due_resources:
        resource_id = res['id']
        form_label = res.get('activityinfo_form_label', resource_id)
        current_count = int(res.get('activityinfo_auto_update_count', 0) or 0)
        max_runs = int(res.get('activityinfo_auto_update_runs', 1) or 1)
        user_name = res.get('activityinfo_user')

        if not user_name:
            click.echo(
                f"\nSkipping: {form_label} ({resource_id}) "
                f"- no activityinfo_user set"
            )
            skipped += 1
            continue

        click.echo(
            f"\nUpdating: {form_label} ({resource_id}) "
            f"- run {current_count + 1}/{max_runs}, user: {user_name}"
        )

        try:
            result = toolkit.get_action('act_info_update_resource_file')(
                {'user': user_name, 'ignore_auth': True},
                {'resource_id': resource_id}
            )

            # Update the counter and timestamp now that the job is enqueued
            # No matter if the job succeeds or fails, we count this as a run to avoid infinite retries on failures
            # Errors will be registered with the activityinfo_error resource extra field
            now_iso = datetime.now(timezone.utc).isoformat()
            toolkit.get_action('resource_patch')(
                {'user': user_name, 'ignore_auth': True},
                {
                    'id': resource_id,
                    'activityinfo_last_updated': now_iso,
                    'activityinfo_auto_update_count': current_count + 1,
                }
            )

            job_id = result.get('job_id', '?')
            click.echo(
                f"  OK - job {job_id} enqueued "
                f"(run {current_count + 1}/{max_runs})"
            )
            enqueued += 1

        except Exception as e:
            click.echo(f"  FAILED - {e}", err=True)
            failed += 1
            continue

    click.echo(f"\nSync complete: {enqueued} enqueued, {failed} failed, {skipped} skipped.")

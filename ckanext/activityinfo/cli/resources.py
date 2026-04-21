import click
from ckanext.activityinfo.jobs.download import download_activityinfo_resource
from ckanext.activityinfo.cli.logs import setup_cli_logging
from ckanext.activityinfo.utils import run_sync_auto_updates


@click.command(
    'update-activity-info-resource',
    short_help='Update a single ActivityInfo resource'
)
@click.option('-r', '--resource-id', required=True)
@click.option('-u', '--user-name', required=True, help='CKAN user with permissions (API key) to ActivityInfo')
@click.option('-v', '--verbose', count=True)
def update_activityinfo_resource(resource_id, user_name, verbose):
    """ Update a single ActivityInfo resource. """

    handler, logger = setup_cli_logging(verbose)

    click.echo('Updating ActivityInfo resource')
    try:
        download_activityinfo_resource(resource_id=resource_id, user=user_name)
        click.echo('ActivityInfo resource updated successfully')
    except Exception as e:
        raise click.ClickException(str(e))

    logger.removeHandler(handler)


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
    handler, logger = setup_cli_logging(verbose)
    summary = run_sync_auto_updates(dry_run=dry_run)
    click.echo(
        f"\nSync complete: {summary['enqueued']} enqueued, "
        f"{summary['failed']} failed, {summary['skipped']} skipped."
    )
    logger.removeHandler(handler)

import logging
import click
from ckanext.activityinfo.jobs.download import download_activityinfo_resource


@click.command(
    'update-activity-info-resource',
    short_help='Update a single ActivityInfo resource'
)
@click.option('-r', '--resource-id', required=True)
@click.option('-u', '--user-name', required=True, help='CKAN user with permissions (API key) to ActivityInfo')
@click.option('-v', '--verbose', count=True)
def update_activityinfo_resource(resource_id, user_name, verbose):
    """ Update a single ActivityInfo resource. """

    # Temporarily attach a handler that forwards log messages to click.echo
    download_logger = logging.getLogger('ckanext.activityinfo.jobs.download')
    handler = logging.Handler()
    handler.emit = lambda record: click.echo(handler.format(record))
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    download_logger.addHandler(handler)
    download_logger.setLevel(handler.level)

    click.echo('Updating ActivityInfo resource')
    try:
        download_activityinfo_resource(resource_id=resource_id, user=user_name)
        click.echo('ActivityInfo resource updated successfully')
    finally:
        download_logger.removeHandler(handler)

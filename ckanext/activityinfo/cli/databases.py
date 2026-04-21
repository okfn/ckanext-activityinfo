import logging
import click
from requests.exceptions import HTTPError
from ckanext.activityinfo.cli.logs import setup_cli_logging
from ckanext.activityinfo.data.base import ActivityInfoClient
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError


log = logging.getLogger(__name__)


@click.command(
    'list',
    short_help='Get all ActivityInfo databases for a user'
)
@click.option('-t', '--activityinfo-token', required=True)
@click.option('-v', '--verbose', count=True)
def get_activityinfo_databases_list(activityinfo_token, verbose):
    """ Get a list with all ActivityInfo databases for a user. """

    handler, logger = setup_cli_logging(verbose)

    click.secho('Getting ActivityInfo databases')
    aic = ActivityInfoClient(api_key=activityinfo_token)
    try:
        databases = aic.get_databases()
    except HTTPError as e:
        # We can expect a HTTPError 401 Client Error: Unauthorized for url: https://www.activityinfo.org/resources/databases
        # for users with an invalid API key
        error = f"Error retrieving databases: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    total = 0
    for database in databases:
        database_id = database['databaseId']
        database_label = database['label']
        click.secho(f"database {database_id}: {database_label}")
        total += 1
        if verbose:
            click.secho(f"  Description: {database.get('description', 'N/A')}")
            click.secho(f"  ownerId: {database.get('ownerId', 'N/A')}")

    click.secho(f'Total ActivityInfo databases: {total}')
    logger.removeHandler(handler)

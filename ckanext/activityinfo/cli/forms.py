import logging
import click
from requests.exceptions import HTTPError
from ckanext.activityinfo.data.base import ActivityInfoClient
from ckanext.activityinfo.exceptions import ActivityInfoConnectionError


log = logging.getLogger(__name__)


@click.command(
    'list',
    short_help='Get all ActivityInfo forms'
)
@click.option('-t', '--activityinfo-token', required=True)
@click.option('-d', '--database-id', required=True)
@click.option('-s', '--include-sub-forms', is_flag=True, default=False)
@click.option('-v', '--verbose', count=True)
def get_activityinfo_forms_list(activityinfo_token, database_id, include_sub_forms, verbose):
    """ Get a list with all forms and sub-forms in ActivityInfo. """

    click.secho('Getting ActivityInfo forms')
    aic = ActivityInfoClient(api_key=activityinfo_token)
    try:
        forms = aic.get_forms(database_id, include_db_data=True)
    except HTTPError as e:
        error = f"Error retrieving forms for database {database_id} and user: {e}"
        log.error(error)
        raise ActivityInfoConnectionError(error)

    for form in forms['forms']:
        form_id = form['id']
        form_label = form['label']
        click.secho(f"form {form_id}: {form_label}")
        if verbose:
            click.secho(f"  Type: {form.get('type', 'N/A')}")
            click.secho(f"  Description: {form.get('description', 'N/A')}")
            click.secho(f"  ownerId: {form.get('ownerId', 'N/A')}")

    if include_sub_forms:
        for sub_form in forms.get('sub_forms', []):
            sub_form_id = sub_form['id']
            sub_form_label = sub_form['label']
            click.secho(f"sub-form {sub_form_id}: {sub_form_label}")
            if verbose:
                click.secho(f"  Type: {sub_form.get('type', 'N/A')}")
                click.secho(f"  Description: {sub_form.get('description', 'N/A')}")
                click.secho(f"  ownerId: {sub_form.get('ownerId', 'N/A')}")

    total_forms = len(forms['forms'])
    total_sub_forms = len(forms.get('sub_forms', []))

    click.secho(f'Total ActivityInfo forms: {total_forms}, sub-forms: {total_sub_forms}')

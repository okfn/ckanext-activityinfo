import click
from ckanext.activityinfo.cli import (
    databases as cli_databases,
    forms as cli_forms,
    resources as cli_resources,
)


@click.group(short_help='ActivityInfo plugin management commands')
def activityinfo():
    pass


@activityinfo.group(short_help='ActivityInfo databases')
def databases():
    pass


@activityinfo.group(short_help='ActivityInfo forms')
def forms():
    pass


@activityinfo.group(short_help='ActivityInfo resources')
def resources():
    pass


# ckan activityinfo databases list -t xxxxxx
databases.add_command(cli_databases.get_activityinfo_databases_list)

# ckan activityinfo forms list -t xxxxx -d yyyyy [-s]
forms.add_command(cli_forms.get_activityinfo_forms_list)

# ckan activityinfo resources update-activity-info-resource -r xxxxx -u username
# The user should have permissions to access the ActivityInfo API (API key) and the resource to update
resources.add_command(cli_resources.update_activityinfo_resource)

# ckan activityinfo resources sync-auto-updates [--dry-run] [-v]
# Find and update all resources due for automatic update (meant for cron)
resources.add_command(cli_resources.sync_auto_updates)

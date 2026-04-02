import click
from ckanext.activityinfo.cli import (
    databases as cli_databases,
    forms as cli_forms,
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


# ckan activityinfo databases list -t xxxxxx
databases.add_command(cli_databases.get_activityinfo_databases_list)

# ckan activityinfo forms list -t xxxxx -d yyyyy [-s]
forms.add_command(cli_forms.get_activityinfo_forms_list)

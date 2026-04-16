[![Tests CKAN 2.10](https://github.com/okfn/ckanext-activityinfo/workflows/CKAN%202.10%20Tests/badge.svg)](https://github.com/okfn/ckanext-activityinfo/actions)
[![Tests CKAN 2.11](https://github.com/okfn/ckanext-activityinfo/workflows/CKAN%202.11%20Tests/badge.svg)](https://github.com/okfn/ckanext-activityinfo/actions)

# ActivityInfo

[ActivityInfo](https://www.activityinfo.org) is a Information management software for the social sector.  

 - Documentation: https://www.activityinfo.org/support/docs/index.html
 - API Reference: https://www.activityinfo.org/support/docs/api/index.html
 - Source code (old version): https://github.com/bedatadriven/activityinfo

# CKAN ActivityInfo extension

A CKAN extension to connecto to your ActivityInfo account with your CKAN instance.  

## Compatibility with core CKAN versions

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | not tested    |
| 2.10            | yes           |
| 2.11            | yes           |

## Requirements

You'll need an ActivityInfo account to use this extension.  

## Installation

```bash
pip install git+https://github.com/okfn/ckanext-activityinfo@0.1.0#egg=ckanext-activityinfo
```

Also, add `activityinfo` to the `ckan.plugins` setting in your CKAN config file.  

## Automatic updates

ActivityInfo resources can be configured to update automatically (daily or weekly) with a limited number of runs (1 to 20).
These settings are available in the resource creation and edit forms.

To enable automatic updates, you need to set up a cron job (or equivalent scheduler) that runs the `sync-auto-updates` CLI command periodically.
The command checks all resources that are due for an update, enqueues background download jobs using each resource's original creator API key, and exits.

### Cron

As example.
Run the sync command at a frequency that matches your shortest update interval. If you have daily resources, run it at least once a day:

```bash
# Run every 6 hours (covers both daily and weekly resources)
0 */6 * * * /usr/bin/ckan -c /etc/ckan/production.ini activityinfo resources sync-auto-updates >> /var/log/ckan/activityinfo-sync.log 2>&1
```

### Yacron

```yaml
jobs:
  - name: activityinfo-sync
    command: ckan -c /etc/ckan/production.ini activityinfo resources sync-auto-updates
    schedule: "0 */6 * * *"
```

### Options

```bash
# Preview what would be updated without actually running
ckan activityinfo resources sync-auto-updates --dry-run

# Enable verbose logging
ckan activityinfo resources sync-auto-updates -v
```

## Resource extra fields

This extension adds the following resource extra fields to CKAN resources:
 - `activityinfo_form_id`: the ActivityInfo form ID
 - `activityinfo_database_id`: the ActivityInfo database ID
 - `activityinfo_status`: the download status (`pending`, `exporting`, `downloading`, `complete`, `error`)
 - `activityinfo_progress`: the download progress (0-100)
 - `activityinfo_error`: any error message if the download failed
 - `activityinfo_format`: the format of the downloaded data (e.g. `csv`, `xlsx`)
 - `activityinfo_form_label`: the label of the ActivityInfo form
 - `activityinfo_auto_update`: automatic update frequency (`never`, `daily`, `weekly`)
 - `activityinfo_auto_update_runs`: how many times automatic updates should run (1-20)
 - `activityinfo_last_updated`: ISO timestamp of the last automatic update
 - `activityinfo_auto_update_count`: how many automatic updates have been completed so far
 - `activityinfo_user`: the CKAN username who created the resource (used for automatic update authentication)

You'll need to add them to `ckan.extra_resource_fields` in your CKAN config:

```ini
ckan.extra_resource_fields = activityinfo_form_id activityinfo_database_id activityinfo_form_label activityinfo_status activityinfo_auto_update activityinfo_auto_update_runs activityinfo_last_updated activityinfo_auto_update_count activityinfo_user
```


## Config settings

These are the configuration settings that can be set in your `ckan.ini` file:

```
# Define where to save temporary files downloaded from ActivityInfo.
# If not set or "sys_tmp", the system temporary directory will be used.
ckanext.activityinfo.tmp_dir = /path/to/tmp/dir
```

### This extension as a feature flag

If you need to implement this extension in a way that it can be enabled/disabled with a feature flag, you can
define the following setting in your `ckan.ini` file:

```
# activityinfo_enabled defaults to true, so the extension is enabled by default. You can set it to false to temporarily disable the extension.
ckanext.activityinfo.activityinfo_enabled = false
```

Disabling the extension will only hide the option to create new ActivityInfo resources in the CKAN UI, but it won't affect existing ActivityInfo resources.  
Also, the UI access for users to add or edit their ActivityInfo API key in their user   profile will be hidden, but the API key will still be valid and can be used to download data from ActivityInfo for existing resources.  
Hiding elements from the UI is just a soft way to disable this extension. This is not a hard disable.  

## Get you ActivityInfo data

### ActivityInfo API Key

Log in to your ActivityInfo account and generate an API key:
Go to _Account settings_ -> _API Tokens_ -> _add_.  
Then define a label and the access level (Read or Read/Write) and click on "Generate".  

![Generate API key](/extras/imgs/activityinfo-token-generation.png)

You'll need to add this API key to your CKAN user profile.  

![CKAN User profile page](/extras/imgs/activity-info-user-page.png)

![Add you API key to CKAN](/extras/imgs/activity-info-define-api-key.png)


## CLI commands

This extension also provides some CLI commands to list your ActivityInfo databases and forms.  
You can run these commands with the `ckan` CLI tool. For example:  

```bash
# Get databases list
ckan activityinfo databases list -t <your_api_key> -v
# Get forms list for a specific database
ckan activityinfo forms list -t <your_api_key> -d <database_id> -v --include-sub-forms
```

## Adding a new resources

![Generate API key](/extras/imgs/activityinfo-new-res-01.png)

![Generate API key](/extras/imgs/activityinfo-new-res-02.png)

![Generate API key](/extras/imgs/activityinfo-new-res-03.png)

![Generate API key](/extras/imgs/activityinfo-new-res-04.png)

![Generate API key](/extras/imgs/activityinfo-new-res-05.png)

![Generate API key](/extras/imgs/activityinfo-new-res-06.png)

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

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

## Resource extra fields

This extension adds the following resource extra fields to CKAN resources:
 - `activityinfo_form_id`: the ActivityInfo form ID
 - `activityinfo_database_id`: the ActivityInfo database ID
 - `activityinfo_status`: the download status (e.g. 'pending', 'in_progress', 'complete', 'error')
 - `activityinfo_progress`: the download progress (0-100)
 - `activityinfo_error`: any error message if the download failed
 - `activityinfo_format`: the format of the downloaded data (e.g. 'csv', 'xls')
 - `activityinfo_form_label`: the label of the ActivityInfo form

You'll need to add them to `ckan.extra_resource_fields` to allow searching resources (action `resource_search`) by these fields.  

```bash
ckan.extra_resource_fields = activityinfo_form_id activityinfo_database_id activityinfo_form_label
```

## Config settings

None at present.

## Get you ActivityInfo data

### ActivityInfo API Key

Log in to your ActivityInfo account and generate an API key:
Go to _Account settings_ -> _API Tokens_ -> _add_.  
Then define a label and the access level (Read or Read/Write) and click on "Generate".  

![Generate API key](/extras/imgs/activityinfo-token-generation.png)

### Get your ActivityInfo databases


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

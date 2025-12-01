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

## Config settings

None at present

## Get you ActivityInfo data

### ActivityInfo API Key

Log in to your ActivityInfo account and generate an API key:
Go to _Account settings_ -> _API Tokens_ -> _add_.  
Then define a label and the access level (Read or Read/Write) and click on "Generate".  

![Generate API key](/extras/imgs/activityinfo-token-generation.png)

### Get your ActivityInfo databases


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

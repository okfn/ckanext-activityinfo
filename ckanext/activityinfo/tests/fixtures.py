import pytest
from ckanext.activityinfo.tests import factories


@pytest.fixture
def ai_user_with_api_key():
    """A CKAN user with an existing ActivityInfo API key."""
    return factories.ActivityInfoUser()


# Use 'with_plugins' fixture in ALL tests
@pytest.fixture(autouse=True)
def load_standard_plugins(with_plugins):
    pass

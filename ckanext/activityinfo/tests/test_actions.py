from unittest import mock
import pytest
from ckan.plugins import toolkit
from ckantoolkit.tests import factories as ckan_factories


@pytest.mark.usefixtures("clean_db")
class TestActInfoGetFormsAction:
    def test_get_forms_returns_sub_forms(self, ai_user_with_api_key):
        user = ai_user_with_api_key
        fake_forms = [
            {"id": "form01", "label": "Form 01", "type": "FORM"}
        ]
        fake_sub_forms = [
            {"id": "subform01", "label": "Sub Form 01", "type": "SUB_FORM"},
            {"id": "subform02", "label": "Sub Form 02", "type": "SUB_FORM"}
        ]
        fake_database = {
            "databaseId": "db01",
            "label": "Database 01"
        }
        fake_data = {
            "forms": fake_forms,
            "sub_forms": fake_sub_forms,
            "database": fake_database
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            return_value=fake_data,
        ):
            result = toolkit.get_action('act_info_get_forms')(
                context={'user': user['name']},
                data_dict={'database_id': 'db01'}
            )
            assert 'forms' in result
            assert 'sub_forms' in result
            assert 'database' in result
            assert len(result['forms']) == 1
            assert len(result['sub_forms']) == 2
            assert result['sub_forms'][0]['id'] == 'subform01'
            assert result['sub_forms'][1]['id'] == 'subform02'

    def test_get_forms_empty_sub_forms(self, ai_user_with_api_key):
        user = ai_user_with_api_key
        fake_forms = [
            {"id": "form01", "label": "Form 01", "type": "FORM"}
        ]
        fake_database = {
            "databaseId": "db01",
            "label": "Database 01"
        }
        fake_data = {
            "forms": fake_forms,
            "sub_forms": [],
            "database": fake_database
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            return_value=fake_data,
        ):
            result = toolkit.get_action('act_info_get_forms')(
                context={'user': user['name']},
                data_dict={'database_id': 'db01'}
            )
            assert 'sub_forms' in result
            assert len(result['sub_forms']) == 0

    def test_get_forms_missing_sub_forms_key(self, ai_user_with_api_key):
        """Test that action handles missing sub_forms key gracefully."""
        user = ai_user_with_api_key
        fake_forms = [
            {"id": "form01", "label": "Form 01", "type": "FORM"}
        ]
        fake_database = {
            "databaseId": "db01",
            "label": "Database 01"
        }
        # Simulate response without sub_forms key
        fake_data = {
            "forms": fake_forms,
            "database": fake_database
        }
        with mock.patch(
            "ckanext.activityinfo.data.base.ActivityInfoClient.get_forms",
            return_value=fake_data,
        ):
            result = toolkit.get_action('act_info_get_forms')(
                context={'user': user['name']},
                data_dict={'database_id': 'db01'}
            )
            assert 'sub_forms' in result
            assert result['sub_forms'] == []

    def test_get_forms_no_api_key_user(self):
        user = ckan_factories.User()
        with pytest.raises(toolkit.NotAuthorized):
            toolkit.get_action('act_info_get_forms')(
                context={'user': user['name']},
                data_dict={'database_id': 'db01'}
            )

    def test_get_forms_missing_database_id(self, ai_user_with_api_key):
        user = ai_user_with_api_key
        with pytest.raises(toolkit.ValidationError) as excinfo:
            toolkit.get_action('act_info_get_forms')(
                context={'user': user['name']},
                data_dict={}
            )
        assert 'database_id' in str(excinfo.value)

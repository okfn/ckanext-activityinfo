import requests


class ActivityInfoClient:
    """Base class for ActivityInfo API client."""

    def __init__(self, base_url="https://www.activityinfo.org", api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def get_user_auth_headers(self):
        """
        Utility function to create authentication headers for ActivityInfo API requests.
        """
        if not self.api_key:
            raise ValueError("API key is required for authentication headers.")
        auth_headers = {"Authorization": f"Bearer {self.api_key}"}
        return auth_headers

    def get(self, endpoint, params=None):
        """Make a GET request to the ActivityInfo API."""
        headers = self.get_user_auth_headers()
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_databases(self):
        """ Fetch the list of databases for the authenticated user.
        Returns:
            A list of databases.
        Reponse sample:
        [
          {
          'databaseId': 'cqvxxxxxx',
          'label': 'Some DB',
          'description': '',
          'ownerId': '2132xxxxx',
          'billingAccountId': 5682xxxxx,
          'suspended': False,
          'publishedTemplate': False,
          'languages': []
          }
        ]
        """
        return self.get("resources/databases")

    def get_database(self, database_id):
        """ Fetch the details of a specific database.
        Args:
            database_id (str): The ID of the database to fetch.
        Returns:
            A dictionary containing the details of the database.
        """
        return self.get(f"resources/databases/{database_id}")

    def get_forms(self, database_id):
        """ Fetch the list of forms for a specific database.
        Args:
            database_id (str): The ID of the database to fetch forms for.
        Returns:
            A list of forms.
        Reponse sample:
        [
          {
          'formId': 'cqvxxxxxx',
          'label': 'Some Form',
          'description': '',
          'ownerId': '2132xxxxx',
          'billingAccountId': 5682xxxxx,
          'suspended': False,
          'publishedTemplate': False,
          'languages': []
          }
        ]
        """
        return self.get(f"resources/databases/{database_id}/forms")

    def get_form(self, database_id, form_id):
        """ Fetch the details of a specific form.
        Args:
            database_id (str): The ID of the database to fetch forms for.
            form_id (str): The ID of the form to fetch.
        Returns:
            A dictionary containing the details of the form.
        """
        return self.get(f"resources/databases/{database_id}/forms/{form_id}")

    def get_form_fields(self, database_id, form_id):
        """ Fetch the list of fields for a specific form.
        Args:
            database_id (str): The ID of the database to fetch forms for.
            form_id (str): The ID of the form to fetch fields for.
        Returns:
            A list of fields.
        Reponse sample:
        [
          {
          'fieldId': 'cqvxxxxxx',
          'label': 'Some Field',
          'description': '',
          'ownerId': '2132xxxxx',
          'billingAccountId': 5682xxxxx,
          'suspended': False,
          'publishedTemplate': False,
          'languages': []
          }
        ]
        """
        return self.get(f"resources/databases/{database_id}/forms/{form_id}/fields")

    def get_form_field(self, database_id, form_id, field_id):
        """ Fetch the details of a specific field.
        Args:
            database_id (str): The ID of the database to fetch forms for.
            form_id (str): The ID of the form to fetch fields for.
            field_id (str): The ID of the field to fetch.
        Returns:
            A dictionary containing the details of the field.
        """
        return self.get(f"resources/databases/{database_id}/forms/{form_id}/fields/{field_id}")

    def get_form_field_values(self, database_id, form_id, field_id):
        """ Fetch the list of values for a specific field.
        Args:
            database_id (str): The ID of the database to fetch forms for.
            form_id (str): The ID of the form to fetch fields for.
            field_id (str): The ID of the field to fetch values for.
        Returns:
            A list of values.
        Reponse sample:
        [
          {
          'fieldId': 'cqvxxxxxx',
          'label': 'Some Field',
          'description': '',
          'ownerId': '2132xxxxx',
          'billingAccountId': 5682xxxxx,
          'suspended': False,
          'publishedTemplate': False,
          'languages': []
          }
        ]
        """
        return self.get(f"resources/databases/{database_id}/forms/{form_id}/fields/{field_id}/values")

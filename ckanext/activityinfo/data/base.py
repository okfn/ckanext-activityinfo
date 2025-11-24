import logging
from pathlib import Path
import requests


log = logging.getLogger(__name__)


class ActivityInfoClient:
    """Base class for ActivityInfo API client."""

    def __init__(self, base_url="https://www.activityinfo.org", api_key=None, debug=True):
        self.base_url = base_url
        self.api_key = api_key
        self.debug = debug
        self.responses_debug_dir = None
        if self.debug:
            here = Path(__file__).parent
            self.responses_debug_dir = here / "responses_debug_dir"
            self.responses_debug_dir.mkdir(exist_ok=True)
        log.debug(f"ActivityInfoClient initialized with base_url: {self.base_url}, debug: {self.debug}")

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
        log.info(f"ActivityInfoClient Making GET request to {endpoint}")
        headers = self.get_user_auth_headers()
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        log.info(f"ActivityInfoClient GET request to {endpoint} completed")
        if self.debug:
            # create all folders in path
            Path(self.responses_debug_dir / endpoint).mkdir(parents=True, exist_ok=True)
            with open(self.responses_debug_dir / endpoint / "response.json", "w") as f:
                f.write(response.body)
        return response.json()

    def get_databases(self):
        """ Fetch the list of databases for the authenticated user.
        Docs: https://www.activityinfo.org/support/docs/api/reference/getDatabases.html
        Returns:
            A list of databases.
        Reponse sample: see ckanext/activityinfo/data/samples/databases.json
        """
        return self.get("resources/databases")

    def get_database(self, database_id):
        """ Fetch the details of a specific database.
        Docs: https://www.activityinfo.org/support/docs/api/reference/getDatabaseTree.html
        Args:
            database_id (str): The ID of the database to fetch.
        Returns:
            A dictionary containing the details of the database.
            This include resources by types: DATABASE, FOLDER, REPORT, FORM and SUB_FORM
        Response sample: see ckanext/activityinfo/data/samples/database.json
        """
        return self.get(f"resources/databases/{database_id}")

    def get_forms(self, database_id, include_db_data=True):
        """ Fetch the list of forms for a specific database.
        There is not direct API endpoint
        We get the database nad the resources -> list -> filter type=FORM
        """
        database = self.get_database(database_id)
        forms = [resource for resource in database["resources"] if resource["type"] == "FORM"]
        data = {"forms": forms}
        if include_db_data:
            data["database"] = database
        return data

    def get_form(self, database_id, form_id):
        """ Fetch the details of a specific form.
        Args:
            database_id (str): The ID of the database to fetch forms for.
            form_id (str): The ID of the form to fetch.
        Returns:
            A dictionary containing the details of the form.
        """
        return self.get(f"resources/databases/{database_id}/forms/{form_id}")

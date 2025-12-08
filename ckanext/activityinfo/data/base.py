import logging
from pathlib import Path
import requests


log = logging.getLogger(__name__)


class ActivityInfoClient:
    """Base class for ActivityInfo API client."""

    def __init__(self, base_url="https://www.activityinfo.org", api_key=None, debug=False):
        self.base_url = base_url
        self.api_key = api_key
        self.debug = debug
        self.responses_debug_dir = None
        if self.debug:
            here = Path(__file__).parent
            self.responses_debug_dir = here / "responses_debug_dir"

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
            try:
                Path(self.responses_debug_dir / endpoint).mkdir(parents=True, exist_ok=True)
                with open(self.responses_debug_dir / endpoint / "response.json", "w") as f:
                    f.write(response.text)
            except Exception as e:
                log.debug(f"Failed to write debug response for {endpoint}: {e}")
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

    def get_forms(self, database_id, include_db_data=True, include_sub_forms=True):
        """ Fetch the list of forms for a specific database.
        There is not direct API endpoint
        We get the database nad the resources -> list -> filter type=FORM
        """
        database = self.get_database(database_id)
        forms = [
            resource for resource in database["resources"]
            if resource["type"] == "FORM"
        ]
        data = {"forms": forms, "sub_forms": [], "database": {}}
        if include_sub_forms:
            sub_forms = [
                resource for resource in database["resources"]
                if resource["type"] == "SUB_FORM"
            ]
            data["sub_forms"] = sub_forms

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
        See a data sample here ckanext/activityinfo/data/samples/form-tree-translated.json

        We here get the data schema, the actual data must be acceced in chunks from
        POST /resources/query/chunks
        """
        return self.get(f"resources/form/{form_id}/tree/translated")

    def get_form_columns(self, form_id):
        """
        Get the columns for a form to use in export requests.
        Fetches the form schema and builds the columns array from the elements.

        Args:
            form_id (str): The ID of the form.
        Returns:
            A list of column definitions for the export API.
        """
        form_tree = self.get(f"resources/form/{form_id}/tree/translated")
        forms_data = form_tree.get('forms', {})
        form_data = forms_data.get(form_id, {})
        schema = form_data.get('schema', {})
        elements = schema.get('elements', [])

        columns = []
        for element in elements:
            # Skip sub-forms and other non-field elements
            element_type = element.get('type', '')
            if element_type in ('SUB_FORM', 'section'):
                continue

            column = {
                'id': element.get('id'),
                'label': element.get('label', element.get('id')),
                'formula': element.get('id'),
                'translate': False
            }
            columns.append(column)

        return columns

    def get_url_to_database(self, database_id):
        """ Utility function to get the URL to access a database in ActivityInfo web app.
        Args:
            database_id (str): The ID of the database.
        Returns:
            A string containing the URL to access the database.
        """
        return f"{self.base_url}/app#database/{database_id}/"

    def get_url_to_form(self, form_id):
        """ Utility function to get the URL to access a form in ActivityInfo web app.
        Args:
            database_id (str): The ID of the database.
            form_id (str): The ID of the form.
        Returns:
            A string containing the URL to access the form.
        """
        return f"{self.base_url}/app#form/{form_id}/table"

    def start_job_download_form_data(self, form_id, format="CSV", columns=None):
        """
        Use the Jobs API to export form data as CSV.
        Read: https://www.activityinfo.org/support/docs/api/reference/exportFormJob.html
        See response sample ckanext/activityinfo/data/samples/job-started.json

        Args:
            form_id (str): The ID of the form to export.
            format (str): Export format (CSV, XLSX, etc.)
            columns (list): Column definitions. If None, fetches all columns from form schema.
        """
        available_formats = ["CSV", "XLSX", "TEXT"]
        if format not in available_formats:
            raise ValueError(f"Invalid format. Supported formats are {available_formats}")

        # If no columns provided, fetch them from the form schema
        if columns is None:
            columns = self.get_form_columns(form_id)
            log.info(f"Fetched {len(columns)} columns for form {form_id}")

        endpoint = "resources/jobs"
        payload = {
            "type": "exportForm",
            "descriptor": {
                "tableModels": [
                    {
                        "formId": form_id,
                        "columns": columns,
                        "ordering": [],
                        "filter": None,
                    }
                ],
                "format": format,
                "utcOffset": 0,
            }
        }
        headers = self.get_user_auth_headers()
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        job_info = response.json()
        return job_info

    def get_job_status(self, job_id):
        """
        Get the status of a job.
        Read:
         - Getting job status https://www.activityinfo.org/support/docs/api/reference/exportFormJob.html#getting-the-job-status
           GET https://www.activityinfo.org/resources/jobs/{jobId}
        """
        endpoint = f"resources/jobs/{job_id}"
        return self.get(endpoint)

    def get_job_file(self, job_id):
        """
        Download the file or return the percentage completed if not ready.
        See JSON sample from ckanext/activityinfo/data/samples/job-complete.json
        Return a tuple: (bool done, content or progress %)
        """
        job_status = self.get_job_status(job_id)
        if job_status["state"] != "completed":
            return False, job_status.get("percentComplete", 0)

        export_info = job_status["result"]
        endpoint = export_info["downloadUrl"].lstrip("/")
        url = f"{self.base_url}/{endpoint}"
        return True, url

    def download_finished_export(self, download_url):
        """
        Download the finished export file from ActivityInfo.
        Args:
            download_url (str): The URL to download the file from.
        Returns:
            The content of the downloaded file.
        """
        headers = self.get_user_auth_headers()
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()
        return response.content

    def download_file(self, url: str) -> bytes:
        """Download a file from ActivityInfo.

        Args:
            url: The download URL

        Returns:
            The file contents as bytes
        """
        headers = {'Authorization': f'Bearer {self.api_key}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content

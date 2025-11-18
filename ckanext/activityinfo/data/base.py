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
        """Fetch the list of databases for the authenticated user."""
        return self.get("resources/databases")
"""Azure DevOps REST API Client with retry mechanism."""

import base64
import logging
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AzureDevOpsConfig

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    """Client for interacting with Azure DevOps REST API."""

    def __init__(self, config: AzureDevOpsConfig):
        self.config = config
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create an HTTP session with retry strategy."""
        session = requests.Session()

        # Set authentication header
        credentials = base64.b64encode(f":{self.config.pat}".encode()).decode()
        session.headers.update({
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Make an HTTP request with error handling."""
        kwargs.setdefault("timeout", self.config.timeout)
        try:
            logger.debug(f"{method.upper()} {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def execute_wiql(self, query: str) -> list[dict[str, Any]]:
        """Execute a WIQL query and return full work item details."""
        logger.info("Executing WIQL query")
        result = self._request("POST", self.config.wiql_url, json={"query": query})

        work_item_ids = [item["id"] for item in result.get("workItems", [])]
        if not work_item_ids:
            logger.info("No work items found")
            return []

        logger.info(f"Found {len(work_item_ids)} work items")
        return self._fetch_work_items_batch(work_item_ids)

    def _fetch_work_items_batch(
        self, ids: list[int], batch_size: int = 200
    ) -> list[dict[str, Any]]:
        """Fetch work items in batches."""
        all_items = []
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
            ids_str = ",".join(str(id) for id in batch)
            url = (
                f"{self.config.base_url}/wit/workitems?ids={ids_str}"
                f"&$expand=all&api-version={self.config.api_version}"
            )
            result = self._request("GET", url)
            all_items.extend(result.get("value", []))
            if i + batch_size < len(ids):
                time.sleep(0.5)  # Rate limiting between batches
        return all_items

    def get_all_bugs(self) -> list[dict[str, Any]]:
        """Fetch all bug work items."""
        query = """
        SELECT [System.Id], [System.Title], [System.State],
               [Microsoft.VSTS.Common.Priority], [System.AssignedTo],
               [System.CreatedDate], [System.ChangedDate],
               [Microsoft.VSTS.Common.Severity], [System.IterationPath],
               [System.AreaPath], [System.Tags]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Bug'
        ORDER BY [Microsoft.VSTS.Common.Priority] ASC, [System.CreatedDate] DESC
        """
        return self.execute_wiql(query)

    def get_active_bugs(self) -> list[dict[str, Any]]:
        """Fetch all active bugs."""
        query = """
        SELECT [System.Id], [System.Title], [System.State],
               [Microsoft.VSTS.Common.Priority], [System.AssignedTo],
               [System.CreatedDate], [Microsoft.VSTS.Common.Severity],
               [System.IterationPath], [System.AreaPath], [System.Tags]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Bug'
              AND [System.State] = 'Active'
        ORDER BY [Microsoft.VSTS.Common.Priority] ASC, [System.CreatedDate] DESC
        """
        return self.execute_wiql(query)

    def get_bugs_assigned_to_me(self) -> list[dict[str, Any]]:
        """Fetch bugs assigned to the current user."""
        query = """
        SELECT [System.Id], [System.Title], [System.State],
               [Microsoft.VSTS.Common.Priority], [System.AssignedTo],
               [System.CreatedDate], [Microsoft.VSTS.Common.Severity],
               [System.IterationPath], [System.Tags]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Bug'
              AND [System.AssignedTo] = @Me
        ORDER BY [Microsoft.VSTS.Common.Priority] ASC, [System.State] ASC
        """
        return self.execute_wiql(query)

    def get_p1_p2_bugs(self) -> list[dict[str, Any]]:
        """Fetch P1 and P2 priority bugs."""
        query = """
        SELECT [System.Id], [System.Title], [System.State],
               [Microsoft.VSTS.Common.Priority], [System.AssignedTo],
               [System.CreatedDate], [Microsoft.VSTS.Common.Severity],
               [System.IterationPath], [System.AreaPath], [System.Tags]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Bug'
              AND [Microsoft.VSTS.Common.Priority] <= 2
        ORDER BY [Microsoft.VSTS.Common.Priority] ASC, [System.State] ASC
        """
        return self.execute_wiql(query)

    def get_sprint_bugs(self, iteration_path: Optional[str] = None) -> list[dict[str, Any]]:
        """Fetch bugs for a specific sprint or current iteration."""
        if iteration_path:
            query = f"""
            SELECT [System.Id], [System.Title], [System.State],
                   [Microsoft.VSTS.Common.Priority], [System.AssignedTo],
                   [System.CreatedDate], [Microsoft.VSTS.Common.Severity],
                   [System.IterationPath], [System.Tags]
            FROM WorkItems
            WHERE [System.WorkItemType] = 'Bug'
                  AND [System.IterationPath] = '{iteration_path}'
            ORDER BY [Microsoft.VSTS.Common.Priority] ASC
            """
        else:
            query = """
            SELECT [System.Id], [System.Title], [System.State],
                   [Microsoft.VSTS.Common.Priority], [System.AssignedTo],
                   [System.CreatedDate], [Microsoft.VSTS.Common.Severity],
                   [System.IterationPath], [System.Tags]
            FROM WorkItems
            WHERE [System.WorkItemType] = 'Bug'
                  AND [System.IterationPath] = @CurrentIteration
            ORDER BY [Microsoft.VSTS.Common.Priority] ASC
            """
        return self.execute_wiql(query)

    def get_saved_queries(self, folder: str = "Shared Queries") -> list[dict[str, Any]]:
        """Fetch saved queries from Azure DevOps."""
        url = self.config.get_queries_url(folder)
        try:
            result = self._request("GET", url)
            return self._flatten_queries(result)
        except Exception as e:
            logger.error(f"Failed to fetch saved queries: {e}")
            return []

    def _flatten_queries(self, query_node: dict, queries: list = None) -> list[dict]:
        """Recursively flatten query tree structure."""
        if queries is None:
            queries = []

        if query_node.get("isFolder"):
            for child in query_node.get("children", []):
                self._flatten_queries(child, queries)
        else:
            queries.append({
                "id": query_node.get("id"),
                "name": query_node.get("name"),
                "path": query_node.get("path"),
                "wiql": query_node.get("wiql"),
            })
        return queries

    def execute_saved_query(self, query_id: str) -> list[dict[str, Any]]:
        """Execute a saved query by its ID."""
        url = (
            f"{self.config.base_url}/wit/wiql/{query_id}"
            f"?api-version={self.config.api_version}"
        )
        result = self._request("GET", url)
        work_item_ids = [item["id"] for item in result.get("workItems", [])]
        if not work_item_ids:
            return []
        return self._fetch_work_items_batch(work_item_ids)

    def get_bug_statistics(self) -> dict[str, Any]:
        """Get comprehensive bug statistics."""
        all_bugs = self.get_all_bugs()
        stats = {
            "total": len(all_bugs),
            "by_state": {},
            "by_priority": {},
            "by_severity": {},
            "by_sprint": {},
            "by_assignee": {},
        }

        for bug in all_bugs:
            fields = bug.get("fields", {})

            state = fields.get("System.State", "Unknown")
            stats["by_state"][state] = stats["by_state"].get(state, 0) + 1

            priority = fields.get("Microsoft.VSTS.Common.Priority", 0)
            priority_label = f"P{priority}" if priority else "Unset"
            stats["by_priority"][priority_label] = stats["by_priority"].get(priority_label, 0) + 1

            severity = fields.get("Microsoft.VSTS.Common.Severity", "Unset")
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

            sprint = fields.get("System.IterationPath", "Unassigned")
            stats["by_sprint"][sprint] = stats["by_sprint"].get(sprint, 0) + 1

            assignee = fields.get("System.AssignedTo", {})
            assignee_name = assignee.get("displayName", "Unassigned") if isinstance(assignee, dict) else "Unassigned"
            stats["by_assignee"][assignee_name] = stats["by_assignee"].get(assignee_name, 0) + 1

        return stats

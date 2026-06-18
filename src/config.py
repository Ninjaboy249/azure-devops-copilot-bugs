"""Configuration module for Azure DevOps Bug Tracker."""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AzureDevOpsConfig:
    """Azure DevOps connection configuration."""

    org_url: str = field(default_factory=lambda: os.getenv("AZURE_DEVOPS_ORG_URL", ""))
    pat: str = field(default_factory=lambda: os.getenv("AZURE_DEVOPS_PAT", ""))
    project: str = field(default_factory=lambda: os.getenv("AZURE_DEVOPS_PROJECT", ""))
    user_email: str = field(default_factory=lambda: os.getenv("AZURE_DEVOPS_USER_EMAIL", ""))
    team: str = field(default_factory=lambda: os.getenv("AZURE_DEVOPS_TEAM", ""))
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "./output"))
    )
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    api_version: str = "7.1"
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._configure_logging()

    def _configure_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def validate(self) -> bool:
        """Validate required configuration fields."""
        errors = []
        if not self.org_url:
            errors.append("AZURE_DEVOPS_ORG_URL is required")
        if not self.pat:
            errors.append("AZURE_DEVOPS_PAT is required")
        if not self.project:
            errors.append("AZURE_DEVOPS_PROJECT is required")

        if errors:
            for error in errors:
                logger.error(error)
            return False

        # Normalize org URL
        self.org_url = self.org_url.rstrip("/")
        logger.info("Configuration validated successfully")
        return True

    @property
    def base_url(self) -> str:
        """Get the base API URL."""
        return f"{self.org_url}/{self.project}/_apis"

    @property
    def wiql_url(self) -> str:
        """Get the WIQL endpoint URL."""
        return f"{self.base_url}/wit/wiql?api-version={self.api_version}"

    @property
    def work_items_url(self) -> str:
        """Get the work items endpoint URL."""
        return f"{self.base_url}/wit/workitems?api-version={self.api_version}"

    def get_work_item_url(self, item_id: int) -> str:
        """Get URL for a specific work item."""
        return f"{self.base_url}/wit/workitems/{item_id}?api-version={self.api_version}&$expand=all"

    def get_queries_url(self, folder_path: str = "") -> str:
        """Get URL for saved queries."""
        base = f"{self.base_url}/wit/queries"
        if folder_path:
            base += f"/{folder_path}"
        return f"{base}?api-version={self.api_version}&$depth=2"

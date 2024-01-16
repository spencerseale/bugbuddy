import io
import json
import os
import uuid
from logging import Logger, getLogger
from typing import Mapping, Optional, Union

import requests
from attrs import define, field
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass
class Issue:
    """Normalized Remote Issue."""

    id: int
    """Issue ID."""
    title: str
    """Issue title."""
    state: str
    """Issue state."""
    project_id: int
    """Remote project ID."""
    author: tuple[str, str, str]
    """Author name, username, and state."""
    created_at: str
    """Time issue created."""
    updated_at: str
    """Time issue updated."""
    description: str
    """Issue description."""
    labels: list[str] = field(factory=list)
    """Issue labels."""

    def _clean(self) -> str:
        """Clean attributes so they're ready for df transformation."""

        attribs = self.__dict__.copy()
        attribs = {k: v if isinstance(v, (str, int)) else "_".join(v) for k, v in attribs.items()}
        return attribs

    @staticmethod
    def _jdump(contents: list[dict[str, any]], handler: io.TextIOWrapper) -> str:
        """Dump to JSON."""

        json.dump(
            contents, handler, indent=4, sort_keys=False, default=str, separators=(",", ": ")
        )

    def cache(self, cache: str = ".bug_buddy.cache") -> str:
        """Append to a local cache file."""

        cleaned = self._clean()

        # try to open up cache if it exists in $HOME
        cache = os.path.join(os.environ["HOME"], cache)
        try:
            with open(cache, "r+") as rf:
                existing = json.load(rf)

            # add to existing cache
            existing.append(cleaned)

            with open(cache, "w") as of:
                Issue._jdump(existing, of)

        except FileNotFoundError:
            with open(cache, "w") as f:
                Issue._jdump([cleaned], f)


@define
class GitlabIssuesApi:
    """GitLab Project-pinned Issues API."""

    url: str = "https://gitlab.com/api/v4"
    """GitLab API URL."""
    endpoint: str = field(default="projects/{project_id}/issues")
    """Project-pinned GitLab issues endpoint."""

    @endpoint.validator
    def _validate_endpoint(self, attribute: str, value: str) -> str:
        """Validate endpoint doesn't start with a forward slash."""
        if value.startswith("/"):
            raise ValueError("Endpoint cannot start with a forward slash.")

    token: str = field(converter=str)
    """Personal, project, or group token."""

    @token.default
    def _token_default(self) -> str:
        return os.environ["GITLAB_TOKEN"]

    logger: Logger = field()
    """Logging instance."""

    @logger.default
    def _logger_default(self) -> Logger:
        return getLogger(__name__)

    @staticmethod
    def _normalize_itype(response_map: Mapping[str, any]) -> Issue:
        """Normalize issue type.

        Args:
            response_map: responsing mapping from GitLab API.

        Returns:
            Normalized Issue type.
        """

        return Issue(
            id=response_map["id"],
            title=response_map["title"],
            state=response_map["state"],
            project_id=response_map["project_id"],
            author=(
                response_map["author"]["name"],
                response_map["author"]["username"],
                response_map["author"]["state"],
            ),
            created_at=response_map["created_at"],
            updated_at=response_map["updated_at"],
            description=response_map["description"],
            labels=response_map["labels"],
        )

    def get_issues(
        self,
        project_id: int,
        id: Optional[int] = None,
        normalize: bool = True,
    ) -> Union[Issue, list[dict[str, any]]]:
        """Project-pinned issues.

        Args:
            project_id: project ID.
            id: issue ID.
            normalize: whether to normalize issue type.

        Returns:
            Project-pinned issues, normalzied or raw.
        """

        self.logger.debug("Getting issues for project %s", project_id)

        resp = requests.get(
            os.path.join(self.url, self.endpoint.format(project_id=project_id)),
            params={
                "private_token": self.token,
                "iids": id,
            },
        )

        resp.raise_for_status()
        self.logger.debug("Response code: %s", resp.status_code)
        issue = resp.json()

        if normalize:
            return [self._normalize_itype(issue) for issue in resp.json()]
        else:
            return issue

    def create_issue(
        self,
        project_id: int,
        description: str,
        labels: Optional[list[str]] = None,
        title: Optional[str] = None,
    ) -> Issue:
        """Create an issue.

        Args:
            project_id: project ID.
            description: issue description.
            labels: issue labels.
            title: issue title.

        Returns:
            Created issue, normalized.
        """

        title = title or "BugBuddy-" + str(uuid.uuid4())
        # always include BugBuddy label
        if labels is None:
            labels = ["BugBuddy"]
        elif "BugBuddy" not in labels:
            labels.append("BugBuddy")

        resp = requests.post(
            os.path.join(self.url, self.endpoint.format(project_id=project_id)),
            params={
                "private_token": self.token,
            },
            json={
                "title": title,
                "description": description,
                "labels": labels,
            },
        )

        resp.raise_for_status()
        self.logger.debug("Response code: %s", resp.status_code)
        issue = resp.json()
        return self._normalize_itype(issue)
